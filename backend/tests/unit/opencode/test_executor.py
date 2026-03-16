"""OpenCode 模块单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

# 测试导入是否正常
def test_import_opencode_config():
    """测试 OpenCodeConfig 导入"""
    from src.opencode.config import OpenCodeConfig
    config = OpenCodeConfig()
    assert config.model == "glm-4.7"
    assert config.timeout == 300
    assert config.max_retries == 3


def test_import_opencode_executor():
    """测试 OpenCodeExecutor 导入"""
    from src.opencode.executor import OpenCodeExecutor, OpenCodeError
    assert OpenCodeExecutor is not None
    assert OpenCodeError is not None


def test_import_opencode_tasks():
    """测试 OpenCodeTasks 导入"""
    from src.opencode.tasks import OpenCodeTasks
    assert OpenCodeTasks is not None


def test_import_opencode_pool():
    """测试 OpenCodePool 导入"""
    from src.opencode.pool import OpenCodePool
    assert OpenCodePool is not None


def test_opencode_config_defaults():
    """测试默认配置"""
    from src.opencode.config import OpenCodeConfig

    config = OpenCodeConfig()
    assert config.model == "glm-4.7"
    assert config.timeout == 300
    assert config.max_retries == 3
    assert "glm-4.5" in config.models
    assert "glm-5" in config.models
    assert config.compaction_threshold == 10
    assert config.warning_tokens == 60000


def test_opencode_config_custom():
    """测试自定义配置"""
    from src.opencode.config import OpenCodeConfig

    config = OpenCodeConfig(
        model="glm-5",
        timeout=600,
        max_retries=5,
        compaction_threshold=20
    )
    assert config.model == "glm-5"
    assert config.timeout == 600
    assert config.max_retries == 5
    assert config.compaction_threshold == 20


class TestOpenCodeExecutor:
    """OpenCodeExecutor 测试"""

    def test_init(self):
        """测试初始化"""
        from src.opencode.executor import OpenCodeExecutor
        from src.opencode.config import OpenCodeConfig

        config = OpenCodeConfig(model="glm-4.6")
        executor = OpenCodeExecutor(config)
        assert executor.cfg.model == "glm-4.6"

    def test_init_default(self):
        """测试默认初始化"""
        from src.opencode.executor import OpenCodeExecutor

        executor = OpenCodeExecutor()
        assert executor.cfg.model == "glm-4.7"

    def test_build_prompt_simple(self):
        """测试简单提示词构建"""
        from src.opencode.executor import OpenCodeExecutor

        executor = OpenCodeExecutor()
        prompt = executor._build_prompt("测试任务")
        assert prompt == "测试任务"

    def test_build_prompt_with_context(self):
        """测试带上下文的提示词构建"""
        from src.opencode.executor import OpenCodeExecutor

        executor = OpenCodeExecutor()
        prompt = executor._build_prompt("测试任务", "这是上下文")
        assert "上下文" in prompt
        assert "测试任务" in prompt

    def test_set_model(self):
        """测试模型切换"""
        from src.opencode.executor import OpenCodeExecutor

        executor = OpenCodeExecutor()
        executor.set_model("glm-5")
        assert executor.cfg.model == "glm-5"

    def test_set_model_invalid(self):
        """测试无效模型切换"""
        from src.opencode.executor import OpenCodeExecutor

        executor = OpenCodeExecutor()
        with pytest.raises(ValueError):
            executor.set_model("invalid-model")

    @pytest.mark.asyncio
    async def test_execute_empty_task(self):
        """测试空任务执行"""
        from src.opencode.executor import OpenCodeExecutor

        executor = OpenCodeExecutor()
        with pytest.raises(ValueError, match="task cannot be empty"):
            await executor.execute("")


class TestOpenCodeTasks:
    """OpenCodeTasks 测试"""

    @pytest.fixture
    def mock_executor(self):
        """模拟执行器"""
        from src.opencode.executor import OpenCodeExecutor
        mock = MagicMock(spec=OpenCodeExecutor)
        mock.execute = AsyncMock(return_value='{"summary": "测试摘要"}')
        return mock

    def test_init(self, mock_executor):
        """测试初始化"""
        from src.opencode.tasks import OpenCodeTasks

        tasks = OpenCodeTasks(mock_executor)
        assert tasks.exe == mock_executor

    def test_extract_json(self, mock_executor):
        """测试 JSON 提取"""
        from src.opencode.tasks import OpenCodeTasks

        tasks = OpenCodeTasks(mock_executor)

        # 直接 JSON
        assert tasks._extract_json('{"key": "value"}') == '{"key": "value"}'

        # 代码块中的 JSON
        text = '```json\n{"key": "value"}\n```'
        assert tasks._extract_json(text) == '{"key": "value"}'


class TestOpenCodePool:
    """OpenCodePool 测试"""

    def test_singleton(self):
        """测试单例模式"""
        from src.opencode.pool import OpenCodePool
        OpenCodePool.reset()  # 重置单例

        pool1 = OpenCodePool()
        pool2 = OpenCodePool()
        assert pool1 is pool2

        OpenCodePool.reset()

    def test_get_executor(self):
        """测试获取执行器"""
        from src.opencode.pool import OpenCodePool
        OpenCodePool.reset()

        pool = OpenCodePool()
        executor = pool.get_executor("glm-4.7")
        assert executor is not None
        assert executor.cfg.model == "glm-4.7"

        OpenCodePool.reset()

    def test_list_models(self):
        """测试列出模型"""
        from src.opencode.pool import OpenCodePool
        OpenCodePool.reset()

        pool = OpenCodePool()
        pool.get_executor("glm-4.7")
        pool.get_executor("glm-5")

        models = pool.list_models()
        assert "glm-4.7" in models
        assert "glm-5" in models

        OpenCodePool.reset()
