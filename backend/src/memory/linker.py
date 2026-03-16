"""任务-记忆关联器

管理任务与记忆之间的关联关系
"""

import hashlib
import json
import logging
import time
import uuid
from typing import Optional

from ..dal import TaskMemoryLink, TaskMemoryLinkDAO

logger = logging.getLogger(__name__)


class TaskMemoryLinker:
    """
    任务-记忆关联器

    职责：
    - 计算任务签名
    - 创建关联
    - 查询关联
    - 更新召回计数

    Example:
        >>> linker = TaskMemoryLinker(link_dao)
        >>> sig = linker.calculate_signature("写章节", ["修仙", "突破"])
        >>> link = linker.create_link(sig, "memory-001", "compaction")
    """

    def __init__(
        self,
        link_dao: TaskMemoryLinkDAO
    ):
        """
        初始化关联器

        Args:
            link_dao: 任务-记忆关联 DAO
        """
        self.dao = link_dao

    def calculate_signature(
        self,
        task: str,
        keywords: list[str]
    ) -> str:
        """
        计算任务签名

        基于任务描述和关键词生成唯一标识

        Args:
            task: 任务描述
            keywords: 关键词列表

        Returns:
            任务签名（SHA256 前 16 位）

        Example:
            >>> sig = linker.calculate_signature(
            ...     "生成修仙小说章节",
            ...     ["修仙", "突破", "境界"]
            ... )
            >>> print(sig)
            'a1b2c3d4e5f67890'
        """
        content = f"{task}|{','.join(sorted(keywords))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def calculate_similarity_signature(
        self,
        task: str,
        keywords: list[str],
        threshold: float = 0.8
    ) -> str:
        """
        计算相似任务签名

        允许一定程度的模糊匹配

        Args:
            task: 任务描述
            keywords: 关键词列表
            threshold: 相似度阈值

        Returns:
            任务签名

        Example:
            >>> sig = linker.calculate_similarity_signature(
            ...     "生成修仙小说的章节内容",
            ...     ["修仙", "突破"],
            ...     threshold=0.7
            ... )
        """
        # 简化任务描述
        simplified_task = self._simplify_task(task)

        # 使用关键词的主要部分
        main_keywords = [kw[:4] if len(kw) > 4 else kw for kw in keywords]

        content = f"{simplified_task}|{','.join(sorted(main_keywords))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _simplify_task(
        self,
        task: str
    ) -> str:
        """
        简化任务描述

        提取核心动词和名词

        Args:
            task: 原始任务描述

        Returns:
            简化后的任务
        """
        # 移除常见修饰词
        stop_words = {"的", "一下", "帮我", "请", "要", "需要", "想要"}

        simplified = task
        for word in stop_words:
            simplified = simplified.replace(word, "")

        # 截断到核心部分
        if len(simplified) > 20:
            simplified = simplified[:20]

        return simplified.strip()

    def create_link(
        self,
        task_signature: str,
        memory_id: str,
        memory_type: str,
        relevance: float = 1.0
    ) -> TaskMemoryLink:
        """
        创建任务-记忆关联

        Args:
            task_signature: 任务签名
            memory_id: 记忆 ID
            memory_type: 记忆类型 ('message' | 'compaction')
            relevance: 相关性分数 (0-1)

        Returns:
            关联记录

        Example:
            >>> link = linker.create_link(
            ...     task_signature="a1b2c3d4",
            ...     memory_id="idx-001",
            ...     memory_type="compaction",
            ...     relevance=0.9
            ... )
        """
        now = int(time.time())

        model = TaskMemoryLink(
            id=str(uuid.uuid4())[:8],
            task_signature=task_signature,
            memory_id=memory_id,
            memory_type=memory_type,
            relevance_score=relevance,
            recall_count=0,
            last_recalled_at=now,
            created_at=now
        )

        return self.dao.create(model)

    def find_or_create_link(
        self,
        task_signature: str,
        memory_id: str,
        memory_type: str,
        relevance: float = 1.0
    ) -> TaskMemoryLink:
        """
        查找或创建关联

        如果已存在则返回现有记录

        Args:
            task_signature: 任务签名
            memory_id: 记忆 ID
            memory_type: 记忆类型
            relevance: 相关性分数

        Returns:
            关联记录

        Example:
            >>> link = linker.find_or_create_link(
            ...     "a1b2c3d4",
            ...     "idx-001",
            ...     "compaction"
            ... )
        """
        return self.dao.find_or_create(
            task_signature=task_signature,
            memory_id=memory_id,
            memory_type=memory_type,
            relevance=relevance
        )

    def get_task_memories(
        self,
        task_signature: str,
        limit: int = 10
    ) -> list[TaskMemoryLink]:
        """
        获取任务关联的记忆

        Args:
            task_signature: 任务签名
            limit: 返回数量限制

        Returns:
            关联记录列表

        Example:
            >>> links = linker.get_task_memories("a1b2c3d4")
            >>> for link in links:
            ...     print(f"{link.memory_id}: score={link.relevance_score}")
        """
        return self.dao.get_task_memories(task_signature, limit)

    def get_similar_task_memories(
        self,
        task_signature: str,
        prefix_len: int = 8,
        limit: int = 10
    ) -> list[TaskMemoryLink]:
        """
        获取相似任务关联的记忆

        使用签名前缀匹配实现模糊检索

        Args:
            task_signature: 任务签名
            prefix_len: 签名前缀长度
            limit: 返回数量限制

        Returns:
            关联记录列表

        Example:
            >>> links = linker.get_similar_task_memories("a1b2c3d4", prefix_len=6)
        """
        prefix = task_signature[:prefix_len]

        # 获取所有关联（简单实现）
        all_links = self.dao.list(limit=200)

        # 筛选前缀匹配的
        matched = [
            link for link in all_links
            if link.task_signature.startswith(prefix)
        ]

        # 按相关性和召回次数排序
        matched.sort(
            key=lambda x: (x.relevance_score, x.recall_count),
            reverse=True
        )

        return matched[:limit]

    def increment_recall(
        self,
        link_id: str
    ) -> None:
        """
        增加召回计数

        Args:
            link_id: 关联记录 ID

        Example:
            >>> linker.increment_recall("abc123")
        """
        self.dao.increment_recall(link_id)

    def batch_create_links(
        self,
        task_signature: str,
        memory_ids: list[str],
        memory_type: str,
        relevance_scores: Optional[list[float]] = None
    ) -> list[TaskMemoryLink]:
        """
        批量创建关联

        Args:
            task_signature: 任务签名
            memory_ids: 记忆 ID 列表
            memory_type: 记忆类型
            relevance_scores: 相关性分数列表（可选）

        Returns:
            关联记录列表

        Example:
            >>> links = linker.batch_create_links(
            ...     "a1b2c3d4",
            ...     ["idx-001", "idx-002", "idx-003"],
            ...     "compaction",
            ...     relevance_scores=[0.9, 0.8, 0.7]
            ... )
        """
        if relevance_scores is None:
            relevance_scores = [1.0] * len(memory_ids)

        results: list[TaskMemoryLink] = []
        for mid, rel in zip(memory_ids, relevance_scores):
            link = self.find_or_create_link(
                task_signature=task_signature,
                memory_id=mid,
                memory_type=memory_type,
                relevance=rel
            )
            results.append(link)

        logger.debug(
            f"[TaskMemoryLinker] 批量创建关联: "
            f"sig={task_signature[:8]}, count={len(results)}"
        )

        return results

    def cleanup_low_relevance(
        self,
        min_recall_count: int = 1,
        max_relevance_threshold: float = 0.3
    ) -> int:
        """
        清理低相关性关联

        Args:
            min_recall_count: 最小保留召回次数
            max_relevance_threshold: 最大清理相关性阈值

        Returns:
            清理的记录数量

        Example:
            >>> deleted = linker.cleanup_low_relevance()
            >>> print(f"清理了 {deleted} 条低相关性关联")
        """
        all_links = self.dao.list(limit=1000)
        deleted_count = 0

        for link in all_links:
            # 保留有一定召回的关联
            if link.recall_count >= min_recall_count:
                continue

            # 删除低相关性且无召回的关联
            if link.relevance_score < max_relevance_threshold:
                if self.dao.delete(link.id):
                    deleted_count += 1

        logger.info(
            f"[TaskMemoryLinker] 清理低相关性关联: deleted={deleted_count}"
        )

        return deleted_count

    def get_link_stats(self) -> dict:
        """
        获取关联统计

        Returns:
            {
                "total": 总关联数,
                "by_type": {type: count},
                "avg_relevance": 平均相关性,
                "avg_recall": 平均召回次数
            }

        Example:
            >>> stats = linker.get_link_stats()
            >>> print(f"平均相关性: {stats['avg_relevance']:.2f}")
        """
        all_links = self.dao.list(limit=10000)

        if not all_links:
            return {
                "total": 0,
                "by_type": {},
                "avg_relevance": 0.0,
                "avg_recall": 0.0
            }

        by_type: dict[str, int] = {}
        total_relevance = 0.0
        total_recall = 0

        for link in all_links:
            by_type[link.memory_type] = by_type.get(link.memory_type, 0) + 1
            total_relevance += link.relevance_score
            total_recall += link.recall_count

        return {
            "total": len(all_links),
            "by_type": by_type,
            "avg_relevance": total_relevance / len(all_links),
            "avg_recall": total_recall / len(all_links)
        }
