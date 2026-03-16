"""索引管理器

管理压缩索引的创建、查询、搜索和删除
"""

import logging
from typing import Optional

from ..dal import CompactionIndex, CompactionIndexDAO

logger = logging.getLogger(__name__)


class IndexManager:
    """
    索引管理器

    职责：
    - 创建索引
    - 获取索引
    - 全文搜索
    - 删除索引
    - 会话索引管理
    - 层级索引管理

    Example:
        >>> manager = IndexManager(compaction_dao)
        >>> index = manager.create_index(...)
        >>> results = manager.search_fts("修仙")
    """

    def __init__(
        self,
        compaction_dao: CompactionIndexDAO
    ):
        """
        初始化索引管理器

        Args:
            compaction_dao: 压缩索引 DAO
        """
        self.dao = compaction_dao

    def create_index(
        self,
        index: CompactionIndex
    ) -> CompactionIndex:
        """
        创建索引

        Args:
            index: 压缩索引模型

        Returns:
            创建后的索引

        Example:
            >>> index = CompactionIndex(
            ...     id="idx-001",
            ...     session_id="sess-001",
            ...     layer=1,
            ...     summary="讨论了修仙小说的设定",
            ...     ...
            ... )
            >>> manager.create_index(index)
        """
        return self.dao.create(index)

    def get_index(
        self,
        compaction_id: str
    ) -> Optional[CompactionIndex]:
        """
        获取索引

        Args:
            compaction_id: 压缩索引 ID

        Returns:
            压缩索引或 None

        Example:
            >>> index = manager.get_index("idx-001")
            >>> if index:
            ...     print(index.summary)
        """
        return self.dao.get_by_id(compaction_id)

    def search_fts(
        self,
        query: str,
        limit: int = 20
    ) -> list[CompactionIndex]:
        """
        全文搜索

        使用 FTS5 进行高效的全文搜索

        Args:
            query: 搜索查询
            limit: 返回数量限制

        Returns:
            匹配的索引列表

        Example:
            >>> results = manager.search_fts("修仙 境界", limit=10)
            >>> for idx in results:
            ...     print(f"{idx.summary} (score={idx.compression_ratio:.2%})")
        """
        # 直接使用 DAO 层的 FTS5 搜索方法
        return self.dao.search_fts(query, limit)

    def delete_index(
        self,
        compaction_id: str
    ) -> bool:
        """
        删除索引

        Args:
            compaction_id: 压缩索引 ID

        Returns:
            是否删除成功

        Example:
            >>> if manager.delete_index("idx-001"):
            ...     print("删除成功")
        """
        return self.dao.delete(compaction_id)

    def get_session_indexes(
        self,
        session_id: str
    ) -> list[CompactionIndex]:
        """
        获取会话的所有索引

        Args:
            session_id: 会话 ID

        Returns:
            索引列表，按创建时间倒序

        Example:
            >>> indexes = manager.get_session_indexes("sess-001")
            >>> print(f"会话有 {len(indexes)} 个压缩索引")
        """
        return self.dao.get_by_session(session_id)

    def get_layer_indexes(
        self,
        layer: int,
        limit: int = 100
    ) -> list[CompactionIndex]:
        """
        获取指定层级的索引

        Args:
            layer: 压缩层级 (1-3)
            limit: 返回数量限制

        Returns:
            索引列表

        Example:
            >>> layer1_indexes = manager.get_layer_indexes(1)
            >>> print(f"Layer 1 有 {len(layer1_indexes)} 个索引")
        """
        if not 1 <= layer <= 3:
            logger.warning(f"[IndexManager] 无效的层级: {layer}")
            return []

        return self.dao.get_by_layer(layer, limit)

    def get_index_stats(
        self,
        session_id: Optional[str] = None
    ) -> dict:
        """
        获取索引统计

        Args:
            session_id: 可选的会话 ID 过滤

        Returns:
            {
                "total": 总索引数,
                "by_layer": {1: count, 2: count, 3: count},
                "avg_compression_ratio": 平均压缩比
            }

        Example:
            >>> stats = manager.get_index_stats()
            >>> print(f"平均压缩比: {stats['avg_compression_ratio']:.2%}")
        """
        indexes = self.dao.get_by_session(session_id) if session_id else self.dao.list()

        if not indexes:
            return {
                "total": 0,
                "by_layer": {1: 0, 2: 0, 3: 0},
                "avg_compression_ratio": 0.0
            }

        by_layer = {1: 0, 2: 0, 3: 0}
        total_ratio = 0.0

        for idx in indexes:
            if 1 <= idx.layer <= 3:
                by_layer[idx.layer] += 1
            total_ratio += idx.compression_ratio

        return {
            "total": len(indexes),
            "by_layer": by_layer,
            "avg_compression_ratio": total_ratio / len(indexes) if indexes else 0.0
        }

    def cleanup_old_indexes(
        self,
        max_age_days: int = 90,
        keep_layers: list[int] = None
    ) -> int:
        """
        清理过期索引

        Args:
            max_age_days: 最大保留天数
            keep_layers: 需要保留的层级列表

        Returns:
            删除的索引数量

        Example:
            >>> deleted = manager.cleanup_old_indexes(max_age_days=30)
            >>> print(f"清理了 {deleted} 个过期索引")
        """
        import time

        keep_layers = keep_layers or [2, 3]  # 默认保留高层索引
        cutoff_time = int(time.time()) - max_age_days * 86400

        all_indexes = self.dao.list()
        deleted_count = 0

        for idx in all_indexes:
            # 跳过需要保留的层级
            if idx.layer in keep_layers:
                continue

            # 检查是否过期
            if idx.created_at < cutoff_time:
                if self.dao.delete(idx.id):
                    deleted_count += 1

        logger.info(
            f"[IndexManager] 清理过期索引: max_age={max_age_days}天, "
            f"deleted={deleted_count}"
        )

        return deleted_count
