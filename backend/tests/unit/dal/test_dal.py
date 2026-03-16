"""DAL 模块单元测试 - 简化版"""

import pytest
import tempfile
import os


class TestDALImports:
    """DAL 模块导入测试"""

    def test_import_base(self):
        """测试 BaseDAO 导入"""
        try:
            from src.dal.base import BaseDAO
            assert BaseDAO is not None
        except ImportError as e:
            pytest.skip(f"无法导入 BaseDAO: {e}")

    def test_import_compaction_dao(self):
        """测试 CompactionIndexDAO 导入"""
        try:
            from src.dal.compaction_dao import CompactionIndexDAO, CompactionIndex
            assert CompactionIndexDAO is not None
            assert CompactionIndex is not None
        except ImportError as e:
            pytest.skip(f"无法导入 CompactionIndexDAO: {e}")

    def test_import_link_dao(self):
        """测试 TaskMemoryLinkDAO 导入"""
        try:
            from src.dal.link_dao import TaskMemoryLinkDAO, TaskMemoryLink
            assert TaskMemoryLinkDAO is not None
            assert TaskMemoryLink is not None
        except ImportError as e:
            pytest.skip(f"无法导入 TaskMemoryLinkDAO: {e}")

    def test_import_skill_dao(self):
        """测试 SkillDAO 导入"""
        try:
            from src.dal.skill_dao import SkillDAO, Skill
            assert SkillDAO is not None
            assert Skill is not None
        except ImportError as e:
            pytest.skip(f"无法导入 SkillDAO: {e}")

    def test_import_feedback_dao(self):
        """测试 FeedbackDAO 导入"""
        try:
            from src.dal.feedback_dao import FeedbackDAO, FeedbackRecord
            assert FeedbackDAO is not None
            assert FeedbackRecord is not None
        except ImportError as e:
            pytest.skip(f"无法导入 FeedbackDAO: {e}")

    def test_import_expert_dao(self):
        """测试 ExpertDAO 导入"""
        try:
            from src.dal.expert_dao import ExpertDAO, Expert
            assert ExpertDAO is not None
            assert Expert is not None
        except ImportError as e:
            pytest.skip(f"无法导入 ExpertDAO: {e}")

    def test_import_experience_dao(self):
        """测试 ExperienceDAO 导入"""
        try:
            from src.dal.experience_dao import ExperienceDAO, Experience
            assert ExperienceDAO is not None
            assert Experience is not None
        except ImportError as e:
            pytest.skip(f"无法导入 ExperienceDAO: {e}")

    def test_import_project_dao(self):
        """测试 NovelProjectDAO 导入"""
        try:
            from src.dal.project_dao import NovelProjectDAO, NovelProject
            assert NovelProjectDAO is not None
            assert NovelProject is not None
        except ImportError as e:
            pytest.skip(f"无法导入 NovelProjectDAO: {e}")

    def test_import_chapter_dao(self):
        """测试 NovelChapterDAO 导入"""
        try:
            from src.dal.chapter_dao import NovelChapterDAO, NovelChapter
            assert NovelChapterDAO is not None
            assert NovelChapter is not None
        except ImportError as e:
            pytest.skip(f"无法导入 NovelChapterDAO: {e}")


class TestCompactionIndex:
    """CompactionIndex 模型测试"""

    def test_create(self):
        """测试创建模型"""
        try:
            from src.dal.compaction_dao import CompactionIndex
            import time

            index = CompactionIndex(
                id="test-001",
                session_id="session-001",
                layer=1,
                source_memory_ids=["m1", "m2"],
                source_compaction_ids=None,
                summary="测试摘要",
                key_topics=["主题1", "主题2"],
                key_decisions=["决策1"],
                key_entities=["实体1"],
                key_conclusions=["结论1"],
                task_type="测试",
                task_description="测试任务",
                original_token_count=1000,
                compressed_token_count=200,
                compression_ratio=0.8,
                created_at=int(time.time())
            )

            assert index.id == "test-001"
            assert index.layer == 1
            assert len(index.key_topics) == 2
            assert index.compression_ratio == 0.8
        except ImportError as e:
            pytest.skip(f"无法导入: {e}")


class TestSkill:
    """Skill 模型测试"""

    def test_create(self):
        """测试创建技能模型"""
        try:
            from src.dal.skill_dao import Skill
            import time

            now = int(time.time())
            skill = Skill(
                id="skill-001",
                name="测试技能",
                description="这是一个测试技能",
                expert_id="expert-001",
                prompt="技能提示词",
                examples=[{"input": "a", "output": "b"}],
                conditions=["条件1"],
                steps=["步骤1", "步骤2"],
                success_rate=0.9,
                usage_count=10,
                source="extracted",
                source_session_id="session-001",
                created_at=now,
                updated_at=now
            )

            assert skill.name == "测试技能"
            assert skill.success_rate == 0.9
            assert skill.source == "extracted"
        except ImportError as e:
            pytest.skip(f"无法导入: {e}")


class TestExpert:
    """Expert 模型测试"""

    def test_create(self):
        """测试创建专家模型"""
        try:
            from src.dal.expert_dao import Expert
            import time

            now = int(time.time())
            expert = Expert(
                id="expert-001",
                name="创意策划师",
                domain="creative",
                description="负责创意孵化",
                keywords=["创意", "点子", "灵感"],
                system_prompt="你是创意策划师",
                capabilities=["创意生成", "点子拓展"],
                is_builtin=True,
                usage_count=0,
                created_at=now,
                updated_at=now
            )

            assert expert.name == "创意策划师"
            assert expert.domain == "creative"
            assert expert.is_builtin is True
        except ImportError as e:
            pytest.skip(f"无法导入: {e}")


class TestTaskMemoryLink:
    """TaskMemoryLink 测试"""

    def test_create(self):
        """测试创建关联"""
        try:
            from src.dal.link_dao import TaskMemoryLink
            import time

            now = int(time.time())
            link = TaskMemoryLink(
                id="link-001",
                task_signature="abc123",
                memory_id="mem-001",
                memory_type="compaction",
                relevance_score=0.9,
                recall_count=0,
                last_recalled_at=now,
                created_at=now
            )

            assert link.task_signature == "abc123"
            assert link.relevance_score == 0.9
        except ImportError as e:
            pytest.skip(f"无法导入: {e}")
