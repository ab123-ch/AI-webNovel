"""Memory 模块单元测试 - 简化版"""

import pytest
from unittest.mock import MagicMock, AsyncMock
import tempfile
import os


# 测试导入
def test_import_memory_compaction():
    """测试 MemoryCompaction 导入"""
    from src.memory.compaction import MemoryCompaction
    assert MemoryCompaction is not None


def test_import_memory_review():
    """测试 MemoryReview 导入"""
    from src.memory.review import MemoryReview
    assert MemoryReview is not None


def test_import_index_manager():
    """测试 IndexManager 导入"""
    from src.memory.index_manager import IndexManager
    assert IndexManager is not None


def test_import_task_memory_linker():
    """测试 TaskMemoryLinker 导入"""
    from src.memory.linker import TaskMemoryLinker
    assert TaskMemoryLinker is not None


class TestMemoryCompaction:
    """MemoryCompaction 测试"""

    def test_check_compaction_needed(self):
        """测试压缩检查"""
        from src.memory.compaction import MemoryCompaction

        # 模拟依赖
        mock_tasks = MagicMock()
        mock_compaction_dao = MagicMock()
        mock_link_dao = MagicMock()

        service = MemoryCompaction(
            opencode_tasks=mock_tasks,
            compaction_dao=mock_compaction_dao,
            link_dao=mock_link_dao
        )

        # 需要压缩
        assert service.check_compaction_needed("sess-1", 70000, 60000) is True
        # 不需要压缩
        assert service.check_compaction_needed("sess-1", 50000, 60000) is False

    def test_estimate_tokens(self):
        """测试 token 估算"""
        from src.memory.compaction import MemoryCompaction

        mock_tasks = MagicMock()
        mock_compaction_dao = MagicMock()
        mock_link_dao = MagicMock()

        service = MemoryCompaction(
            opencode_tasks=mock_tasks,
            compaction_dao=mock_compaction_dao,
            link_dao=mock_link_dao
        )

        messages = [
            {"content": "这是测试内容"},
            {"content": "Another test"}
        ]
        tokens = service._estimate_tokens(messages)
        assert tokens > 0

    @pytest.mark.asyncio
    async def test_compact_layer1(self):
        """测试 Layer 1 压缩"""
        from src.memory.compaction import MemoryCompaction
        import time

        mock_tasks = MagicMock()
        mock_tasks.compact_memories = AsyncMock(return_value={
            "summary": "测试摘要",
            "key_topics": ["主题1"],
            "key_decisions": [],
            "key_entities": [],
            "key_conclusions": [],
            "task_type": "test",
            "task_description": "测试任务"
        })
        mock_compaction_dao = MagicMock()
        mock_compaction_dao.create = MagicMock()

        service = MemoryCompaction(
            opencode_tasks=mock_tasks,
            compaction_dao=mock_compaction_dao,
            link_dao=MagicMock()
        )

        messages = [
            {"role": "user", "content": "帮我写小说"},
            {"role": "assistant", "content": "好的，请告诉我更多"}
        ]

        index = await service.compact_layer1("sess-001", messages)

        assert index.session_id == "sess-001"
        assert index.layer == 1
        assert index.summary == "测试摘要"

    def test_get_trace_path(self):
        """测试追溯路径"""
        from src.memory.compaction import MemoryCompaction

        mock_tasks = MagicMock()
        mock_compaction_dao = MagicMock()
        mock_compaction_dao.get_source_ids = MagicMock(return_value={
            "memory_ids": ["m1", "m2"],
            "compaction_ids": []
        })
        mock_link_dao = MagicMock()

        service = MemoryCompaction(
            opencode_tasks=mock_tasks,
            compaction_dao=mock_compaction_dao,
            link_dao=mock_link_dao
        )

        path = service.get_trace_path("idx-001")
        assert "idx-001" in path


class TestMemoryReview:
    """MemoryReview 测试"""

    def test_calculate_keyword_score(self):
        """测试关键词匹配分数计算"""
        from src.memory.review import MemoryReview
        from src.dal.compaction_dao import CompactionIndex
        import time

        mock_tasks = MagicMock()
        mock_compaction_dao = MagicMock()
        mock_link_dao = MagicMock()

        service = MemoryReview(
            opencode_tasks=mock_tasks,
            compaction_dao=mock_compaction_dao,
            link_dao=mock_link_dao
        )

        index = CompactionIndex(
            id="test",
            session_id="sess",
            layer=1,
            source_memory_ids=[],
            source_compaction_ids=None,
            summary="这是关于修仙小说的讨论",
            key_topics=["修仙", "境界"],
            key_entities=["主角"],
            key_decisions=[],
            key_conclusions=[],
            original_token_count=100,
            compressed_token_count=20,
            compression_ratio=0.8,
            created_at=int(time.time())
        )

        score = service._calculate_keyword_score(index, ["修仙", "境界"])
        assert score > 0

        score = service._calculate_keyword_score(index, ["无关词"])
        assert score == 0

    @pytest.mark.asyncio
    async def test_review_by_keywords(self):
        """测试关键词检索"""
        from src.memory.review import MemoryReview

        mock_tasks = MagicMock()
        mock_compaction_dao = MagicMock()
        mock_compaction_dao.list = MagicMock(return_value=[])
        mock_link_dao = MagicMock()

        service = MemoryReview(
            opencode_tasks=mock_tasks,
            compaction_dao=mock_compaction_dao,
            link_dao=mock_link_dao
        )

        results = await service.review_by_keywords(["测试"])
        assert isinstance(results, list)


class TestIndexManager:
    """IndexManager 测试"""

    def test_search_fts_empty(self):
        """测试空搜索"""
        from src.memory.index_manager import IndexManager

        mock_dao = MagicMock()
        # 新实现直接调用 dao.search_fts()
        mock_dao.search_fts = MagicMock(return_value=[])

        manager = IndexManager(mock_dao)
        results = manager.search_fts("测试")
        assert results == []
        # 验证调用了正确的 DAO 方法
        mock_dao.search_fts.assert_called_once_with("测试", 20)

    def test_search_fts_with_results(self):
        """测试有结果的搜索"""
        from src.memory.index_manager import IndexManager
        from src.dal.compaction_dao import CompactionIndex

        mock_dao = MagicMock()
        mock_index = CompactionIndex(
            id="idx-001",
            session_id="sess-001",
            layer=1,
            source_memory_ids=["m1", "m2"],
            summary="测试摘要",
            key_topics=["测试"],
            key_decisions=[],
            key_entities=[],
            key_conclusions=[],
            original_token_count=100,
            compressed_token_count=50,
            compression_ratio=0.5,
            created_at=1234567890
        )
        mock_dao.search_fts = MagicMock(return_value=[mock_index])

        manager = IndexManager(mock_dao)
        results = manager.search_fts("测试", limit=10)

        assert len(results) == 1
        assert results[0].id == "idx-001"
        mock_dao.search_fts.assert_called_once_with("测试", 10)


class TestTaskMemoryLinker:
    """TaskMemoryLinker 测试"""

    def test_calculate_signature(self):
        """测试任务签名计算"""
        from src.memory.linker import TaskMemoryLinker

        mock_dao = MagicMock()
        service = TaskMemoryLinker(mock_dao)

        sig1 = service.calculate_signature("写章节", ["修仙", "突破"])
        sig2 = service.calculate_signature("写章节", ["修仙", "突破"])
        sig3 = service.calculate_signature("写章节", ["其他", "关键词"])

        assert sig1 == sig2  # 相同输入产生相同签名
        assert sig1 != sig3  # 不同输入产生不同签名

    def test_create_link(self):
        """测试创建关联"""
        from src.memory.linker import TaskMemoryLinker
        from src.dal.link_dao import TaskMemoryLink
        import time

        now = int(time.time())
        created_link = TaskMemoryLink(
            id="link-001",
            task_signature="abc123",
            memory_id="mem-001",
            memory_type="compaction",
            relevance_score=0.9,
            recall_count=0,
            last_recalled_at=now,
            created_at=now
        )

        mock_dao = MagicMock()
        mock_dao.create = MagicMock(return_value=created_link)

        service = TaskMemoryLinker(mock_dao)
        link = service.create_link(
            task_signature="abc123",
            memory_id="mem-001",
            memory_type="compaction",
            relevance=0.9
        )

        assert link.task_signature == "abc123"
        assert link.memory_id == "mem-001"

    def test_simplify_task(self):
        """测试任务简化"""
        from src.memory.linker import TaskMemoryLinker

        mock_dao = MagicMock()
        service = TaskMemoryLinker(mock_dao)

        simple = service._simplify_task("帮我写一下修仙小说的章节")
        assert "帮我" not in simple
        assert "一下" not in simple

    def test_get_link_stats(self):
        """测试关联统计"""
        from src.memory.linker import TaskMemoryLinker

        mock_dao = MagicMock()
        mock_dao.list = MagicMock(return_value=[])

        service = TaskMemoryLinker(mock_dao)
        stats = service.get_link_stats()

        assert "total" in stats
        assert "avg_relevance" in stats
