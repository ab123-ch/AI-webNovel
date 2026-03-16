from __future__ import annotations
"""专家数据访问对象"""

import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class Expert(BaseModel):
    """专家模型"""

    id: str
    name: str
    domain: str
    description: str
    keywords: list[str]
    system_prompt: str
    capabilities: list[str]
    is_builtin: bool = False
    usage_count: int = 0
    created_at: int
    updated_at: int

    model_config = {"extra": "forbid"}


class ExpertDAO(BaseDAO[Expert]):
    """
    专家数据访问对象

    管理 experts 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "experts"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS experts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            domain TEXT NOT NULL,
            description TEXT NOT NULL,
            keywords TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            capabilities TEXT NOT NULL,
            is_builtin INTEGER NOT NULL DEFAULT 0,
            usage_count INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_expert_domain
            ON experts(domain);
        CREATE INDEX IF NOT EXISTS idx_expert_builtin
            ON experts(is_builtin);
        """

    def create(self, model: Expert) -> Expert:
        """创建专家"""
        sql = """
        INSERT INTO experts (
            id, name, domain, description, keywords, system_prompt,
            capabilities, is_builtin, usage_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.name,
            model.domain,
            model.description,
            json.dumps(model.keywords),
            model.system_prompt,
            json.dumps(model.capabilities),
            1 if model.is_builtin else 0,
            model.usage_count,
            model.created_at,
            model.updated_at
        ))
        logger.info(f"[ExpertDAO] 创建专家: {model.name} ({model.domain})")
        return model

    def get_by_id(self, id: str) -> Optional[Expert]:
        """按 ID 获取专家"""
        sql = "SELECT * FROM experts WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def get_by_name(self, name: str) -> Optional[Expert]:
        """按名称获取专家"""
        sql = "SELECT * FROM experts WHERE name = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (name,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: Expert) -> Expert:
        """更新专家"""
        import time
        model.updated_at = int(time.time())

        sql = """
        UPDATE experts SET
            domain = ?, description = ?, keywords = ?,
            system_prompt = ?, capabilities = ?, usage_count = ?, updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.domain,
            model.description,
            json.dumps(model.keywords),
            model.system_prompt,
            json.dumps(model.capabilities),
            model.usage_count,
            model.updated_at,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除专家"""
        # 不允许删除内置专家
        expert = self.get_by_id(id)
        if expert and expert.is_builtin:
            logger.warning(f"[ExpertDAO] 不允许删除内置专家: {expert.name}")
            return False

        sql = "DELETE FROM experts WHERE id = ?"
        cursor = self.execute(sql, (id,))
        success = cursor.rowcount > 0
        if success:
            logger.info(f"[ExpertDAO] 删除专家: id={id}")
        return success

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[Expert]:
        """列出专家"""
        sql = "SELECT * FROM experts"
        params: list = []

        if filters:
            conditions = []
            if "domain" in filters:
                conditions.append("domain = ?")
                params.append(filters["domain"])
            if "is_builtin" in filters:
                conditions.append("is_builtin = ?")
                params.append(1 if filters["is_builtin"] else 0)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY {order_by or 'usage_count DESC, name'}"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def increment_usage(self, expert_id: str) -> None:
        """增加使用计数"""
        sql = """
        UPDATE experts SET
            usage_count = usage_count + 1,
            updated_at = ?
        WHERE id = ?
        """
        import time
        self.execute(sql, (int(time.time()), expert_id))

    def get_builtin_experts(self) -> list[Expert]:
        """获取内置专家列表"""
        return self.list(filters={"is_builtin": True})

    def get_by_domain(self, domain: str) -> list[Expert]:
        """获取领域专家"""
        return self.list(filters={"domain": domain})

    def search_by_keywords(
        self,
        query: str,
        limit: int = 5
    ) -> list[tuple[Expert, float]]:
        """
        按关键词搜索专家

        Args:
            query: 查询字符串
            limit: 返回数量限制

        Returns:
            (专家, 匹配分数) 列表
        """
        experts = self.list()
        results: list[tuple[Expert, float]] = []

        query_lower = query.lower()
        for expert in experts:
            score = 0.0
            for kw in expert.keywords:
                if kw.lower() in query_lower:
                    score += 1.0 / len(expert.keywords)
            if score > 0:
                results.append((expert, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _row_to_model(self, row: sqlite3.Row) -> Expert:
        """将数据库行转换为模型"""
        return Expert(
            id=row["id"],
            name=row["name"],
            domain=row["domain"],
            description=row["description"],
            keywords=json.loads(row["keywords"]),
            system_prompt=row["system_prompt"],
            capabilities=json.loads(row["capabilities"]),
            is_builtin=bool(row["is_builtin"]),
            usage_count=row["usage_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
