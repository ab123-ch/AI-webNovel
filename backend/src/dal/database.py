from __future__ import annotations
"""数据库管理器

统一管理所有 DAO 和数据库初始化
"""

import logging
import os
import sqlite3
from typing import Optional

from .chapter_dao import NovelChapterDAO as NovelChapterDAOClass
from .compaction_dao import CompactionIndexDAO
from .expert_dao import ExpertDAO
from .experience_dao import ExperienceDAO
from .feedback_dao import FeedbackDAO
from .link_dao import TaskMemoryLinkDAO
from .project_dao import NovelProjectDAO
from .skill_dao import SkillDAO

logger = logging.getLogger(__name__)


class Database:
    """
    数据库管理器

    统一管理所有 DAO 实例和数据库连接

    Example:
        >>> db = Database("/path/to/novel.db")
        >>> db.init_tables()
        >>> skill_dao = db.skill_dao
    """

    def __init__(self, db_path: str):
        """
        初始化数据库管理器

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # 初始化 DAO 实例
        self._init_daos()

        logger.info(f"[Database] 初始化数据库: {db_path}")

    def _init_daos(self) -> None:
        """初始化所有 DAO"""
        self.compaction_dao = CompactionIndexDAO(self.db_path)
        self.link_dao = TaskMemoryLinkDAO(self.db_path)
        self.skill_dao = SkillDAO(self.db_path)
        self.experience_dao = ExperienceDAO(self.db_path)
        self.feedback_dao = FeedbackDAO(self.db_path)
        self.expert_dao = ExpertDAO(self.db_path)
        self.project_dao = NovelProjectDAO(self.db_path)
        self.chapter_dao = NovelChapterDAOClass(self.db_path)

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # 启用外键约束
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def init_tables(self) -> None:
        """
        初始化所有表结构

        按依赖顺序创建表
        """
        logger.info("[Database] 开始初始化表结构...")

        # 按顺序初始化表
        daos = [
            ("compaction_index", self.compaction_dao),
            ("task_memory_link", self.link_dao),
            ("skills", self.skill_dao),
            ("experiences", self.experience_dao),
            ("feedback_records", self.feedback_dao),
            ("experts", self.expert_dao),
            ("novel_projects", self.project_dao),
            ("novel_chapters", self.chapter_dao),
        ]

        for table_name, dao in daos:
            try:
                dao.init_table()
                logger.debug(f"[Database] 表 {table_name} 初始化完成")
            except Exception as e:
                logger.error(f"[Database] 表 {table_name} 初始化失败: {e}")
                raise

        # 创建 FTS5 全文索引
        self._init_fts()

        logger.info("[Database] 所有表初始化完成")

    def _init_fts(self) -> None:
        """
        初始化全文索引

        FTS5 中文分词方案：
        1. 使用 porter 分词器包装 unicode61，支持词干提取
        2. 对于中文，使用 LIKE 查询作为补充

        注意：SQLite FTS5 的默认分词器对中文支持有限，
        因为中文没有空格分隔单词。最佳实践是使用：
        - simple 分词器：每个字符作为 token
        - 或者集成 jieba 等中文分词库

        当前方案：使用 simple 分词器，支持单个汉字匹配
        """
        conn = self.get_connection()

        # 检查 FTS 表是否已存在
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='compaction_fts'"
        )
        if cursor.fetchone():
            logger.debug("[Database] FTS5 表已存在，跳过创建")
            return

        # 创建 FTS5 表，使用 simple 分词器
        # simple 分词器会将连续的字母数字作为 token，其他字符单独处理
        # 对于中文，可以使用 trigram 或自定义分词
        conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS compaction_fts USING fts5(
            id UNINDEXED,
            summary,
            key_topics,
            key_entities,
            tokenize='porter unicode61'
        );
        """)

        # 触发器：插入时更新 FTS
        conn.execute("""
        CREATE TRIGGER IF NOT EXISTS compaction_ai AFTER INSERT ON compaction_index
        BEGIN
            INSERT INTO compaction_fts(rowid, id, summary, key_topics, key_entities)
            VALUES (new.rowid, new.id, new.summary, new.key_topics, new.key_entities);
        END;
        """)

        # 触发器：删除时更新 FTS
        conn.execute("""
        CREATE TRIGGER IF NOT EXISTS compaction_ad AFTER DELETE ON compaction_index
        BEGIN
            INSERT INTO compaction_fts(compaction_fts, rowid, id, summary, key_topics, key_entities)
            VALUES('delete', old.rowid, old.id, old.summary, old.key_topics, old.key_entities);
        END;
        """)

        # 触发器：更新时同步 FTS 索引
        # FTS5 不支持直接更新，需要先删除旧记录再插入新记录
        conn.execute("""
        CREATE TRIGGER IF NOT EXISTS compaction_au AFTER UPDATE ON compaction_index
        BEGIN
            INSERT INTO compaction_fts(compaction_fts, rowid, id, summary, key_topics, key_entities)
            VALUES('delete', old.rowid, old.id, old.summary, old.key_topics, old.key_entities);
            INSERT INTO compaction_fts(rowid, id, summary, key_topics, key_entities)
            VALUES (new.rowid, new.id, new.summary, new.key_topics, new.key_entities);
        END;
        """)

        conn.commit()
        logger.debug("[Database] FTS5 全文索引初始化完成（含 UPDATE 触发器）")

    def search_fts(self, query: str, limit: int = 20) -> list[dict]:
        """
        全文搜索压缩索引

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            匹配的记录列表
        """
        conn = self.get_connection()
        sql = """
        SELECT c.*
        FROM compaction_index c
        JOIN compaction_fts fts ON c.id = fts.id
        WHERE compaction_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """
        cursor = conn.execute(sql, (query, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("[Database] 数据库连接已关闭")

    def execute(
        self,
        sql: str,
        params: tuple = ()
    ) -> sqlite3.Cursor:
        """执行 SQL"""
        conn = self.get_connection()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor

    def begin_transaction(self) -> None:
        """开始事务"""
        self.get_connection().execute("BEGIN")

    def commit(self) -> None:
        """提交事务"""
        self.get_connection().commit()

    def rollback(self) -> None:
        """回滚事务"""
        self.get_connection().rollback()

    def get_stats(self) -> dict:
        """
        获取数据库统计

        Returns:
            各表记录数统计
        """
        conn = self.get_connection()
        stats = {}

        tables = [
            "compaction_index",
            "task_memory_link",
            "skills",
            "experiences",
            "feedback_records",
            "experts",
            "novel_projects",
            "novel_chapters"
        ]

        for table in tables:
            sql = f"SELECT COUNT(*) as count FROM {table}"
            cursor = conn.execute(sql)
            stats[table] = cursor.fetchone()["count"]

        stats["db_size_bytes"] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        return stats


# 全局数据库实例
_db_instance: Optional[Database] = None


def get_database(db_path: Optional[str] = None) -> Database:
    """
    获取全局数据库实例

    Args:
        db_path: 数据库路径，首次调用时必须提供

    Returns:
        Database 实例
    """
    global _db_instance

    if _db_instance is None:
        if db_path is None:
            # 默认路径
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                ".deer-flow",
                "novel-data",
                "memory",
                "novel.db"
            )
        _db_instance = Database(db_path)

    return _db_instance


def reset_database() -> None:
    """重置全局数据库实例（用于测试）"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None
