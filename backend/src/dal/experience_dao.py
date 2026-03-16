from __future__ import annotations
"""经验数据访问对象"""

import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class Experience(BaseModel):
    """经验模型"""

    id: str
    session_id: str
    type: str  # 'success' | 'failure' | 'learning'
    task: str
    context: str
    result: str
    insight: str
    tags: list[str]
    score: int  # 1-10
    created_at: int

    model_config = {"extra": "forbid"}


class ExperienceDAO(BaseDAO[Experience]):
    """
    经验数据访问对象

    管理 experiences 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "experiences"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS experiences (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            type TEXT NOT NULL,
            task TEXT NOT NULL,
            context TEXT NOT NULL,
            result TEXT NOT NULL,
            insight TEXT NOT NULL,
            tags TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_exp_session
            ON experiences(session_id);
        CREATE INDEX IF NOT EXISTS idx_exp_type
            ON experiences(type);
        CREATE INDEX IF NOT EXISTS idx_exp_score
            ON experiences(score DESC);
        """

    def create(self, model: Experience) -> Experience:
        """创建经验记录"""
        sql = """
        INSERT INTO experiences (
            id, session_id, type, task, context, result, insight, tags, score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.session_id,
            model.type,
            model.task,
            model.context,
            model.result,
            model.insight,
            json.dumps(model.tags),
            model.score,
            model.created_at
        ))
        logger.debug(f"[ExperienceDAO] 创建经验: type={model.type}, score={model.score}")
        return model

    def get_by_id(self, id: str) -> Optional[Experience]:
        """按 ID 获取经验"""
        sql = "SELECT * FROM experiences WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: Experience) -> Experience:
        """更新经验（通常不需要）"""
        sql = """
        UPDATE experiences SET
            insight = ?, tags = ?, score = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.insight,
            json.dumps(model.tags),
            model.score,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除经验"""
        sql = "DELETE FROM experiences WHERE id = ?"
        cursor = self.execute(sql, (id,))
        return cursor.rowcount > 0

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[Experience]:
        """列出经验"""
        sql = "SELECT * FROM experiences"
        params: list = []

        if filters:
            conditions = []
            if "session_id" in filters:
                conditions.append("session_id = ?")
                params.append(filters["session_id"])
            if "type" in filters:
                conditions.append("type = ?")
                params.append(filters["type"])
            if "min_score" in filters:
                conditions.append("score >= ?")
                params.append(filters["min_score"])
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY {order_by or 'score DESC, created_at DESC'}"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_high_score_experiences(
        self,
        min_score: int = 8,
        limit: int = 20
    ) -> list[Experience]:
        """获取高分经验"""
        return self.list(
            filters={"min_score": min_score},
            limit=limit
        )

    def get_session_experiences(
        self,
        session_id: str
    ) -> list[Experience]:
        """获取会话的经验"""
        return self.list(filters={"session_id": session_id})

    def get_successful_experiences(
        self,
        limit: int = 50
    ) -> list[Experience]:
        """获取成功经验"""
        return self.list(
            filters={"type": "success"},
            limit=limit
        )

    def get_failed_experiences(
        self,
        limit: int = 50
    ) -> list[Experience]:
        """获取失败经验（用于学习）"""
        return self.list(
            filters={"type": "failure"},
            limit=limit
        )

    def search_by_tags(
        self,
        tags: list[str],
        limit: int = 20
    ) -> list[Experience]:
        """
        按标签搜索经验

        Args:
            tags: 标签列表
            limit: 返回数量限制

        Returns:
            匹配的经验列表
        """
        if not tags:
            return []

        # 构建查询条件
        conditions = " OR ".join(["tags LIKE ?" for _ in tags])
        params = [f'%"{tag}%"' for tag in tags]

        sql = f"""
        SELECT * FROM experiences
        WHERE {conditions}
        ORDER BY score DESC, created_at DESC
        LIMIT {limit}
        """

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_stats(self) -> dict:
        """
        获取经验统计

        Returns:
            {
                "total": 总数,
                "by_type": {type: count},
                "avg_score": 平均分
            }
        """
        sql_total = "SELECT COUNT(*) as total FROM experiences"
        sql_by_type = "SELECT type, COUNT(*) as count FROM experiences GROUP BY type"
        sql_avg = "SELECT AVG(score) as avg FROM experiences"

        conn = self.get_connection()

        total = conn.execute(sql_total).fetchone()["total"]

        by_type = {}
        cursor = conn.execute(sql_by_type)
        for row in cursor.fetchall():
            by_type[row["type"]] = row["count"]

        avg_row = conn.execute(sql_avg).fetchone()
        avg = round(avg_row["avg"], 2) if avg_row["avg"] else 0.0

        return {
            "total": total,
            "by_type": by_type,
            "avg_score": avg
        }

    def _row_to_model(self, row: sqlite3.Row) -> Experience:
        """将数据库行转换为模型"""
        return Experience(
            id=row["id"],
            session_id=row["session_id"],
            type=row["type"],
            task=row["task"],
            context=row["context"],
            result=row["result"],
            insight=row["insight"],
            tags=json.loads(row["tags"]),
            score=row["score"],
            created_at=row["created_at"]
        )
