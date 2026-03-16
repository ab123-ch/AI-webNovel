"""数据访问层模块

提供统一的数据库访问接口
"""

from __future__ import annotations

from .base import BaseDAO
from .chapter_dao import NovelChapter, NovelChapterDAO
from .compaction_dao import CompactionIndex, CompactionIndexDAO
from .experience_dao import Experience, ExperienceDAO
from .expert_dao import Expert, ExpertDAO
from .feedback_dao import FeedbackRecord, FeedbackDAO
from .link_dao import TaskMemoryLink, TaskMemoryLinkDAO
from .project_dao import NovelProject, NovelProjectDAO
from .skill_dao import Skill, SkillDAO

__all__ = [
    # 基类
    "BaseDAO",
    # 模型和 DAO
    "CompactionIndex",
    "CompactionIndexDAO",
    "TaskMemoryLink",
    "TaskMemoryLinkDAO",
    "Skill",
    "SkillDAO",
    "Experience",
    "ExperienceDAO",
    "FeedbackRecord",
    "FeedbackDAO",
    "Expert",
    "ExpertDAO",
    "NovelProject",
    "NovelProjectDAO",
    "NovelChapter",
    "NovelChapterDAO",
]
