from __future__ import annotations
"""反馈数据访问对象"""

import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class FeedbackRecord(BaseModel):
    """反馈记录模型"""

    id: str
    session_id: str
    memory_id: Optional[str] = None
    type: str  # 'score' | 'comment' | 'modification'
    score: Optional[int] = None
    comment: Optional[str] = None
    original_content: Optional[str] = None
    modified_content: Optional[str] = None
    analysis: Optional[dict] = None
    created_at: int

    model_config = {"extra": "forbid"}


class FeedbackDAO(BaseDAO[FeedbackRecord]):
    """
    反馈数据访问对象

    管理 feedback_records 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "feedback_records"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS feedback_records (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            memory_id TEXT,
            type TEXT NOT NULL,
            score INTEGER,
            comment TEXT,
            original_content TEXT,
            modified_content TEXT,
            analysis TEXT,
            created_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_feedback_session
            ON feedback_records(session_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_type
            ON feedback_records(type);
        CREATE INDEX IF NOT EXISTS idx_feedback_memory
            ON feedback_records(memory_id);
        """

    def create(self, model: FeedbackRecord) -> FeedbackRecord:
        """创建反馈记录"""
        sql = """
        INSERT INTO feedback_records (
            id, session_id, memory_id, type, score, comment,
            original_content, modified_content, analysis, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.session_id,
            model.memory_id,
            model.type,
            model.score,
            model.comment,
            model.original_content,
            model.modified_content,
            json.dumps(model.analysis) if model.analysis else None,
            model.created_at
        ))
        logger.debug(f"[FeedbackDAO] 创建反馈: id={model.id}, type={model.type}")
        return model

    def get_by_id(self, id: str) -> Optional[FeedbackRecord]:
        """按 ID 获取反馈"""
        sql = "SELECT * FROM feedback_records WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: FeedbackRecord) -> FeedbackRecord:
        """更新反馈"""
        sql = """
        UPDATE feedback_records SET
            analysis = ?
        WHERE id = ?
        """
        self.execute(sql, (
            json.dumps(model.analysis) if model.analysis else None,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除反馈"""
        sql = "DELETE FROM feedback_records WHERE id = ?"
        cursor = self.execute(sql, (id,))
        return cursor.rowcount > 0

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[FeedbackRecord]:
        """列出反馈"""
        sql = "SELECT * FROM feedback_records"
        params: list = []

        if filters:
            conditions = []
            if "session_id" in filters:
                conditions.append("session_id = ?")
                params.append(filters["session_id"])
            if "type" in filters:
                conditions.append("type = ?")
                params.append(filters["type"])
            if "memory_id" in filters:
                conditions.append("memory_id = ?")
                params.append(filters["memory_id"])
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY {order_by or 'created_at DESC'}"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_session_feedback(
        self,
        session_id: str,
        feedback_type: Optional[str] = None
    ) -> list[FeedbackRecord]:
        """获取会话的反馈"""
        filters = {"session_id": session_id}
        if feedback_type:
            filters["type"] = feedback_type
        return self.list(filters=filters)

    def get_modifications(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[FeedbackRecord]:
        """获取会话的修改反馈"""
        return self.list(
            filters={"session_id": session_id, "type": "modification"},
            limit=limit
        )

    def get_score_stats(self, session_id: str) -> dict:
        """
        获取会话评分统计

        Returns:
            {
                "count": 评分数量,
                "avg": 平均分,
                "min": 最低分,
                "max": 最高分
            }
        """
        sql = """
        SELECT
            COUNT(*) as count,
            AVG(score) as avg,
            MIN(score) as min,
            MAX(score) as max
        FROM feedback_records
        WHERE session_id = ? AND type = 'score' AND score IS NOT NULL
        """
        conn = self.get_connection()
        cursor = conn.execute(sql, (session_id,))
        row = cursor.fetchone()

        if row and row["count"] > 0:
            return {
                "count": row["count"],
                "avg": round(row["avg"], 2),
                "min": row["min"],
                "max": row["max"]
            }
        return {"count": 0, "avg": 0.0, "min": 0, "max": 0}

    def _row_to_model(self, row: sqlite3.Row) -> FeedbackRecord:
        """将数据库行转换为模型"""
        return FeedbackRecord(
            id=row["id"],
            session_id=row["session_id"],
            memory_id=row["memory_id"],
            type=row["type"],
            score=row["score"],
            comment=row["comment"],
            original_content=row["original_content"],
            modified_content=row["modified_content"],
            analysis=json.loads(row["analysis"]) if row["analysis"] else None,
            created_at=row["created_at"]
        )
