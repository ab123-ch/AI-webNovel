from __future__ import annotations
"""技能数据访问对象"""

import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class Skill(BaseModel):
    """技能模型"""

    id: str
    name: str
    description: str
    expert_id: Optional[str] = None
    prompt: str
    examples: list[dict]
    conditions: list[str]
    steps: list[str]
    success_rate: float = 0.0
    usage_count: int = 0
    source: str  # 'extracted' | 'manual'
    source_session_id: Optional[str] = None
    created_at: int
    updated_at: int

    model_config = {"extra": "forbid"}


class SkillDAO(BaseDAO[Skill]):
    """
    技能数据访问对象

    管理 skills 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "skills"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            expert_id TEXT,
            prompt TEXT NOT NULL,
            examples TEXT NOT NULL,
            conditions TEXT NOT NULL,
            steps TEXT NOT NULL,
            success_rate REAL NOT NULL DEFAULT 0.0,
            usage_count INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL,
            source_session_id TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_skill_expert
            ON skills(expert_id);
        CREATE INDEX IF NOT EXISTS idx_skill_source
            ON skills(source);
        CREATE INDEX IF NOT EXISTS idx_skill_success
            ON skills(success_rate DESC);
        """

    def create(self, model: Skill) -> Skill:
        """创建技能"""
        sql = """
        INSERT INTO skills (
            id, name, description, expert_id, prompt, examples,
            conditions, steps, success_rate, usage_count,
            source, source_session_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.name,
            model.description,
            model.expert_id,
            model.prompt,
            json.dumps(model.examples),
            json.dumps(model.conditions),
            json.dumps(model.steps),
            model.success_rate,
            model.usage_count,
            model.source,
            model.source_session_id,
            model.created_at,
            model.updated_at
        ))
        logger.info(f"[SkillDAO] 创建技能: {model.name}")
        return model

    def get_by_id(self, id: str) -> Optional[Skill]:
        """按 ID 获取技能"""
        sql = "SELECT * FROM skills WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def get_by_name(self, name: str) -> Optional[Skill]:
        """按名称获取技能"""
        sql = "SELECT * FROM skills WHERE name = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (name,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: Skill) -> Skill:
        """更新技能"""
        import time
        model.updated_at = int(time.time())

        sql = """
        UPDATE skills SET
            description = ?, expert_id = ?, prompt = ?, examples = ?,
            conditions = ?, steps = ?, success_rate = ?, usage_count = ?,
            updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.description,
            model.expert_id,
            model.prompt,
            json.dumps(model.examples),
            json.dumps(model.conditions),
            json.dumps(model.steps),
            model.success_rate,
            model.usage_count,
            model.updated_at,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除技能"""
        sql = "DELETE FROM skills WHERE id = ?"
        cursor = self.execute(sql, (id,))
        success = cursor.rowcount > 0
        if success:
            logger.info(f"[SkillDAO] 删除技能: id={id}")
        return success

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[Skill]:
        """列出技能"""
        sql = "SELECT * FROM skills"
        params: list = []

        if filters:
            conditions = []
            if "expert_id" in filters:
                conditions.append("expert_id = ?")
                params.append(filters["expert_id"])
            if "source" in filters:
                conditions.append("source = ?")
                params.append(filters["source"])
            if "name_contains" in filters:
                conditions.append("name LIKE ?")
                params.append(f"%{filters['name_contains']}%")
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        if order_by:
            sql += f" ORDER BY {order_by}"
        else:
            sql += " ORDER BY success_rate DESC, usage_count DESC"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def update_success_rate(
        self,
        skill_id: str,
        success: bool
    ) -> None:
        """
        更新成功率

        使用增量更新公式计算新的成功率

        Args:
            skill_id: 技能 ID
            success: 是否成功
        """
        skill = self.get_by_id(skill_id)
        if not skill:
            return

        # 增量更新
        new_count = skill.usage_count + 1
        old_rate = skill.success_rate * skill.usage_count
        new_rate = (old_rate + (1.0 if success else 0.0)) / new_count

        sql = """
        UPDATE skills SET
            success_rate = ?, usage_count = ?, updated_at = ?
        WHERE id = ?
        """
        import time
        self.execute(sql, (new_rate, new_count, int(time.time()), skill_id))

    def get_by_expert(self, expert_id: str) -> list[Skill]:
        """获取专家的技能列表"""
        return self.list(filters={"expert_id": expert_id})

    def get_top_skills(self, limit: int = 10) -> list[Skill]:
        """获取高成功率技能"""
        return self.list(order_by="success_rate DESC", limit=limit)

    def _row_to_model(self, row: sqlite3.Row) -> Skill:
        """将数据库行转换为模型"""
        return Skill(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            expert_id=row["expert_id"],
            prompt=row["prompt"],
            examples=json.loads(row["examples"]),
            conditions=json.loads(row["conditions"]),
            steps=json.loads(row["steps"]),
            success_rate=row["success_rate"],
            usage_count=row["usage_count"],
            source=row["source"],
            source_session_id=row["source_session_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
