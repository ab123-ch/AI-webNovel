"""记忆回顾服务

实现任务驱动的记忆检索和相关性排序
"""

import json
import logging
import time
from typing import Optional

from ..dal import CompactionIndexDAO, TaskMemoryLink, TaskMemoryLinkDAO
from ..opencode import OpenCodeTasks

logger = logging.getLogger(__name__)


class MemoryReview:
    """
    记忆回顾服务

    职责：
    - 任务驱动检索
    - 关键词检索
    - 时间范围检索
    - 相关性排序
    - 召回计数更新

    Example:
        >>> review = MemoryReview(tasks, compaction_dao, link_dao)
        >>> memories = await review.review_by_task("write_chapter", keywords=["修仙"])
    """

    def __init__(
        self,
        opencode_tasks: OpenCodeTasks,
        compaction_dao: CompactionIndexDAO,
        link_dao: TaskMemoryLinkDAO
    ):
        """
        初始化记忆回顾服务

        Args:
            opencode_tasks: OpenCode 任务封装器
            compaction_dao: 压缩索引 DAO
            link_dao: 任务-记忆关联 DAO
        """
        self.tasks = opencode_tasks
        self.compaction_dao = compaction_dao
        self.link_dao = link_dao

    async def review_by_task(
        self,
        task_signature: str,
        limit: int = 10
    ) -> list[dict]:
        """
        任务驱动检索

        根据任务签名检索相关记忆

        Args:
            task_signature: 任务签名
            limit: 返回数量限制

        Returns:
            记忆列表，按相关性排序

        Example:
            >>> memories = await review.review_by_task(
            ...     "write_chapter_修仙_1",
            ...     limit=5
            ... )
        """
        # 从关联表获取匹配的记忆
        links = self.link_dao.get_task_memories(task_signature, limit=limit * 2)

        # 获取详细内容
        results: list[dict] = []
        for link in links:
            if link.memory_type == "compaction":
                index = self.compaction_dao.get_by_id(link.memory_id)
                if index:
                    results.append({
                        "id": index.id,
                        "type": "compaction",
                        "layer": index.layer,
                        "summary": index.summary,
                        "key_topics": index.key_topics,
                        "key_entities": index.key_entities,
                        "relevance_score": link.relevance_score,
                        "recall_count": link.recall_count,
                        "created_at": index.created_at
                    })
            else:
                # 消息类型（需要从消息存储获取）
                results.append({
                    "id": link.memory_id,
                    "type": "message",
                    "relevance_score": link.relevance_score,
                    "recall_count": link.recall_count,
                    "created_at": link.created_at
                })

        # 相关性排序
        results = self._rank_relevance(results)

        # 更新召回计数
        for link in links[:limit]:
            self.link_dao.increment_recall(link.id)

        logger.debug(
            f"[MemoryReview] 任务检索: sig={task_signature[:16]}..., "
            f"found={len(results)}"
        )

        return results[:limit]

    async def review_by_keywords(
        self,
        keywords: list[str],
        limit: int = 10
    ) -> list[dict]:
        """
        关键词检索

        使用 FTS5 全文搜索

        Args:
            keywords: 关键词列表
            limit: 返回数量限制

        Returns:
            匹配的记忆列表

        Example:
            >>> memories = await review.review_by_keywords(
            ...     ["修仙", "突破", "境界"]
            ... )
        """
        # 构建搜索查询
        query = " ".join(keywords)

        # 使用全文搜索
        # TODO: 实现实际的 FTS 搜索
        # 目前使用简单的 LIKE 搜索
        all_indexes = self.compaction_dao.list(limit=100)

        results: list[dict] = []
        for index in all_indexes:
            # 计算匹配分数
            score = self._calculate_keyword_score(index, keywords)
            if score > 0:
                results.append({
                    "id": index.id,
                    "type": "compaction",
                    "layer": index.layer,
                    "summary": index.summary,
                    "key_topics": index.key_topics,
                    "key_entities": index.key_entities,
                    "relevance_score": score,
                    "recall_count": 0,
                    "created_at": index.created_at
                })

        # 按分数排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        logger.debug(
            f"[MemoryReview] 关键词检索: keywords={keywords}, "
            f"found={len(results)}"
        )

        return results[:limit]

    async def review_by_time(
        self,
        start: int,
        end: int,
        limit: int = 20
    ) -> list[dict]:
        """
        时间范围检索

        Args:
            start: 开始时间戳
            end: 结束时间戳
            limit: 返回数量限制

        Returns:
            时间范围内的记忆列表

        Example:
            >>> import time
            >>> now = int(time.time())
            >>> memories = await review.review_by_time(
            ...     now - 86400 * 7,  # 一周前
            ...     now
            ... )
        """
        all_indexes = self.compaction_dao.list(limit=500)

        results: list[dict] = []
        for index in all_indexes:
            if start <= index.created_at <= end:
                results.append({
                    "id": index.id,
                    "type": "compaction",
                    "layer": index.layer,
                    "summary": index.summary,
                    "key_topics": index.key_topics,
                    "key_entities": index.key_entities,
                    "relevance_score": 1.0,
                    "recall_count": 0,
                    "created_at": index.created_at
                })

        # 按时间排序
        results.sort(key=lambda x: x["created_at"], reverse=True)

        logger.debug(
            f"[MemoryReview] 时间检索: range=[{start}, {end}], "
            f"found={len(results)}"
        )

        return results[:limit]

    def _rank_relevance(
        self,
        results: list[dict]
    ) -> list[dict]:
        """
        相关性排序

        综合考虑：
        - 原始相关性分数
        - 召回次数（越常被召回越重要）
        - 时间衰减（越近越重要）

        Args:
            results: 结果列表

        Returns:
            排序后的结果列表
        """
        now = int(time.time())
        day_seconds = 86400

        for r in results:
            # 基础分数
            base_score = r.get("relevance_score", 0.5)

            # 召回加权
            recall_bonus = min(r.get("recall_count", 0) * 0.05, 0.3)

            # 时间衰减（30 天半衰期）
            age_days = (now - r.get("created_at", now)) / day_seconds
            time_decay = 0.5 ** (age_days / 30)

            # 综合分数
            r["final_score"] = (base_score + recall_bonus) * time_decay

        # 排序
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        return results

    def _calculate_keyword_score(
        self,
        index,
        keywords: list[str]
    ) -> float:
        """
        计算关键词匹配分数

        Args:
            index: 压缩索引
            keywords: 关键词列表

        Returns:
            匹配分数 0-1
        """
        if not keywords:
            return 0.0

        score = 0.0
        all_text = (
            index.summary +
            " ".join(index.key_topics) +
            " ".join(index.key_entities)
        ).lower()

        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in all_text:
                score += 1.0 / len(keywords)

        return min(score, 1.0)

    def update_recall_count(
        self,
        link_id: str
    ) -> None:
        """
        更新召回计数

        Args:
            link_id: 关联记录 ID
        """
        self.link_dao.increment_recall(link_id)

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
            memory_type: 记忆类型
            relevance: 相关性分数

        Returns:
            关联记录
        """
        return self.link_dao.find_or_create(
            task_signature=task_signature,
            memory_id=memory_id,
            memory_type=memory_type,
            relevance=relevance
        )
