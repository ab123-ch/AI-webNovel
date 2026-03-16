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
        """
        估算消息 token 数

        优先使用 tiktoken 进行精确计算，
        如果不可用则降级为智能估算

        Args:
            messages: 消息列表

        Returns:
            估算的 token 数
        """
        import time
        start_time = time.time()

        logger.debug(f"[MemoryCompaction] 开始估算 token 数量，消息数: {len(messages)}")

        # 尝试使用 tiktoken
        try:
            import tiktoken
            logger.debug("[MemoryCompaction] 使用 tiktoken 进行精确计算")
            enc = tiktoken.get_encoding("cl100k_base")  # GPT-4 编码
            total = 0
            for msg in messages:
                content = msg.get("content", "")
                total += len(enc.encode(content))

            elapsed = time.time() - start_time
            logger.info(
                f"[MemoryCompaction][tiktoken] Token 估算完成 "
                f"| 消息数: {len(messages)} "
                f"| 总 token: {total} "
                f"| 耗时: {elapsed:.3f}s"
            )
            return total

        except ImportError as e:
            # 降级为智能估算
            elapsed = time.time() - start_time
            logger.warning(
                f"[MemoryCompaction][降级] tiktoken 不可用 "
                f"| 错误类型: ImportError "
                f"| 错误信息: {e} "
                f"| 降级方案: _smart_estimate_messages() "
                f"| 提示: pip install tiktoken 可获得精确计算 "
                f"| 耗时: {elapsed:.3f}s"
            )
            return self._smart_estimate_messages(messages)

    def _smart_estimate_messages(
        self,
        messages: list[dict]
    ) -> int:
        """
        智能 token 估算（降级方案）

        中文字符约 1.5 token，英文约 0.25 token
        混合内容按比例计算

        Args:
            messages: 消息列表

        Returns:
            估算的 token 数
        """
        import time
        start_time = time.time()

        logger.debug("[MemoryCompaction][降级估算] 使用智能估算算法")

        total = 0
        total_chinese = 0
        total_other = 0

        for msg in messages:
            content = msg.get("content", "")
            # 统计中文字符数量
            chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            other_chars = len(content) - chinese_chars
            total_chinese += chinese_chars
            total_other += other_chars
            # 中文字符约 1.5 token，英文约 0.25 token
            total += int(chinese_chars * 1.5 + other_chars * 0.25)

        elapsed = time.time() - start_time
        logger.info(
            f"[MemoryCompaction][降级估算] Token 估算完成 "
            f"| 消息数: {len(messages)} "
            f"| 中文字符: {total_chinese} "
            f"| 其他字符: {total_other} "
            f"| 估算 token: {total} "
            f"| 系数: 中文1.5 + 英文0.25 "
            f"| 耗时: {elapsed:.3f}s"
        )
        return total

    def _estimate_text_tokens(
        self,
        text: str
    ) -> int:
        """
        估算文本 token 数

        优先使用 tiktoken 进行精确计算

        Args:
            text: 文本内容

        Returns:
            估算的 token 数
        """
        import time
        start_time = time.time()

        logger.debug(f"[MemoryCompaction] 开始估算文本 token，长度: {len(text)}")

        try:
            import tiktoken
            logger.debug("[MemoryCompaction] 使用 tiktoken 进行精确计算")
            enc = tiktoken.get_encoding("cl100k_base")
            result = len(enc.encode(text))

            elapsed = time.time() - start_time
            logger.info(
                f"[MemoryCompaction][tiktoken] 文本 Token 估算完成 "
                f"| 文本长度: {len(text)} "
                f"| token 数: {result} "
                f"| 耗时: {elapsed:.3f}s"
            )
            return result

        except ImportError as e:
            # 降级为智能估算
            elapsed = time.time() - start_time
            logger.warning(
                f"[MemoryCompaction][降级] tiktoken 不可用 "
                f"| 错误类型: ImportError "
                f"| 降级方案: _smart_estimate_text() "
                f"| 耗时: {elapsed:.3f}s"
            )
            return self._smart_estimate_text(text)

    def _smart_estimate_text(
        self,
        text: str
    ) -> int:
        """
        智能文本 token 估算（降级方案）

        Args:
            text: 文本内容

        Returns:
            估算的 token 数
        """
        import time
        start_time = time.time()

        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        result = int(chinese_chars * 1.5 + other_chars * 0.25)

        elapsed = time.time() - start_time
        logger.info(
            f"[MemoryCompaction][降级估算] 文本 Token 估算完成 "
            f"| 文本长度: {len(text)} "
            f"| 中文字符: {chinese_chars} "
            f"| 其他字符: {other_chars} "
            f"| 估算 token: {result} "
            f"| 耗时: {elapsed:.3f}s"
        )
        return result
