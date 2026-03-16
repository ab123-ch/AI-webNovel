from __future__ import annotations
"""任务-记忆关联数据访问对象"""

import hashlib
import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class TaskMemoryLink(BaseModel):
    """任务-记忆关联模型"""

    id: str
    task_signature: str
    memory_id: str
    memory_type: str  # 'message' | 'compaction'
    relevance_score: float
    recall_count: int
    last_recalled_at: int
    created_at: int

    model_config = {"extra": "forbid"}


class TaskMemoryLinkDAO(BaseDAO[TaskMemoryLink]):
    """
    任务-记忆关联数据访问对象

    管理 task_memory_link 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "task_memory_link"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS task_memory_link (
            id TEXT PRIMARY KEY,
            task_signature TEXT NOT NULL,
            memory_id TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            relevance_score REAL NOT NULL DEFAULT 0.0,
            recall_count INTEGER NOT NULL DEFAULT 0,
            last_recalled_at INTEGER,
            created_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_link_signature
            ON task_memory_link(task_signature);
        CREATE INDEX IF NOT EXISTS idx_link_memory
            ON task_memory_link(memory_id);
        CREATE INDEX IF NOT EXISTS idx_link_relevance
            ON task_memory_link(relevance_score DESC);
        """

    def create(self, model: TaskMemoryLink) -> TaskMemoryLink:
        """创建关联记录"""
        sql = """
        INSERT INTO task_memory_link (
            id, task_signature, memory_id, memory_type,
            relevance_score, recall_count, last_recalled_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.task_signature,
            model.memory_id,
            model.memory_type,
            model.relevance_score,
            model.recall_count,
            model.last_recalled_at,
            model.created_at
        ))
        logger.debug(f"[TaskMemoryLinkDAO] 创建关联: sig={model.task_signature[:16]}...")
        return model

    def get_by_id(self, id: str) -> Optional[TaskMemoryLink]:
        """按 ID 获取关联"""
        sql = "SELECT * FROM task_memory_link WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: TaskMemoryLink) -> TaskMemoryLink:
        """更新关联"""
        sql = """
        UPDATE task_memory_link SET
            relevance_score = ?, recall_count = ?, last_recalled_at = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.relevance_score,
            model.recall_count,
            model.last_recalled_at,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除关联"""
        sql = "DELETE FROM task_memory_link WHERE id = ?"
        cursor = self.execute(sql, (id,))
        return cursor.rowcount > 0

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[TaskMemoryLink]:
        """列出关联"""
        sql = "SELECT * FROM task_memory_link"
        params: list = []

        if filters:
            conditions = []
            if "task_signature" in filters:
                conditions.append("task_signature = ?")
                params.append(filters["task_signature"])
            if "memory_type" in filters:
                conditions.append("memory_type = ?")
                params.append(filters["memory_type"])
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        if order_by:
            sql += f" ORDER BY {order_by}"
        else:
            sql += " ORDER BY relevance_score DESC, recall_count DESC"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_task_memories(
        self,
        task_signature: str,
        limit: int = 10
    ) -> list[TaskMemoryLink]:
        """获取任务关联的记忆"""
        return self.list(
            filters={"task_signature": task_signature},
            order_by="relevance_score DESC, recall_count DESC",
            limit=limit
        )

    def increment_recall(self, link_id: str) -> None:
        """增加召回计数"""
        import time
        sql = """
        UPDATE task_memory_link SET
            recall_count = recall_count + 1,
            last_recalled_at = ?
        WHERE id = ?
        """
        self.execute(sql, (int(time.time()), link_id))

    def calculate_signature(self, task: str, keywords: list[str]) -> str:
        """
        计算任务签名

        用于唯一标识任务类型

        Args:
            task: 任务描述
            keywords: 关键词列表

        Returns:
            SHA256 签名（前 16 位）
        """
        content = f"{task}|{','.join(sorted(keywords))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def find_or_create(
        self,
        task_signature: str,
        memory_id: str,
        memory_type: str,
        relevance: float = 1.0
    ) -> TaskMemoryLink:
        """
        查找或创建关联

        如果已存在相同签名和 memory_id 的关联，返回现有记录

        Args:
            task_signature: 任务签名
            memory_id: 记忆 ID
            memory_type: 记忆类型
            relevance: 相关性分数

        Returns:
            关联记录
        """
        import time
        import uuid

        # 查找现有记录
        sql = """
        SELECT * FROM task_memory_link
        WHERE task_signature = ? AND memory_id = ?
        """
        conn = self.get_connection()
        cursor = conn.execute(sql, (task_signature, memory_id))
        row = cursor.fetchone()

        if row:
            return self._row_to_model(row)

        # 创建新记录
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
        return self.create(model)

    def get_by_signature_prefix(
        self,
        prefix: str,
        limit: int = 10
    ) -> list[TaskMemoryLink]:
        """
        按签名前缀查询

        使用 SQL LIKE 查询替代内存筛选，提高大数据量时的性能

        Args:
            prefix: 签名前缀
            limit: 返回数量限制

        Returns:
            匹配的关联记录列表

        Example:
            >>> links = dao.get_by_signature_prefix("a1b2c3d4", limit=10)
        """
        sql = """
        SELECT * FROM task_memory_link
        WHERE task_signature LIKE ?
        ORDER BY relevance_score DESC, recall_count DESC
        LIMIT ?
        """
        conn = self.get_connection()
        cursor = conn.execute(sql, (f"{prefix}%", limit))
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def _row_to_model(self, row: sqlite3.Row) -> TaskMemoryLink:
        """将数据库行转换为模型"""
        return TaskMemoryLink(
            id=row["id"],
            task_signature=row["task_signature"],
            memory_id=row["memory_id"],
            memory_type=row["memory_type"],
            relevance_score=row["relevance_score"],
            recall_count=row["recall_count"],
            last_recalled_at=row["last_recalled_at"],
            created_at=row["created_at"]
        )
