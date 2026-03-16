# DeerFlow Novel 开发说明文档

> 版本: 1.0.0
> 日期: 2026-03-16
> 适用范围: 所有参与 DeerFlow Novel 开发的 AI Agent 和开发者

---

## 一、开发约束

### 1.1 代码规范

#### 1.1.1 命名规范（强制）

```python
# ✅ 正确：单次命名，简洁明了
pid, cfg, err, opts, dir, root, state

# ❌ 错误：冗余的多词命名
inputPID, existingClient, connectTimeout

# ✅ 类名使用 PascalCase
class OpenCodeExecutor:
    pass

# ✅ 函数/方法名使用 snake_case
def compact_memories(self, messages: list) -> dict:
    pass

# ✅ 常量使用 UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 300

# ✅ 私有方法使用下划线前缀
def _build_prompt(self, task: str) -> str:
    pass
```

#### 1.1.2 类型注解（强制）

```python
# ✅ 所有公共方法必须有类型注解
async def execute(
    self,
    task: str,
    context: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    pass

# ✅ 使用 Pydantic 模型定义数据结构
class CompactionIndex(BaseModel):
    id: str
    session_id: str
    layer: int

# ❌ 禁止使用 any 类型
def process(data: any):  # 错误！
    pass
```

#### 1.1.3 文档字符串（强制）

```python
async def compact_memories(self, messages: list[dict], layer: int = 1) -> dict:
    """
    记忆压缩任务

    Args:
        messages: 消息列表，每条消息包含 role 和 content
        layer: 压缩层级，1-3

    Returns:
        压缩结果字典，包含 summary, key_topics 等字段

    Raises:
        OpenCodeError: OpenCode 执行失败时抛出

    Example:
        >>> result = await compact_memories([{"role": "user", "content": "..."}])
        >>> print(result["summary"])
    """
    pass
```

### 1.2 设计模式（强制应用）

#### 1.2.1 必须使用的设计模式

| 模式 | 应用场景 | 示例 |
|------|----------|------|
| **工厂模式** | 创建复杂对象 | `OpenCodePool.get_executor()` |
| **策略模式** | 可互换的算法 | 不同压缩策略 |
| **观察者模式** | 事件通知 | 守护进程状态变化 |
| **单例模式** | 全局唯一实例 | `ExpertRegistry`, `DaemonService` |
| **装饰器模式** | 功能增强 | 日志、缓存、重试 |
| **依赖注入** | 解耦组件依赖 | 构造函数注入 |

#### 1.2.2 设计模式示例

```python
# 工厂模式 - 执行器工厂
class OpenCodePool:
    _executors: dict[str, OpenCodeExecutor] = {}

    def get_executor(self, model: Optional[str] = None) -> OpenCodeExecutor:
        model = model or self.config.model
        if model not in self._executors:
            self._executors[model] = OpenCodeExecutor(
                OpenCodeConfig(model=model)
            )
        return self._executors[model]


# 策略模式 - 压缩策略
class CompactionStrategy(Protocol):
    def compact(self, messages: list[dict]) -> dict:
        ...

class Layer1Strategy(CompactionStrategy):
    def compact(self, messages: list[dict]) -> dict:
        # Layer 1 压缩逻辑
        pass

class Layer2Strategy(CompactionStrategy):
    def compact(self, messages: list[dict]) -> dict:
        # Layer 2 压缩逻辑
        pass


# 依赖注入 - 构造函数注入
class MemoryCompaction:
    def __init__(
        self,
        opencode_tasks: OpenCodeTasks,
        db: Database,
        strategy: CompactionStrategy
    ):
        self.opencode_tasks = opencode_tasks
        self.db = db
        self.strategy = strategy


# 装饰器模式 - 重试装饰器
def with_retry(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator
```

### 1.3 代码质量检查（强制）

#### 1.3.1 静态检查工具

```bash
# 必须通过的检查
# 1. 类型检查
mypy backend/src --strict

# 2. 代码风格
ruff check backend/src

# 3. 格式化
ruff format backend/src --check

# 4. 安全检查
bandit -r backend/src
```

#### 1.3.2 检查配置

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
```

### 1.4 错误处理规范

```python
# ✅ 自定义异常层次
class NovelSystemError(Exception):
    """系统基础异常"""
    pass

class OpenCodeError(NovelSystemError):
    """OpenCode 执行错误"""
    pass

class MemoryError(NovelSystemError):
    """记忆系统错误"""
    pass

class CompactionError(MemoryError):
    """压缩错误"""
    pass


# ✅ 使用上下文管理器
@contextmanager
def database_transaction(db: Database):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


# ✅ 避免 bare except
# ❌ 错误
try:
    do_something()
except:
    pass

# ✅ 正确
try:
    do_something()
except (ValueError, TypeError) as e:
    logger.error(f"处理失败: {e}")
    raise
```

---

## 二、需求理解步骤（强制流程）

### 2.1 任务分析流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     需求理解流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 阅读任务描述                                           │
│     ↓                                                           │
│  Step 2: 查找相关文档                                           │
│     ├── 查阅 deerflow-novel-系统架构设计.md                     │
│     ├── 查阅 deerflow-novel-需求实现清单.md                     │
│     └── 查阅 deerflow-novel-开发任务清单.md                     │
│     ↓                                                           │
│  Step 3: 关联分析 (填写关联分析表)                              │
│     ↓                                                           │
│  Step 4: 影响评估 (填写影响评估表)                              │
│     ↓                                                           │
│  Step 5: 设计方案 (输出设计文档)                                │
│     ↓                                                           │
│  Step 6: 代码实现                                               │
│     ↓                                                           │
│  Step 7: 测试验证                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 关联分析表（开发前必须填写）

```markdown
## 任务关联分析表

**任务ID**: P1-OC-005
**任务描述**: 实现 `OpenCodeExecutor.execute` 基础执行方法

### 依赖关系

| 类型 | 模块/类/方法 | 依赖描述 |
|------|--------------|----------|
| 前置依赖 | OpenCodeConfig | 需要配置对象初始化 |
| 前置依赖 | _build_prompt | 需要提示词构建方法 |
| 调用方 | OpenCodeTasks | 本方法会被 OpenCodeTasks 调用 |
| 调用方 | MemoryCompaction | 间接通过 OpenCodeTasks 调用 |

### 数据流

```
OpenCodeTasks.compact_memories()
    → OpenCodeExecutor.execute()
        → _build_prompt()
        → _run_subprocess()
        → 返回结果
```

### 接口契约

```python
# 输入
task: str           # 任务描述，非空
context: str | None # 上下文，可选
model: str | None   # 模型名称，可选，默认使用配置

# 输出
str                 # 执行结果，非空

# 异常
OpenCodeError       # 执行失败
TimeoutError        # 超时
```
```

### 2.3 影响评估表（开发前必须填写）

```markdown
## 影响评估表

**任务ID**: P2-MEM-010
**任务描述**: 实现 `compact_layer1` Layer 1 压缩

### 影响范围

| 影响项 | 影响程度 | 说明 | 需要修改 |
|--------|----------|------|----------|
| MemoryCompaction | 高 | 新增核心方法 | 是 |
| OpenCodeTasks | 低 | 调用已存在的方法 | 否 |
| 数据库 | 中 | 需要新增 compaction_index 表 | 是 |
| 配置文件 | 低 | 使用已有配置 | 否 |

### 兼容性检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 是否影响现有 API | 否 | 新增功能，不修改现有接口 |
| 是否影响数据库迁移 | 是 | 需要新增表和索引 |
| 是否影响配置文件 | 否 | 使用已有配置项 |
| 是否向后兼容 | 是 | 纯新增功能 |

### 性能评估

| 评估项 | 风险等级 | 说明 | 缓解措施 |
|--------|----------|------|----------|
| 响应时间 | 中 | OpenCode 调用有延迟 | 使用异步执行，显示进度 |
| 内存占用 | 低 | 处理有限消息数 | 分批处理 |
| 数据库 IO | 低 | 每次压缩一条记录 | 使用批量插入 |

### 风险清单

| 风险ID | 风险描述 | 可能性 | 影响 | 缓解措施 |
|--------|----------|--------|------|----------|
| R001 | OpenCode 调用超时 | 中 | 高 | 增加重试机制，设置合理超时 |
| R002 | 压缩结果解析失败 | 低 | 中 | JSON 解析异常处理，日志记录 |
| R003 | 并发压缩冲突 | 低 | 中 | 使用锁机制保护共享资源 |
```

### 2.4 开发检查清单（提交前必须确认）

```markdown
## 开发完成检查清单

### 功能检查
- [ ] 功能完全符合需求描述
- [ ] 所有参数校验已实现
- [ ] 所有异常已处理
- [ ] 边界条件已处理

### 代码质量
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 命名符合规范
- [ ] 无重复代码

### 测试覆盖
- [ ] 单元测试已编写
- [ ] 边界测试已编写
- [ ] 异常测试已编写
- [ ] 测试全部通过

### 静态检查
- [ ] mypy 检查通过
- [ ] ruff 检查通过
- [ ] 安全检查通过

### 文档更新
- [ ] API 文档已更新
- [ ] 架构图已更新（如有变更）
- [ ] CHANGELOG 已更新
```

---

## 三、测试流程（强制执行）

### 3.1 测试金字塔

```
                    ┌─────────┐
                    │  E2E    │  10%
                    │  Tests  │
                ┌───┴─────────┴───┐
                │  Integration    │  20%
                │     Tests       │
            ┌───┴─────────────────┴───┐
            │       Unit Tests        │  70%
            │                         │
            └─────────────────────────┘
```

### 3.2 单元测试规范

#### 3.2.1 测试文件结构

```python
# tests/unit/opencode/test_executor.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.src.opencode.executor import (
    OpenCodeExecutor,
    OpenCodeConfig,
    OpenCodeError
)


class TestOpenCodeConfig:
    """OpenCodeConfig 配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = OpenCodeConfig()
        assert config.model == "glm-4.7"
        assert config.timeout == 300
        assert config.max_retries == 3

    def test_custom_config(self):
        """测试自定义配置"""
        config = OpenCodeConfig(
            model="glm-5",
            timeout=600,
            max_retries=5
        )
        assert config.model == "glm-5"
        assert config.timeout == 600


class TestOpenCodeExecutor:
    """OpenCodeExecutor 执行器测试"""

    @pytest.fixture
    def executor(self):
        """创建测试用执行器"""
        return OpenCodeExecutor(OpenCodeConfig())

    @pytest.fixture
    def mock_subprocess(self):
        """模拟子进程执行"""
        with patch('asyncio.create_subprocess_exec') as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, mock_subprocess):
        """测试成功执行"""
        # Arrange
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"test result", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Act
        result = await executor.execute("test task")

        # Assert
        assert result == "test result"
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_context(self, executor, mock_subprocess):
        """测试带上下文执行"""
        # Arrange
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"result", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Act
        result = await executor.execute(
            task="test task",
            context="additional context"
        )

        # Assert
        assert result == "result"

    @pytest.mark.asyncio
    async def test_execute_failure_raises_error(self, executor, mock_subprocess):
        """测试执行失败抛出异常"""
        # Arrange
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"error message")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        # Act & Assert
        with pytest.raises(OpenCodeError) as exc_info:
            await executor.execute("test task")

        assert "error message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor, mock_subprocess):
        """测试执行超时"""
        # Arrange
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = mock_process

        # Act & Assert
        with pytest.raises(TimeoutError):
            await executor.execute("test task")

    @pytest.mark.asyncio
    async def test_execute_empty_task_raises_error(self, executor):
        """测试空任务抛出异常"""
        # Act & Assert
        with pytest.raises(ValueError, match="task cannot be empty"):
            await executor.execute("")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("model", ["glm-4.5", "glm-4.6", "glm-4.7", "glm-5"])
    async def test_execute_with_different_models(self, executor, mock_subprocess, model):
        """测试不同模型执行"""
        # Arrange
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"result", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Act
        result = await executor.execute("test task", model=model)

        # Assert
        assert result == "result"
        # 验证调用参数包含正确的模型
        call_args = mock_subprocess.call_args
        assert model in str(call_args)


class TestOpenCodeExecutorBatch:
    """批量执行测试"""

    @pytest.fixture
    def executor(self):
        return OpenCodeExecutor(OpenCodeConfig())

    @pytest.mark.asyncio
    async def test_batch_execute_concurrent_limit(self, executor):
        """测试并发限制"""
        # 模拟多个任务
        tasks = [
            {"task": f"task-{i}", "context": None}
            for i in range(10)
        ]

        with patch.object(executor, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "result"

            # 执行批量任务，限制并发为3
            results = await executor.execute_batch(tasks, max_concurrent=3)

            # 验证结果数量
            assert len(results) == 10
            # 验证并发限制（通过检查同时执行的数量）
            # 这里需要更复杂的验证，简化处理
```

#### 3.2.2 测试命名规范

```python
# 测试方法命名: test_{method_name}_{scenario}_{expected_result}

def test_compact_memories_with_valid_messages_returns_dict():
    pass

def test_compact_memories_with_empty_messages_raises_error():
    pass

def test_compact_memories_with_opencode_failure_retries():
    pass
```

### 3.3 集成测试规范

```python
# tests/integration/test_memory_flow.py

import pytest
import tempfile
import os

from backend.src.memory.compaction import MemoryCompaction
from backend.src.memory.index_manager import IndexManager
from backend.src.opencode.executor import OpenCodeExecutor, OpenCodeConfig
from backend.src.opencode.tasks import OpenCodeTasks
from backend.src.dal.database import Database


@pytest.fixture
def test_db():
    """创建测试数据库"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    db.init_tables()

    yield db

    # 清理
    os.unlink(db_path)


@pytest.fixture
def memory_system(test_db):
    """创建完整的记忆系统"""
    executor = OpenCodeExecutor(OpenCodeConfig())
    tasks = OpenCodeTasks(executor)
    index_manager = IndexManager(test_db)
    compaction = MemoryCompaction(tasks, test_db, index_manager)

    return {
        "executor": executor,
        "tasks": tasks,
        "index_manager": index_manager,
        "compaction": compaction
    }


@pytest.mark.integration
class TestMemoryCompactionFlow:
    """记忆压缩完整流程测试"""

    @pytest.mark.asyncio
    async def test_full_compaction_flow(self, memory_system):
        """测试完整压缩流程"""
        compaction = memory_system["compaction"]

        # 1. 创建测试消息
        messages = [
            {"role": "user", "content": "帮我写一个修仙小说的开头"},
            {"role": "assistant", "content": "好的，让我构思一下..."},
            # ... 更多消息
        ]

        # 2. 执行压缩
        index = await compaction.compact_layer1("test-session-id")

        # 3. 验证压缩结果
        assert index is not None
        assert index.summary is not None
        assert len(index.source_memory_ids) > 0
        assert index.compression_ratio < 1.0  # 压缩后应该更小

        # 4. 验证可以追溯
        trace_path = await compaction.get_trace_path(index.id)
        assert len(trace_path) > 0

    @pytest.mark.asyncio
    async def test_multi_layer_compaction(self, memory_system):
        """测试多层压缩"""
        compaction = memory_system["compaction"]

        # 1. 执行 Layer 1 压缩
        layer1_index = await compaction.compact_layer1("test-session")

        # 2. 执行 Layer 2 压缩（需要足够多的 Layer 1 索引）
        # 模拟多次 Layer 1 压缩
        for i in range(5):
            await compaction.compact_layer1(f"test-session-{i}")

        layer2_index = await compaction.compact_layer2("test-session")

        # 3. 验证层级关系
        assert layer2_index.layer == 2
        assert layer2_index.source_compaction_ids is not None
```

### 3.4 E2E 测试规范

```python
# tests/e2e/test_writing_workflow.py

import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
class TestWritingWorkflow:
    """写作完整流程 E2E 测试"""

    @pytest.mark.asyncio
    async def test_complete_novel_creation_flow(self):
        """测试完整小说创作流程"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            try:
                # 1. 创建新项目
                await page.goto("http://localhost:3000/projects")
                await page.click('button:has-text("新建项目")')
                await page.fill('input[name="title"]', "测试小说")
                await page.fill('textarea[name="description"]', "这是一个测试")
                await page.click('button:has-text("创建")')

                # 2. 添加创意
                await page.click('a:has-text("测试小说")')
                await page.click('button:has-text("添加创意")')
                await page.fill('textarea[name="idea"]', "一个程序员穿越到修仙世界")
                await page.click('button:has-text("分析创意")')

                # 3. 等待创意分析完成
                await page.wait_for_selector('.creative-analysis-result', timeout=30000)

                # 4. 生成大纲
                await page.click('button:has-text("生成大纲")')
                await page.wait_for_selector('.outline-result', timeout=60000)

                # 5. 验证结果
                outline = await page.text_content('.outline-result')
                assert len(outline) > 100

            finally:
                await browser.close()
```

### 3.5 测试执行命令

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -v

# 运行集成测试
pytest tests/integration -v -m integration

# 运行 E2E 测试
pytest tests/e2e -v -m e2e

# 运行特定测试
pytest tests/unit/opencode/test_executor.py::TestOpenCodeExecutor::test_execute_success -v

# 生成覆盖率报告
pytest --cov=backend/src --cov-report=html --cov-report=term

# 并行运行测试
pytest -n auto

# 只运行失败的测试
pytest --lf

# 停止于第一个失败
pytest -x
```

### 3.6 测试覆盖率要求

| 模块 | 最低覆盖率 | 目标覆盖率 |
|------|------------|------------|
| opencode | 80% | 90% |
| memory | 85% | 95% |
| expert | 80% | 90% |
| evolution | 80% | 90% |
| daemon | 75% | 85% |

```bash
# 检查覆盖率
pytest --cov=backend/src --cov-fail-under=80
```

---

## 四、参考文档

### 4.1 DeerFlow 官方文档

| 文档 | 链接 | 说明 |
|------|------|------|
| DeepWiki | https://deepwiki.com/deer-flow/deer-flow | 完整架构文档 |
| GitHub | https://github.com/deer-flow/deer-flow | 源码仓库 |
| Skills 系统 | `backend/src/skills/public/` | 内置 Skills 示例 |
| Memory 系统 | `backend/src/memory/long_term.py` | 长期记忆实现 |

### 4.2 OpenCode 官方文档

| 文档 | 路径/链接 | 说明 |
|------|-----------|------|
| 项目 README | `/Users/chenh/PycharmProjects/opencode/README.md` | 项目概述 |
| CLAUDE.md | `/Users/chenh/PycharmProjects/opencode/CLAUDE.md` | 开发指南 |
| 架构文档 | `/Users/chenh/PycharmProjects/opencode/packages/opencode/src/` | 源码参考 |

### 4.3 GLM Coding 套餐

| 文档 | 链接 | 说明 |
|------|------|------|
| 套餐概述 | https://docs.bigmodel.cn/cn/coding-plan/overview | 功能和限制 |
| 模型列表 | 套餐文档 | glm-4.5/4.6/4.7/5 |

### 4.4 项目设计文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 系统架构设计 | `deerflow-novel-系统架构设计.md` | 架构总览 |
| 需求实现清单 | `deerflow-novel-需求实现清单.md` | 方法级实现 |
| 开发任务清单 | `deerflow-novel-开发任务清单.md` | 任务ID映射 |

### 4.5 技术栈文档

| 技术 | 链接 | 说明 |
|------|------|------|
| Python | https://docs.python.org/3.11/ | 语言参考 |
| Pydantic | https://docs.pydantic.dev/ | 数据验证 |
| asyncio | https://docs.python.org/3/library/asyncio.html | 异步编程 |
| pytest | https://docs.pytest.org/ | 测试框架 |
| SQLite | https://www.sqlite.org/docs.html | 数据库 |
| LangChain | https://python.langchain.com/docs/ | Agent 框架 |
| LangGraph | https://langchain-ai.github.io/langgraph/ | 状态图 |

---

## 五、开发工作流

### 5.1 单个任务开发流程

```bash
# 1. 拉取最新代码
git checkout dev
git pull origin dev

# 2. 创建功能分支
git checkout -b feature/P1-OC-005-execute-method

# 3. 开发（遵循本文档规范）
# - 填写关联分析表
# - 填写影响评估表
# - 编写代码
# - 编写测试

# 4. 运行测试
pytest tests/unit/opencode/test_executor.py -v

# 5. 运行静态检查
mypy backend/src/opencode/
ruff check backend/src/opencode/

# 6. 提交代码
git add .
git commit -m "feat(opencode): implement execute method (#P1-OC-005)"

# 7. 推送分支
git push origin feature/P1-OC-005-execute-method

# 8. 创建 PR
gh pr create --base dev --title "feat(opencode): implement execute method"
```

### 5.2 提交信息规范

```bash
# 格式
<type>(<scope>): <subject> (#<task-id>)

# 类型
feat:     新功能
fix:      修复bug
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构
test:     测试
chore:    构建/工具

# 示例
feat(opencode): implement execute method (#P1-OC-005)
fix(memory): resolve compaction race condition (#P2-MEM-015)
docs(api): update chat endpoint documentation (#P8-API-016)
test(expert): add matcher unit tests (#P3-EXP-011)
```

### 5.3 PR 检查清单

```markdown
## PR 检查清单

### 代码质量
- [ ] 代码符合命名规范
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 无重复代码
- [ ] 设计模式正确应用

### 测试
- [ ] 单元测试覆盖
- [ ] 测试全部通过
- [ ] 覆盖率达标

### 静态检查
- [ ] mypy 通过
- [ ] ruff 通过
- [ ] 无安全警告

### 文档
- [ ] 相关文档已更新
- [ ] CHANGELOG 已更新

### 关联
- [ ] 任务ID在提交信息中
- [ ] 关联分析表已填写
- [ ] 影响评估表已填写
```

---

## 六、AI Agent 开发指令

### 6.1 开发前必读

当 AI Agent 收到开发任务时，必须按以下顺序执行：

```
1. 阅读本文档（deerflow-novel-开发说明文档.md）
2. 阅读系统架构设计（deerflow-novel-系统架构设计.md）
3. 查找任务详情（deerflow-novel-需求实现清单.md）
4. 查找任务ID（deerflow-novel-开发任务清单.md）
5. 填写关联分析表
6. 填写影响评估表
7. 开始编码
8. 编写测试
9. 运行检查
10. 提交代码
```

### 6.2 强制输出格式

AI Agent 在开发任务时，必须输出以下内容：

```markdown
## 任务开发报告

### 任务信息
- **任务ID**: P1-OC-005
- **任务描述**: 实现 `OpenCodeExecutor.execute` 基础执行方法

### 关联分析
[填写关联分析表]

### 影响评估
[填写影响评估表]

### 实现方案
[简要描述实现方案]

### 测试结果
- 单元测试: ✅ 5/5 通过
- 覆盖率: 92%

### 检查结果
- mypy: ✅ 通过
- ruff: ✅ 通过

### 待办事项
- [ ] 代码审查
- [ ] 合并到 dev 分支
```

---

## 七、常见问题

### 7.1 OpenCode 调用问题

**Q: OpenCode 调用超时怎么办？**

A:
1. 检查网络连接
2. 增加超时时间配置
3. 添加重试机制
4. 检查任务复杂度，可能需要拆分

**Q: 如何选择合适的模型？**

A:
| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 简单任务 | glm-4.5 | 速度快，成本低 |
| 复杂推理 | glm-4.7 | 平衡性能和成本 |
| 创意写作 | glm-5 | 最佳效果 |

### 7.2 记忆系统问题

**Q: 压缩后信息丢失怎么办？**

A:
1. 使用追溯功能查看原始内容
2. 调整压缩层级策略
3. 增加关键信息保留规则

### 7.3 测试问题

**Q: 异步测试失败？**

A:
1. 确保使用 `@pytest.mark.asyncio`
2. 检查 fixture 是否正确标记 async
3. 使用 `AsyncMock` 而非 `MagicMock`

---

## 八、版本控制

### 8.1 版本号规范

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 变更
MINOR: 向后兼容的功能新增
PATCH: 向后兼容的问题修复

示例:
1.0.0 -> 1.0.1  # Bug 修复
1.0.1 -> 1.1.0  # 新功能
1.1.0 -> 2.0.0  # 破坏性变更
```

### 8.2 CHANGELOG 格式

```markdown
# Changelog

## [1.1.0] - 2026-03-20

### Added
- OpenCode 代理层批量执行功能 (#P1-OC-013)
- 记忆系统 Layer 2 压缩 (#P2-MEM-011)

### Changed
- 优化 OpenCode 调用重试逻辑 (#P1-OC-007)

### Fixed
- 修复记忆追溯路径错误 (#P2-MEM-015)

### Deprecated
- 旧的压缩接口将在 2.0 移除
```

---

**文档结束**

*本文档是 DeerFlow Novel 项目的开发规范，所有开发者（包括 AI Agent）必须严格遵守。*
