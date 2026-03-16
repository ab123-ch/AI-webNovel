"""记忆压缩服务

实现多层记忆压缩和追溯功能
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Optional

from ..dal import CompactionIndex, CompactionIndexDAO, TaskMemoryLinkDAO
from ..opencode import OpenCodeTasks

logger = logging.getLogger(__name__)


class MemoryCompaction:
    """
    记忆压缩服务

    职责：
    - 检测是否需要压缩
    - 执行多层压缩
    - 管理压缩索引
    - 提供追溯功能

    Example:
        >>> compaction = MemoryCompaction(tasks, db)
        >>> if await compaction.check_compaction_needed(session_id):
        ...     index = await compaction.compact_layer1(session_id)
    """

    # 压缩阈值配置
    LAYER1_THRESHOLD = 10  # 10 条消息触发 Layer 1 压缩
    LAYER2_THRESHOLD = 5   # 5 个 Layer 1 索引触发 Layer 2 压缩
    LAYER3_THRESHOLD = 3   # 3 个 Layer 2 索引触发 Layer 3 压缩

    def __init__(
        self,
        opencode_tasks: OpenCodeTasks,
        compaction_dao: CompactionIndexDAO,
        link_dao: TaskMemoryLinkDAO
    ):
        """
        初始化记忆压缩服务

        Args:
            opencode_tasks: OpenCode 任务封装器
            compaction_dao: 压缩索引 DAO
            link_dao: 任务-记忆关联 DAO
        """
        self.tasks = opencode_tasks
        self.compaction_dao = compaction_dao
        self.link_dao = link_dao

    def check_compaction_needed(
        self,
        session_id: str,
        current_tokens: int,
        warning_tokens: int = 60000
    ) -> bool:
        """
        检查是否需要压缩

        Args:
            session_id: 会话 ID
            current_tokens: 当前 token 数
            warning_tokens: 警告阈值

        Returns:
            是否需要压缩
        """
        return current_tokens > warning_tokens

    async def compact_layer1(
        self,
        session_id: str,
        messages: list[dict]
    ) -> CompactionIndex:
        """
        Layer 1 压缩 - 消息级别

        将最近的 N 条消息压缩为摘要和关键信息

        Args:
            session_id: 会话 ID
            messages: 待压缩的消息列表

        Returns:
            压缩索引

        Example:
            >>> index = await compaction.compact_layer1(
            ...     "session-123",
            ...     [{"role": "user", "content": "..."}]
            ... )
        """
        logger.info(
            f"[MemoryCompaction] 开始 Layer 1 压缩: "
            f"session={session_id}, messages={len(messages)}"
        )

        # 调用 OpenCode 进行压缩
        result = await self.tasks.compact_memories(messages, layer=1)

        # 创建压缩索引
        now = int(time.time())
        index = CompactionIndex(
            id=str(uuid.uuid4())[:8],
            session_id=session_id,
            layer=1,
            source_memory_ids=[m.get("id", str(i)) for i, m in enumerate(messages)],
            source_compaction_ids=None,
            summary=result.get("summary", ""),
            key_topics=result.get("key_topics", []),
            key_decisions=result.get("key_decisions", []),
            key_entities=result.get("key_entities", []),
            key_conclusions=result.get("key_conclusions", []),
            task_type=result.get("task_type"),
            task_description=result.get("task_description"),
            original_token_count=self._estimate_tokens(messages),
            compressed_token_count=self._estimate_text_tokens(result.get("summary", "")),
            compression_ratio=0.0,
            created_at=now
        )

        # 计算压缩比
        if index.original_token_count > 0:
            index.compression_ratio = (
                index.original_token_count - index.compressed_token_count
            ) / index.original_token_count

        # 保存到数据库
        self.compaction_dao.create(index)

        logger.info(
            f"[MemoryCompaction] Layer 1 压缩完成: "
            f"ratio={index.compression_ratio:.2%}, "
            f"topics={len(index.key_topics)}"
        )

        return index

    async def compact_layer2(
        self,
        session_id: str,
        layer1_indexes: list[CompactionIndex]
    ) -> CompactionIndex:
        """
        Layer 2 压缩 - 压缩索引级别

        将多个 Layer 1 索引压缩为更高层摘要

        Args:
            session_id: 会话 ID
            layer1_indexes: Layer 1 索引列表

        Returns:
            Layer 2 压缩索引
        """
        logger.info(
            f"[MemoryCompaction] 开始 Layer 2 压缩: "
            f"session={session_id}, sources={len(layer1_indexes)}"
        )

        # 构建输入消息（从索引构建）
        messages = []
        for idx in layer1_indexes:
            messages.append({
                "role": "system",
                "content": f"[压缩摘要] {idx.summary}"
            })
            messages.append({
                "role": "system",
                "content": f"[关键主题] {', '.join(idx.key_topics)}"
            })

        # 调用压缩
        result = await self.tasks.compact_memories(messages, layer=2)

        # 创建索引
        now = int(time.time())
        index = CompactionIndex(
            id=str(uuid.uuid4())[:8],
            session_id=session_id,
            layer=2,
            source_memory_ids=[],
            source_compaction_ids=[idx.id for idx in layer1_indexes],
            summary=result.get("summary", ""),
            key_topics=result.get("key_topics", []),
            key_decisions=result.get("key_decisions", []),
            key_entities=result.get("key_entities", []),
            key_conclusions=result.get("key_conclusions", []),
            task_type=result.get("task_type"),
            task_description=result.get("task_description"),
            original_token_count=sum(idx.original_token_count for idx in layer1_indexes),
            compressed_token_count=self._estimate_text_tokens(result.get("summary", "")),
            compression_ratio=0.0,
            created_at=now
        )

        if index.original_token_count > 0:
            index.compression_ratio = (
                index.original_token_count - index.compressed_token_count
            ) / index.original_token_count

        self.compaction_dao.create(index)

        logger.info(
            f"[MemoryCompaction] Layer 2 压缩完成: "
            f"ratio={index.compression_ratio:.2%}"
        )

        return index

    async def compact_layer3(
        self,
        session_id: str,
        layer2_indexes: list[CompactionIndex]
    ) -> CompactionIndex:
        """
        Layer 3 压缩 - 会话级别

        将多个 Layer 2 索引压缩为会话级摘要

        Args:
            session_id: 会话 ID
            layer2_indexes: Layer 2 索引列表

        Returns:
            Layer 3 压缩索引
        """
        logger.info(
            f"[MemoryCompaction] 开始 Layer 3 压缩: "
            f"session={session_id}, sources={len(layer2_indexes)}"
        )

        # 构建输入
        messages = []
        for idx in layer2_indexes:
            messages.append({
                "role": "system",
                "content": f"[会话段摘要] {idx.summary}"
            })

        result = await self.tasks.compact_memories(messages, layer=3)

        now = int(time.time())
        index = CompactionIndex(
            id=str(uuid.uuid4())[:8],
            session_id=session_id,
            layer=3,
            source_memory_ids=[],
            source_compaction_ids=[idx.id for idx in layer2_indexes],
            summary=result.get("summary", ""),
            key_topics=result.get("key_topics", []),
            key_decisions=result.get("key_decisions", []),
            key_entities=result.get("key_entities", []),
            key_conclusions=result.get("key_conclusions", []),
            task_type=result.get("task_type"),
            task_description=result.get("task_description"),
            original_token_count=sum(idx.original_token_count for idx in layer2_indexes),
            compressed_token_count=self._estimate_text_tokens(result.get("summary", "")),
            compression_ratio=0.0,
            created_at=now
        )

        if index.original_token_count > 0:
            index.compression_ratio = (
                index.original_token_count - index.compressed_token_count
            ) / index.original_token_count

        self.compaction_dao.create(index)

        logger.info(
            f"[MemoryCompaction] Layer 3 压缩完成: "
            f"ratio={index.compression_ratio:.2%}"
        )

        return index

    def get_trace_path(
        self,
        compaction_id: str
    ) -> list[str]:
        """
        获取追溯路径

        从压缩索引递归追溯原始消息

        Args:
            compaction_id: 压缩索引 ID

        Returns:
            路径列表 [compaction_id -> ... -> memory_ids]

        Example:
            >>> path = compaction.get_trace_path("c1")
            >>> print(path)
            ['c1', 'c1-1', 'c1-2', 'm1', 'm2', 'm3']
        """
        path: list[str] = [compaction_id]
        self._trace_recursive(compaction_id, path)
        return path

    def _trace_recursive(
        self,
        compaction_id: str,
        path: list[str]
    ) -> None:
        """递归追溯"""
        sources = self.compaction_dao.get_source_ids(compaction_id)

        # 添加压缩索引源
        for cid in sources.get("compaction_ids", []):
            path.append(cid)
            self._trace_recursive(cid, path)

        # 添加消息源（不再追溯）
        for mid in sources.get("memory_ids", []):
            path.append(mid)

    def _estimate_tokens(
        self,
        messages: list[dict]
    ) -> int:
        """估算消息 token 数"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            # 简单估算：中文约 1.5 字符/token，英文约 4 字符/token
            total += len(content) // 2
        return total

    def _estimate_text_tokens(
        self,
        text: str
    ) -> int:
        """估算文本 token 数"""
        return len(text) // 2
