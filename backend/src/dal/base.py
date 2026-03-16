from __future__ import annotations
"""数据访问层基类

提供通用的 CRUD 操作抽象
"""

import logging
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseDAO(ABC, Generic[T]):
    """
    数据访问对象基类

    提供通用的 CRUD 操作模板

    Type Parameters:
        T: Pydantic 模型类型

    Example:
        >>> class UserDAO(BaseDAO[User]):
        ...     @property
        ...     def table_name(self) -> str:
        ...         return "users"
    """

    def __init__(self, db_path: str):
        """
        初始化 DAO

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    @abstractmethod
    def table_name(self) -> str:
        """表名"""
        pass

    @property
    @abstractmethod
    def create_sql(self) -> str:
        """创建表的 SQL 语句"""
        pass

    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接

        启用 WAL 模式和适当的超时配置以提高并发性能

        Returns:
            SQLite 连接对象
        """
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 增加超时，避免并发锁等待
                check_same_thread=False,  # 允许跨线程（配合锁使用）
                cached_statements=100  # 缓存语句数量
            )
            self._conn.row_factory = sqlite3.Row
            # 启用 WAL 模式提高并发读写性能
            self._conn.execute("PRAGMA journal_mode=WAL")
            # 设置繁忙超时（毫秒）
            self._conn.execute("PRAGMA busy_timeout=30000")
            # 启用外键约束
            self._conn.execute("PRAGMA foreign_keys = ON")
            logger.debug(f"[{self.table_name}] 数据库连接已建立 | WAL模式 | busy_timeout=30000ms")
        return self._conn

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def init_table(self) -> None:
        """
        初始化表结构

        执行 create_sql 创建表
        """
        conn = self.get_connection()
        conn.execute(self.create_sql)
        conn.commit()
        logger.info(f"[{self.table_name}] 表初始化完成")

    @abstractmethod
    def create(self, model: T) -> T:
        """
        创建记录

        Args:
            model: Pydantic 模型实例

        Returns:
            创建后的模型（包含生成的 ID 等）
        """
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """
        按 ID 获取记录

        Args:
            id: 记录 ID

        Returns:
            模型实例或 None
        """
        pass

    @abstractmethod
    def update(self, model: T) -> T:
        """
        更新记录

        Args:
            model: 包含更新数据的模型

        Returns:
            更新后的模型
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        删除记录

        Args:
            id: 记录 ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[T]:
        """
        列出记录

        Args:
            filters: 过滤条件
            order_by: 排序字段
            limit: 限制数量
            offset: 偏移量

        Returns:
            模型列表
        """
        pass

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """
        将数据库行转换为字典

        Args:
            row: SQLite Row 对象

        Returns:
            字典
        """
        return dict(row)

    def execute(
        self,
        sql: str,
        params: tuple = ()
    ) -> sqlite3.Cursor:
        """
        执行 SQL 语句

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            游标对象
        """
        conn = self.get_connection()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor

    def execute_script(self, script: str) -> None:
        """
        执行 SQL 脚本

        Args:
            script: SQL 脚本
        """
        conn = self.get_connection()
        conn.executescript(script)
        conn.commit()
