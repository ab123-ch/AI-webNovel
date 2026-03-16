from __future__ import annotations
"""压缩索引数据访问对象"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class CompactionIndex(BaseModel):
    """压缩索引模型"""

    id: str
    session_id: str
    layer: int
    source_memory_ids: list[str]
    source_compaction_ids: Optional[list[str]] = None
    summary: str
    key_topics: list[str]
    key_decisions: list[str]
    key_entities: list[str]
    key_conclusions: list[str]
    task_type: Optional[str] = None
    task_description: Optional[str] = None
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    created_at: int

    model_config = {"extra": "forbid"}


class CompactionIndexDAO(BaseDAO[CompactionIndex]):
    """
    压缩索引数据访问对象

    管理 compaction_index 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "compaction_index"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS compaction_index (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            layer INTEGER NOT NULL,
            source_memory_ids TEXT NOT NULL,
            source_compaction_ids TEXT,
            summary TEXT NOT NULL,
            key_topics TEXT NOT NULL,
            key_decisions TEXT NOT NULL,
            key_entities TEXT NOT NULL,
            key_conclusions TEXT NOT NULL,
            task_type TEXT,
            task_description TEXT,
            original_token_count INTEGER NOT NULL,
            compressed_token_count INTEGER NOT NULL,
            compression_ratio REAL NOT NULL,
            created_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_compaction_session
            ON compaction_index(session_id);
        CREATE INDEX IF NOT EXISTS idx_compaction_layer
            ON compaction_index(layer);
        CREATE INDEX IF NOT EXISTS idx_compaction_created
            ON compaction_index(created_at);
        """

    def create(self, model: CompactionIndex) -> CompactionIndex:
        """创建压缩索引记录"""
        sql = """
        INSERT INTO compaction_index (
            id, session_id, layer, source_memory_ids, source_compaction_ids,
            summary, key_topics, key_decisions, key_entities, key_conclusions,
            task_type, task_description, original_token_count,
            compressed_token_count, compression_ratio, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.session_id,
            model.layer,
            json.dumps(model.source_memory_ids),
            json.dumps(model.source_compaction_ids) if model.source_compaction_ids else None,
            model.summary,
            json.dumps(model.key_topics),
            json.dumps(model.key_decisions),
            json.dumps(model.key_entities),
            json.dumps(model.key_conclusions),
            model.task_type,
            model.task_description,
            model.original_token_count,
            model.compressed_token_count,
            model.compression_ratio,
            model.created_at
        ))
        logger.debug(f"[CompactionIndexDAO] 创建索引: id={model.id}, layer={model.layer}")
        return model

    def get_by_id(self, id: str) -> Optional[CompactionIndex]:
        """按 ID 获取压缩索引"""
        sql = "SELECT * FROM compaction_index WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: CompactionIndex) -> CompactionIndex:
        """更新压缩索引（通常不需要）"""
        sql = """
        UPDATE compaction_index SET
            summary = ?, key_topics = ?, key_decisions = ?,
            key_entities = ?, key_conclusions = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.summary,
            json.dumps(model.key_topics),
            json.dumps(model.key_decisions),
            json.dumps(model.key_entities),
            json.dumps(model.key_conclusions),
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除压缩索引"""
        sql = "DELETE FROM compaction_index WHERE id = ?"
        cursor = self.execute(sql, (id,))
        return cursor.rowcount > 0

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[CompactionIndex]:
        """列出压缩索引"""
        sql = "SELECT * FROM compaction_index"
        params: list = []

        if filters:
            conditions = []
            if "session_id" in filters:
                conditions.append("session_id = ?")
                params.append(filters["session_id"])
            if "layer" in filters:
                conditions.append("layer = ?")
                params.append(filters["layer"])
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        if order_by:
            sql += f" ORDER BY {order_by}"
        else:
            sql += " ORDER BY created_at DESC"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_session(self, session_id: str) -> list[CompactionIndex]:
        """获取会话的所有压缩索引"""
        return self.list(filters={"session_id": session_id})

    def get_by_layer(self, layer: int, limit: int = 100) -> list[CompactionIndex]:
        """获取指定层级的压缩索引"""
        return self.list(filters={"layer": layer}, limit=limit)

    def get_source_ids(self, compaction_id: str) -> dict[str, list[str]]:
        """
        获取压缩索引的源 ID

        Returns:
            {
                "memory_ids": [...],
                "compaction_ids": [...]
            }
        """
        index = self.get_by_id(compaction_id)
        if not index:
            return {"memory_ids": [], "compaction_ids": []}

        return {
            "memory_ids": index.source_memory_ids,
            "compaction_ids": index.source_compaction_ids or []
        }

    def _row_to_model(self, row: sqlite3.Row) -> CompactionIndex:
        """将数据库行转换为模型"""
        return CompactionIndex(
            id=row["id"],
            session_id=row["session_id"],
            layer=row["layer"],
            source_memory_ids=json.loads(row["source_memory_ids"]),
            source_compaction_ids=json.loads(row["source_compaction_ids"]) if row["source_compaction_ids"] else None,
            summary=row["summary"],
            key_topics=json.loads(row["key_topics"]),
            key_decisions=json.loads(row["key_decisions"]),
            key_entities=json.loads(row["key_entities"]),
            key_conclusions=json.loads(row["key_conclusions"]),
            task_type=row["task_type"],
            task_description=row["task_description"],
            original_token_count=row["original_token_count"],
            compressed_token_count=row["compressed_token_count"],
            compression_ratio=row["compression_ratio"],
            created_at=row["created_at"]
        )
