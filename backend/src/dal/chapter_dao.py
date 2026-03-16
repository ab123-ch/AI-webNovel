"""小说章节数据访问对象"""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseDAO

logger = logging.getLogger(__name__)


class NovelChapter(BaseModel):
    """小说章节模型"""

    id: str
    project_id: str
    chapter_num: int
    title: str
    outline: Optional[str] = None  # 章纲
    content: Optional[str] = None  # 正文
    word_count: int = 0
    status: str  # outline, draft, completed, revised
    score: Optional[int] = None  # 评分 1-10
    feedback: Optional[str] = None  # 反馈
    created_at: int
    updated_at: int

    model_config = {"extra": "forbid"}


class NovelChapterDAO(BaseDAO[NovelChapter]):
    """
    小说章节数据访问对象

    管理 novel_chapters 表的 CRUD 操作
    """

    @property
    def table_name(self) -> str:
        return "novel_chapters"

    @property
    def create_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS novel_chapters (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            chapter_num INTEGER NOT NULL,
            title TEXT NOT NULL,
            outline TEXT,
            content TEXT,
            word_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'outline',
            score INTEGER,
            feedback TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            UNIQUE(project_id, chapter_num)
        );

        CREATE INDEX IF NOT EXISTS idx_chapter_project
            ON novel_chapters(project_id);
        CREATE INDEX IF NOT EXISTS idx_chapter_status
            ON novel_chapters(status);
        """

    def create(self, model: NovelChapter) -> NovelChapter:
        """创建章节"""
        sql = """
        INSERT INTO novel_chapters (
            id, project_id, chapter_num, title, outline, content,
            word_count, status, score, feedback, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            model.id,
            model.project_id,
            model.chapter_num,
            model.title,
            model.outline,
            model.content,
            model.word_count,
            model.status,
            model.score,
            model.feedback,
            model.created_at,
            model.updated_at
        ))
        logger.info(f"[NovelChapterDAO] 创建章节: 第{model.chapter_num}章 - {model.title}")
        return model

    def get_by_id(self, id: str) -> Optional[NovelChapter]:
        """按 ID 获取章节"""
        sql = "SELECT * FROM novel_chapters WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def get_by_number(
        self,
        project_id: str,
        chapter_num: int
    ) -> Optional[NovelChapter]:
        """按章节号获取"""
        sql = """
        SELECT * FROM novel_chapters
        WHERE project_id = ? AND chapter_num = ?
        """
        conn = self.get_connection()
        cursor = conn.execute(sql, (project_id, chapter_num))
        row = cursor.fetchone()
        if row:
            return self._row_to_model(row)
        return None

    def update(self, model: NovelChapter) -> NovelChapter:
        """更新章节"""
        sql = """
        UPDATE novel_chapters SET
            title = ?, outline = ?, content = ?, word_count = ?,
            status = ?, score = ?, feedback = ?, updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (
            model.title,
            model.outline,
            model.content,
            model.word_count,
            model.status,
            model.score,
            model.feedback,
            model.updated_at,
            model.id
        ))
        return model

    def delete(self, id: str) -> bool:
        """删除章节"""
        sql = "DELETE FROM novel_chapters WHERE id = ?"
        cursor = self.execute(sql, (id,))
        return cursor.rowcount > 0

    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[NovelChapter]:
        """列出章节"""
        sql = "SELECT * FROM novel_chapters"
        params: list = []

        if filters:
            conditions = []
            if "project_id" in filters:
                conditions.append("project_id = ?")
                params.append(filters["project_id"])
            if "status" in filters:
                conditions.append("status = ?")
                params.append(filters["status"])
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY {order_by or 'chapter_num ASC'}"

        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        conn = self.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_project_chapters(
        self,
        project_id: str
    ) -> list[NovelChapter]:
        """获取项目的所有章节"""
        return self.list(filters={"project_id": project_id})

    def get_latest_chapter(
        self,
        project_id: str
    ) -> Optional[NovelChapter]:
        """获取最新章节"""
        chapters = self.list(
            filters={"project_id": project_id},
            order_by="chapter_num DESC",
            limit=1
        )
        return chapters[0] if chapters else None

    def get_next_chapter_num(self, project_id: str) -> int:
        """获取下一个章节号"""
        sql = "SELECT MAX(chapter_num) as max FROM novel_chapters WHERE project_id = ?"
        conn = self.get_connection()
        cursor = conn.execute(sql, (project_id,))
        row = cursor.fetchone()
        if row and row["max"]:
            return row["max"] + 1
        return 1

    def update_content(
        self,
        chapter_id: str,
        content: str,
        status: str = "completed"
    ) -> None:
        """更新章节内容"""
        import time
        word_count = len(content.replace(" ", "").replace("\n", ""))

        sql = """
        UPDATE novel_chapters SET
            content = ?, word_count = ?, status = ?, updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (content, word_count, status, int(time.time()), chapter_id))

    def update_outline(
        self,
        chapter_id: str,
        outline: str
    ) -> None:
        """更新章节大纲"""
        import time
        sql = """
        UPDATE novel_chapters SET
            outline = ?, status = 'outline', updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (outline, int(time.time()), chapter_id))

    def update_score(
        self,
        chapter_id: str,
        score: int,
        feedback: Optional[str] = None
    ) -> None:
        """更新章节评分"""
        import time
        sql = """
        UPDATE novel_chapters SET
            score = ?, feedback = ?, updated_at = ?
        WHERE id = ?
        """
        self.execute(sql, (score, feedback, int(time.time()), chapter_id))

    def get_stats(self, project_id: str) -> dict:
        """
        获取项目统计

        Returns:
            {
                "total_chapters": 总章节数,
                "completed_chapters": 已完成章节,
                "total_words": 总字数,
                "avg_score": 平均分
            }
        """
        sql = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(word_count) as words,
            AVG(score) as avg
        FROM novel_chapters
        WHERE project_id = ?
        """
        conn = self.get_connection()
        cursor = conn.execute(sql, (project_id,))
        row = cursor.fetchone()

        return {
            "total_chapters": row["total"] or 0,
            "completed_chapters": row["completed"] or 0,
            "total_words": row["words"] or 0,
            "avg_score": round(row["avg"], 2) if row["avg"] else 0.0
        }

    def _row_to_model(self, row: sqlite3.Row) -> NovelChapter:
        """将数据库行转换为模型"""
        return NovelChapter(
            id=row["id"],
            project_id=row["project_id"],
            chapter_num=row["chapter_num"],
            title=row["title"],
            outline=row["outline"],
            content=row["content"],
            word_count=row["word_count"],
            status=row["status"],
            score=row["score"],
            feedback=row["feedback"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
