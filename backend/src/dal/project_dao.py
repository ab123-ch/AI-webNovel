from __future__ import annotations
"""小说项目数据访问对象"""

import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class NovelProject(BaseModel):
    """小说项目模型"""

    id: str
    title: str
    description: str
    genre: str  # 题材：仙侠、玄幻、都市等
    style: str  # 风格
    status: str  # draft, writing, completed, archived
    core_idea: Optional[str] = None  # 核心创意
    world_setting: Optional[str] = None  # 世界观设定
    outline: Optional[str] = None  # 大纲 JSON
    chapter_count: int = 0
    word_count: int = 0
    created_at: int
    updated_at: int

    model_config = {"extra": "forbid"}


class NovelProjectDAO(BaseDAO[NovelProject]):
    """
    小说项目数据访问对象

    管理 novel_projects 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "novel_projects"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS novel_projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            genre TEXT NOT NULL,
            style TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            core_idea TEXT,
            world_setting TEXT,
            outline TEXT,
            chapter_count INTEGER NOT NULL DEFAULT 0,
            word_count INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_project_status
            ON novel_projects(status);
        CREATE INDEX IF NOT EXISTS idx_project_genre
            ON novel_projects(genre);
        """

    def create(self, model: NovelProject) -> NovelProject:
        """创建项目"""
        sql = """
        INSERT INTO novel_projects (
            id, title, description, genre, style, status,
            core_idea, world_setting, outline, chapter_count, word_count,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.title,
            model.description,
            model.genre,
            model.style,
            model.status,
            model.core_idea,
            model.world_setting,
            model.outline,
            model.chapter_count,
            model.word_count,
            model.created_at,
            model.updated_at
        ))
        logger.info(f"[NovelProjectDAO] 创建项目: {model.title}")
        return model

    def get_by_id(self, id: str) -> Optional[NovelProject]:
        """按 ID 获取项目"""
        sql = "SELECT * FROM novel_projects WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: NovelProject) -> NovelProject:
        """更新项目"""
        sql = """
        UPDATE novel_projects SET
            title = ?, description = ?, genre = ?, style = ?, status = ?,
            core_idea = ?, world_setting = ?, outline = ?,
            chapter_count = ?, word_count = ?, updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.title,
            model.description,
            model.genre,
            model.style,
            model.status,
            model.core_idea,
            model.world_setting,
            model.outline,
            model.chapter_count,
            model.word_count,
            model.updated_at,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除项目"""
        sql = "DELETE FROM novel_projects WHERE id = ?"
        cursor = self.execute(sql, (id,))
        success = cursor.rowcount > 0
        if success:
            logger.info(f"[NovelProjectDAO] 删除项目: id={id}")
        return success

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[NovelProject]:
        """列出项目"""
        sql = "SELECT * FROM novel_projects"
        params: list = []

        if filters:
            conditions = []
            if "status" in filters:
                conditions.append("status = ?")
                params.append(filters["status"])
            if "genre" in filters:
                conditions.append("genre = ?")
                params.append(filters["genre"])
            if "title_contains" in filters:
                conditions.append("title LIKE ?")
                params.append(f"%{filters['title_contains']}%")
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY {order_by or 'updated_at DESC'}"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_active_projects(self, limit: int = 20) -> list[NovelProject]:
        """获取活跃项目"""
        return self.list(
            filters={"status": "writing"},
            limit=limit
        )

    def update_word_count(
        self,
        project_id: str,
        word_delta: int
    ) -> None:
        """
        更新字数

        Args:
            project_id: 项目 ID
            word_delta: 字数增量（可为负）
        """
        sql = """
        UPDATE novel_projects SET
            word_count = MAX(0, word_count + ?),
            updated_at = ?
        WHERE id = ?
        """
        import time
        self.execute(sql, (word_delta, int(time.time()), project_id))

    def increment_chapter_count(self, project_id: str) -> None:
        """增加章节数"""
        sql = """
        UPDATE novel_projects SET
            chapter_count = chapter_count + 1,
            updated_at = ?
        WHERE id = ?
        """
        import time
        self.execute(sql, (int(time.time()), project_id))

    def _row_to_model(self, row: sqlite3.Row) -> NovelProject:
        """将数据库行转换为模型"""
        return NovelProject(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            genre=row["genre"],
            style=row["style"],
            status=row["status"],
            core_idea=row["core_idea"],
            world_setting=row["world_setting"],
            outline=row["outline"],
            chapter_count=row["chapter_count"],
            word_count=row["word_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
