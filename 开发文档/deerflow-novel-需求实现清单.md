# DeerFlow Novel 需求实现清单

> 版本: 2.0.0
> 日期: 2026-03-16
> 基础框架: DeerFlow 2.0 + OpenCode
> 状态: 需求细化

---

## 一、模块总览

| 模块ID | 模块名称 | 包路径 | 类数量 | 方法数量 |
|--------|----------|--------|--------|----------|
| M01 | OpenCode 代理层 | `backend/src/opencode` | 4 | 18 |
| M02 | 记忆系统扩展 | `backend/src/memory` | 5 | 24 |
| M03 | 领域专家系统 | `backend/src/expert` | 4 | 16 |
| M04 | 自我进化系统 | `backend/src/evolution` | 5 | 22 |
| M05 | 守护进程服务 | `backend/src/daemon` | 4 | 18 |
| M06 | 写作 Skills | `backend/src/skills/novel` | 6 | 30 |
| M07 | 数据访问层 | `backend/src/dal` | 8 | 32 |
| M08 | Web API 层 | `backend/src/api` | 6 | 20 |

**总计**: 42 类，180 方法

---

## 二、M01 - OpenCode 代理层

### 2.1 类清单

| 类ID | 类名 | 文件 | 描述 |
|------|------|------|------|
| M01-C01 | `OpenCodeConfig` | `executor.py` | OpenCode 配置模型 |
| M01-C02 | `OpenCodeExecutor` | `executor.py` | OpenCode 执行器 |
| M01-C03 | `OpenCodeTasks` | `tasks.py` | 预定义任务封装 |
| M01-C04 | `OpenCodePool` | `pool.py` | 执行器连接池 |

### 2.2 方法详情

#### M01-C01: OpenCodeConfig

```python
class OpenCodeConfig(BaseModel):
    """OpenCode 配置模型"""

    # 属性
    model: str              # 默认模型
    timeout: int            # 超时时间(秒)
    max_retries: int        # 最大重试次数
    models: list[str]       # 可用模型列表
    working_dir: str        # 工作目录
```

**方法**: 无（Pydantic 模型）

---

#### M01-C02: OpenCodeExecutor

```python
class OpenCodeExecutor:
    """OpenCode 执行器 - 所有 LLM 调用的代理层"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M01-M001 | `__init__` | `config: Optional[OpenCodeConfig]` | `None` | 初始化执行器 |
| M01-M002 | `execute` | `task: str, context: Optional[str], model: Optional[str]` | `str` | 执行 OpenCode 任务 |
| M01-M003 | `execute_with_confirmation` | `task: str, context: str, criteria: list[str], max_rounds: int` | `tuple[str, bool, int]` | 带确认的执行 |
| M01-M004 | `execute_batch` | `tasks: list[dict], max_concurrent: int` | `list[str]` | 批量并行执行 |
| M01-M005 | `_build_prompt` | `task: str, context: Optional[str]` | `str` | 构建完整提示词 |
| M01-M006 | `_run_subprocess` | `cmd: list[str]` | `subprocess.CompletedProcess` | 执行子进程 |
| M01-M007 | `_handle_error` | `error: Exception` | `None` | 错误处理 |
| M01-M008 | `set_model` | `model: str` | `None` | 切换模型 |

**实现逻辑**:

##### M01-M002: execute

```python
async def execute(self, task: str, context: Optional[str] = None, model: Optional[str] = None) -> str:
    """
    执行 OpenCode 任务

    实现逻辑:
    1. 构建完整提示词 (_build_prompt)
    2. 确定使用的模型 (model or config.model)
    3. 构建 CLI 命令: ["opencode", "run", "-m", model, "--non-interactive", prompt]
    4. 执行子进程，设置超时
    5. 检查返回码，非0则抛出异常
    6. 返回 stdout 内容
    """
```

##### M01-M003: execute_with_confirmation

```python
async def execute_with_confirmation(
    self,
    task: str,
    context: str,
    criteria: list[str],
    max_rounds: int = 2
) -> tuple[str, bool, int]:
    """
    带确认的执行 - 多轮确认直到满意

    实现逻辑:
    1. 执行初始任务，获取 current_result
    2. 进入循环 (rounds <= max_rounds):
       a. 构建确认提示词，包含:
          - 原始任务
          - 确认标准列表
          - 当前结果
       b. 请求 OpenCode 确认或改进
       c. 如果回复以 "CONFIRMED:" 开头:
          - 设置 confirmed = True
          - 提取最终结果
          - 退出循环
       d. 如果回复以 "REVISION:" 开头:
          - 更新 current_result
          - rounds += 1
    3. 返回 (current_result, confirmed, rounds)
    """
```

##### M01-M004: execute_batch

```python
async def execute_batch(self, tasks: list[dict], max_concurrent: int = 3) -> list[str]:
    """
    批量执行任务（并行）

    实现逻辑:
    1. 创建信号量 (asyncio.Semaphore)，限制并发数
    2. 为每个任务创建异步任务:
       a. 获取信号量
       b. 执行 execute(task["task"], task.get("context"))
       c. 释放信号量
    3. 使用 asyncio.gather 并行执行
    4. 返回结果列表
    """
```

---

#### M01-C03: OpenCodeTasks

```python
class OpenCodeTasks:
    """预定义的 OpenCode 任务封装"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M01-M009 | `__init__` | `executor: OpenCodeExecutor` | `None` | 初始化 |
| M01-M010 | `compact_memories` | `messages: list[dict], layer: int` | `dict` | 记忆压缩 |
| M01-M011 | `extract_skill` | `task_execution: dict` | `dict` | 技能提取 |
| M01-M012 | `evaluate_writing` | `content: str, dimensions: list[dict]` | `dict` | 写作评估 |
| M01-M013 | `analyze_feedback` | `original: str, modified: str, comment: Optional[str], score: Optional[int]` | `dict` | 反馈分析 |
| M01-M014 | `match_expert` | `query: str` | `dict` | 专家匹配 |
| M01-M015 | `generate_outline` | `core_idea: dict` | `dict` | 生成大纲 |
| M01-M016 | `expand_chapter` | `chapter_outline: dict` | `str` | 扩展章节 |
| M01-M017 | `self_evaluate` | `stats: dict` | `dict` | 自我评估 |

**实现逻辑**:

##### M01-M010: compact_memories

```python
async def compact_memories(self, messages: list[dict], layer: int = 1) -> dict:
    """
    记忆压缩任务

    实现逻辑:
    1. 格式化消息列表为字符串:
       - 每条消息: "[role]: content"
    2. 构建压缩任务提示词:
       - 要求保留关键信息
       - 提取人物、地点、事件
       - 标注任务类型和主题
       - 输出 JSON 格式
    3. 调用 executor.execute()
    4. 解析 JSON 结果并返回
    """
```

##### M01-M011: extract_skill

```python
async def extract_skill(self, task_execution: dict) -> dict:
    """
    技能提取任务

    实现逻辑:
    1. 构建上下文:
       - 任务描述
       - 执行过程
       - 结果
       - 用户评分和反馈
    2. 构建提取任务提示词:
       - 分析成功完成的任务
       - 提取可复用技能
       - 输出: 名称、场景、步骤、注意事项、成功要素
    3. 调用 executor.execute_with_confirmation()，确认标准:
       - 技能描述清晰可执行
       - 适用场景明确
       - 步骤可复用
    4. 解析 JSON 结果并返回
    """
```

---

#### M01-C04: OpenCodePool

```python
class OpenCodePool:
    """执行器连接池"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M01-M018 | `get_executor` | `model: Optional[str]` | `OpenCodeExecutor` | 获取执行器 |

---

## 三、M02 - 记忆系统扩展

### 3.1 类清单

| 类ID | 类名 | 文件 | 描述 |
|------|------|------|------|
| M02-C01 | `CompactionIndex` | `compaction.py` | 压缩索引模型 |
| M02-C02 | `MemoryCompaction` | `compaction.py` | 记忆压缩服务 |
| M02-C03 | `MemoryReview` | `review.py` | 记忆回顾服务 |
| M02-C04 | `IndexManager` | `index_manager.py` | 索引管理器 |
| M02-C05 | `TaskMemoryLinker` | `linker.py` | 任务-记忆关联器 |

### 3.2 方法详情

#### M02-C01: CompactionIndex

```python
class CompactionIndex(BaseModel):
    """压缩索引模型"""

    # 属性
    id: str                     # 唯一ID
    session_id: str             # 会话ID
    layer: int                  # 压缩层级 1-3
    source_memory_ids: list[str]    # 源消息ID
    source_compaction_ids: Optional[list[str]]  # 源压缩ID
    summary: str                # 摘要
    key_topics: list[str]       # 关键主题
    key_decisions: list[str]    # 关键决策
    key_entities: list[str]     # 关键实体
    key_conclusions: list[str]  # 关键结论
    task_type: Optional[str]    # 任务类型
    task_description: Optional[str]  # 任务描述
    original_token_count: int   # 原始token数
    compressed_token_count: int # 压缩后token数
    compression_ratio: float    # 压缩比
    created_at: int             # 创建时间
```

---

#### M02-C02: MemoryCompaction

```python
class MemoryCompaction:
    """记忆压缩服务"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M02-M001 | `__init__` | `opencode_tasks: OpenCodeTasks, db` | `None` | 初始化 |
| M02-M002 | `check_compaction_needed` | `session_id: str` | `bool` | 检查是否需要压缩 |
| M02-M003 | `compact_layer1` | `session_id: str` | `CompactionIndex` | Layer 1 压缩 |
| M02-M004 | `compact_layer2` | `session_id: str` | `CompactionIndex` | Layer 2 压缩 |
| M02-M005 | `compact_layer3` | `session_id: str` | `CompactionIndex` | Layer 3 压缩 |
| M02-M006 | `_compress_messages` | `messages: list[dict], layer: int` | `dict` | 压缩消息 |
| M02-M007 | `_save_index` | `index: CompactionIndex` | `None` | 保存索引 |
| M02-M008 | `get_trace_path` | `compaction_id: str` | `list[str]` | 获取追溯路径 |

**实现逻辑**:

##### M02-M002: check_compaction_needed

```python
async def check_compaction_needed(self, session_id: str) -> bool:
    """
    检查是否需要压缩

    实现逻辑:
    1. 获取会话当前 token 数
    2. 获取配置的 warning_tokens (60000)
    3. 如果 current_tokens > warning_tokens，返回 True
    4. 否则返回 False
    """
```

##### M02-M003: compact_layer1

```python
async def compact_layer1(self, session_id: str) -> CompactionIndex:
    """
    Layer 1 压缩 - 消息级别

    实现逻辑:
    1. 从数据库获取最近 N 条消息 (N = compaction_threshold, 默认10)
    2. 调用 opencode_tasks.compact_memories(messages, layer=1)
    3. 创建 CompactionIndex:
       - id: 生成唯一ID
       - source_memory_ids: 消息ID列表
       - summary, key_topics 等从压缩结果获取
       - original_token_count: 计算原始消息 token
       - compressed_token_count: 计算摘要 token
       - compression_ratio: 原始/压缩
    4. 调用 _save_index 保存到数据库
    5. 返回 CompactionIndex
    """
```

##### M02-M008: get_trace_path

```python
async def get_trace_path(self, compaction_id: str) -> list[str]:
    """
    获取追溯路径 - 从压缩索引追溯原始消息

    实现逻辑:
    1. 从数据库查询 compaction_id 对应的索引
    2. 获取 source_memory_ids 和 source_compaction_ids
    3. 递归查询 source_compaction_ids 的源
    4. 构建完整路径:
       - 如果 layer=1: [compaction_id] -> [memory_id, ...]
       - 如果 layer=2: [compaction_id] -> [layer1_compaction_id, ...] -> [memory_id, ...]
       - 如果 layer=3: [compaction_id] -> [layer2_compaction_id, ...] -> [layer1_compaction_id, ...] -> [memory_id, ...]
    5. 返回完整路径列表
    """
```

---

#### M02-C03: MemoryReview

```python
class MemoryReview:
    """记忆回顾服务"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M02-M009 | `__init__` | `opencode_tasks: OpenCodeTasks, index_manager` | `None` | 初始化 |
| M02-M010 | `review_by_task` | `task_signature: str` | `list[dict]` | 任务驱动检索 |
| M02-M011 | `review_by_keywords` | `keywords: list[str]` | `list[dict]` | 关键词检索 |
| M02-M012 | `review_by_time` | `start: int, end: int` | `list[dict]` | 时间范围检索 |
| M02-M013 | `_rank_relevance` | `results: list[dict]` | `list[dict]` | 相关性排序 |
| M02-M014 | `update_recall_count` | `link_id: str` | `None` | 更新召回次数 |

**实现逻辑**:

##### M02-M010: review_by_task

```python
async def review_by_task(self, task_signature: str) -> list[dict]:
    """
    任务驱动检索 - 根据任务特征检索相关记忆

    实现逻辑:
    1. 从 task_memory_link 表查询 task_signature 匹配的记录
    2. 按 relevance_score 和 recall_count 排序
    3. 对于每条记录:
       - 如果 memory_type == 'message': 从 message 表获取原始消息
       - 如果 memory_type == 'compaction': 从 compaction_index 表获取压缩索引
    4. 调用 _rank_relevance 进行最终相关性排序
    5. 更新召回记录 (update_recall_count)
    6. 返回排序后的记忆列表
    """
```

---

#### M02-C04: IndexManager

```python
class IndexManager:
    """索引管理器"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M02-M015 | `create_index` | `index: CompactionIndex` | `None` | 创建索引 |
| M02-M016 | `get_index` | `compaction_id: str` | `Optional[CompactionIndex]` | 获取索引 |
| M02-M017 | `search_fts` | `query: str, limit: int` | `list[CompactionIndex]` | 全文搜索 |
| M02-M018 | `delete_index` | `compaction_id: str` | `bool` | 删除索引 |
| M02-M019 | `get_session_indexes` | `session_id: str` | `list[CompactionIndex]` | 获取会话索引 |
| M02-M020 | `get_layer_indexes` | `layer: int` | `list[CompactionIndex]` | 获取层级索引 |

---

#### M02-C05: TaskMemoryLinker

```python
class TaskMemoryLinker:
    """任务-记忆关联器"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M02-M021 | `create_link` | `task_signature: str, memory_id: str, memory_type: str, relevance: float` | `str` | 创建关联 |
| M02-M022 | `get_task_memories` | `task_signature: str` | `list[dict]` | 获取任务记忆 |
| M02-M023 | `calculate_signature` | `task: str, keywords: list[str]` | `str` | 计算任务签名 |
| M02-M024 | `increment_recall` | `link_id: str` | `None` | 增加召回计数 |

---

## 四、M03 - 领域专家系统

### 4.1 类清单

| 类ID | 类名 | 文件 | 描述 |
|------|------|------|------|
| M03-C01 | `Expert` | `registry.py` | 专家模型 |
| M03-C02 | `ExpertRegistry` | `registry.py` | 专家注册表 |
| M03-C03 | `ExpertMatcher` | `matcher.py` | 需求-专家匹配 |
| M03-C04 | `ExpertSession` | `session.py` | 专家会话管理 |

### 4.2 方法详情

#### M03-C01: Expert

```python
class Expert(BaseModel):
    """领域专家模型"""

    # 属性
    id: str                     # 专家ID
    name: str                   # 专家名称
    domain: str                 # 领域
    description: str            # 描述
    keywords: list[str]         # 触发关键词
    system_prompt: str          # 系统提示词
    capabilities: list[str]     # 能力列表
    is_builtin: bool            # 是否内置
    usage_count: int            # 使用次数
    created_at: int
    updated_at: int
```

---

#### M03-C02: ExpertRegistry

```python
class ExpertRegistry:
    """专家注册表"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M03-M001 | `__init__` | `db` | `None` | 初始化 |
| M03-M002 | `register` | `expert: Expert` | `None` | 注册专家 |
| M03-M003 | `unregister` | `expert_id: str` | `bool` | 注销专家 |
| M03-M004 | `get_expert` | `expert_id: str` | `Optional[Expert]` | 获取专家 |
| M03-M005 | `list_experts` | `domain: Optional[str]` | `list[Expert]` | 列出专家 |
| M03-M006 | `get_builtin_experts` | `None` | `list[Expert]` | 获取内置专家 |

**实现逻辑**:

##### M03-M006: get_builtin_experts

```python
def get_builtin_experts(self) -> list[Expert]:
    """
    获取内置专家列表

    实现逻辑:
    返回预定义的专家列表:
    1. 创意策划师 (domain: creative)
    2. 大纲规划师 (domain: outline)
    3. 章节细化师 (domain: chapter)
    4. 正文写手 (domain: writing)
    5. 质量审查员 (domain: review)
    6. 世界观架构师 (domain: worldbuilding)
    7. 人物设计师 (domain: character)
    """
```

---

#### M03-C03: ExpertMatcher

```python
class ExpertMatcher:
    """需求-专家匹配"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M03-M007 | `__init__` | `registry: ExpertRegistry, opencode_tasks: OpenCodeTasks` | `None` | 初始化 |
| M03-M008 | `match` | `query: str` | `tuple[Expert, float]` | 匹配专家 |
| M03-M009 | `_keyword_match` | `query: str, expert: Expert` | `float` | 关键词匹配 |
| M03-M010 | `_semantic_match` | `query: str, expert: Expert` | `float` | 语义匹配 |
| M03-M011 | `suggest_switch` | `query: str, current_expert: Expert` | `Optional[Expert]` | 建议切换 |

**实现逻辑**:

##### M03-M008: match

```python
async def match(self, query: str) -> tuple[Expert, float]:
    """
    匹配最合适的专家

    实现逻辑:
    1. 获取所有专家列表
    2. 对每个专家计算匹配分数:
       - keyword_score = _keyword_match(query, expert)
       - semantic_score = await _semantic_match(query, expert)
       - total_score = keyword_score * 0.4 + semantic_score * 0.6
    3. 返回得分最高的专家及其分数
    """
```

##### M03-M010: _semantic_match

```python
async def _semantic_match(self, query: str, expert: Expert) -> float:
    """
    语义匹配 - 使用 OpenCode 进行语义分析

    实现逻辑:
    1. 构建语义匹配提示词:
       - 用户需求: query
       - 专家领域: expert.domain
       - 专家能力: expert.capabilities
    2. 调用 opencode_tasks.match_expert()
    3. 解析返回的匹配分数 (0-1)
    4. 返回分数
    """
```

---

#### M03-C04: ExpertSession

```python
class ExpertSession:
    """专家会话管理"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M03-M012 | `__init__` | `expert: Expert, parent_session_id: Optional[str]` | `None` | 初始化 |
| M03-M013 | `start` | `None` | `str` | 启动会话 |
| M03-M014 | `send_message` | `message: str` | `str` | 发送消息 |
| M03-M015 | `get_context` | `None` | `dict` | 获取上下文 |
| M03-M016 | `should_spawn_subagent` | `query: str` | `bool` | 判断是否需要子Agent |

**实现逻辑**:

##### M03-M016: should_spawn_subagent

```python
async def should_spawn_subagent(self, query: str) -> bool:
    """
    判断是否需要启动子 Agent

    实现逻辑:
    1. 分析 query 的任务类型
    2. 与当前专家的 domain 比较
    3. 如果 query 明显属于其他领域:
       - 计算上下文是否需要保留
       - 如果上下文无关或可迁移，返回 True
    4. 否则返回 False
    """
```

---

## 五、M04 - 自我进化系统

### 5.1 类清单

| 类ID | 类名 | 文件 | 描述 |
|------|------|------|------|
| M04-C01 | `FeedbackRecord` | `feedback.py` | 反馈记录模型 |
| M04-C02 | `FeedbackProcessor` | `feedback.py` | 反馈处理器 |
| M04-C03 | `Skill` | `skill_learner.py` | 技能模型 |
| M04-C04 | `SkillLearner` | `skill_learner.py` | 技能学习器 |
| M04-C05 | `StrategyOptimizer` | `optimizer.py` | 策略优化器 |

### 5.2 方法详情

#### M04-C01: FeedbackRecord

```python
class FeedbackRecord(BaseModel):
    """反馈记录模型"""

    # 属性
    id: str                     # 唯一ID
    session_id: str             # 会话ID
    memory_id: Optional[str]    # 关联记忆
    type: str                   # 类型: score/comment/modification
    score: Optional[int]        # 评分 (1-10)
    comment: Optional[str]      # 评论
    original_content: Optional[str]  # 原始内容
    modified_content: Optional[str]  # 修改后内容
    analysis: Optional[dict]    # 分析结果
    created_at: int
```

---

#### M04-C02: FeedbackProcessor

```python
class FeedbackProcessor:
    """反馈处理器"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M04-M001 | `__init__` | `opencode_tasks: OpenCodeTasks, db` | `None` | 初始化 |
| M04-M002 | `record_score` | `session_id: str, memory_id: str, score: int` | `FeedbackRecord` | 记录评分 |
| M04-M003 | `record_comment` | `session_id: str, memory_id: str, comment: str` | `FeedbackRecord` | 记录评论 |
| M04-M004 | `record_modification` | `session_id: str, original: str, modified: str, comment: Optional[str]` | `FeedbackRecord` | 记录修改 |
| M04-M005 | `analyze_feedback` | `record: FeedbackRecord` | `dict` | 分析反馈 |
| M04-M006 | `get_session_feedback` | `session_id: str` | `list[FeedbackRecord]` | 获取会话反馈 |
| M04-M007 | `calculate_feedback_weight` | `record: FeedbackRecord` | `float` | 计算反馈权重 |

**实现逻辑**:

##### M04-M004: record_modification

```python
async def record_modification(
    self,
    session_id: str,
    original: str,
    modified: str,
    comment: Optional[str] = None
) -> FeedbackRecord:
    """
    记录修改反馈

    实现逻辑:
    1. 创建 FeedbackRecord:
       - type = 'modification'
       - original_content = original
       - modified_content = modified
       - comment = comment
    2. 调用 analyze_feedback() 分析修改
    3. 将分析结果存入 record.analysis
    4. 保存到数据库
    5. 返回 FeedbackRecord
    """
```

##### M04-M005: analyze_feedback

```python
async def analyze_feedback(self, record: FeedbackRecord) -> dict:
    """
    分析反馈 - 使用 OpenCode

    实现逻辑:
    1. 根据 record.type 分别处理:
       - score: 直接返回 {"score": record.score}
       - comment: 提取评论中的偏好和问题
       - modification: 对比原文和修改，提取修改意图
    2. 对于 modification 类型:
       a. 调用 opencode_tasks.analyze_feedback(
            original=record.original_content,
            modified=record.modified_content,
            comment=record.comment
          )
       b. 返回分析结果
    3. 返回分析 dict
    """
```

---

#### M04-C03: Skill

```python
class Skill(BaseModel):
    """技能模型"""

    # 属性
    id: str                     # 唯一ID
    name: str                   # 技能名称
    description: str            # 描述
    expert_id: Optional[str]    # 关联专家
    prompt: str                 # 技能提示词
    examples: list[dict]        # 示例
    conditions: list[str]       # 触发条件
    steps: list[str]            # 执行步骤
    success_rate: float         # 成功率
    usage_count: int            # 使用次数
    source: str                 # 来源: extracted/manual
    source_session_id: Optional[str]
    created_at: int
    updated_at: int
```

---

#### M04-C04: SkillLearner

```python
class SkillLearner:
    """技能学习器"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M04-M008 | `__init__` | `opencode_tasks: OpenCodeTasks, db` | `None` | 初始化 |
| M04-M009 | `extract_from_success` | `session: dict` | `Skill` | 从成功提取 |
| M04-M010 | `extract_from_feedback` | `feedback: FeedbackRecord` | `Optional[Skill]` | 从反馈提取 |
| M04-M011 | `validate_skill` | `skill: Skill` | `bool` | 验证技能 |
| M04-M012 | `save_skill` | `skill: Skill` | `None` | 保存技能 |
| M04-M013 | `get_skill` | `skill_id: str` | `Optional[Skill]` | 获取技能 |
| M04-M014 | `list_skills` | `expert_id: Optional[str]` | `list[Skill]` | 列出技能 |
| M04-M015 | `update_success_rate` | `skill_id: str, success: bool` | `None` | 更新成功率 |

**实现逻辑**:

##### M04-M009: extract_from_success

```python
async def extract_from_success(self, session: dict) -> Skill:
    """
    从成功会话中提取技能

    实现逻辑:
    1. 构建 task_execution:
       - task: 会话的任务描述
       - execution: 会话的执行过程
       - result: 最终结果
       - score: 用户评分 (如果有)
       - feedback: 用户反馈 (如果有)
    2. 调用 opencode_tasks.extract_skill(task_execution)
    3. 创建 Skill:
       - id: 生成唯一ID
       - name: 从提取结果获取
       - prompt: 从提取结果构建
       - source = 'extracted'
       - source_session_id = session.id
    4. 调用 validate_skill() 验证
    5. 如果验证通过，调用 save_skill()
    6. 返回 Skill
    """
```

---

#### M04-C05: StrategyOptimizer

```python
class StrategyOptimizer:
    """策略优化器"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M04-M016 | `__init__` | `opencode_tasks: OpenCodeTasks, skill_learner: SkillLearner` | `None` | 初始化 |
| M04-M017 | `analyze_trends` | `time_range: tuple[int, int]` | `dict` | 分析趋势 |
| M04-M018 | `identify_patterns` | `feedbacks: list[FeedbackRecord]` | `list[dict]` | 识别模式 |
| M04-M019 | `suggest_improvements` | `analysis: dict` | `list[dict]` | 建议改进 |
| M04-M020 | `apply_optimization` | `skill: Skill, improvement: dict` | `Skill` | 应用优化 |
| M04-M021 | `run_ab_test` | `skill_a: Skill, skill_b: Skill, samples: list` | `dict` | A/B测试 |
| M04-M022 | `generate_report` | `time_range: tuple[int, int]` | `dict` | 生成报告 |

**实现逻辑**:

##### M04-M021: run_ab_test

```python
async def run_ab_test(
    self,
    skill_a: Skill,
    skill_b: Skill,
    samples: list
) -> dict:
    """
    A/B 测试对比两个技能版本

    实现逻辑:
    1. 将 samples 随机分为两组
    2. 对 Group A 使用 skill_a 执行
    3. 对 Group B 使用 skill_b 执行
    4. 收集两组的:
       - 执行成功率
       - 用户评分
       - 用户反馈
    5. 统计对比:
       - t-test 检验显著性
       - 计算置信区间
    6. 返回对比结果:
       {
         "skill_a_stats": {...},
         "skill_b_stats": {...},
         "winner": "a" | "b" | "tie",
         "confidence": 0.95,
         "recommendation": "..."
       }
    """
```

---

## 六、M05 - 守护进程服务

### 6.1 类清单

| 类ID | 类名 | 文件 | 描述 |
|------|------|------|------|
| M05-C01 | `DaemonConfig` | `service.py` | 守护进程配置 |
| M05-C02 | `DaemonService` | `service.py` | 主服务 |
| M05-C03 | `BackgroundLearning` | `learning.py` | 后台学习 |
| M05-C04 | `TaskScheduler` | `scheduler.py` | 任务调度器 |

### 6.2 方法详情

#### M05-C01: DaemonConfig

```python
class DaemonConfig(BaseModel):
    """守护进程配置"""

    # 属性
    idle_timeout: int           # 空闲超时(秒)，默认1800
    max_lifetime: int           # 最大运行时间(秒)，默认86400
    learning_tasks: list[dict]  # 学习任务配置
```

---

#### M05-C02: DaemonService

```python
class DaemonService:
    """守护进程主服务"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M05-M001 | `__init__` | `config: DaemonConfig` | `None` | 初始化 |
| M05-M002 | `start` | `None` | `None` | 启动服务 |
| M05-M003 | `stop` | `None` | `None` | 停止服务 |
| M05-M004 | `record_activity` | `None` | `None` | 记录活动 |
| M05-M005 | `check_idle` | `None` | `bool` | 检查空闲 |
| M05-M006 | `enter_background_mode` | `None` | `None` | 进入后台模式 |
| M05-M007 | `exit_background_mode` | `None` | `None` | 退出后台模式 |
| M05-M008 | `get_status` | `None` | `dict` | 获取状态 |

**实现逻辑**:

##### M05-M002: start

```python
async def start(self) -> None:
    """
    启动守护进程服务

    实现逻辑:
    1. 初始化状态:
       - state = 'running'
       - last_activity = 当前时间
    2. 启动空闲检查定时器 (每分钟检查)
    3. 启动后台学习服务 (BackgroundLearning)
    4. 启动任务调度器 (TaskScheduler)
    5. 进入主循环:
       while running:
         await asyncio.sleep(1)
    """
```

##### M05-M005: check_idle

```python
def check_idle(self) -> bool:
    """
    检查是否进入空闲状态

    实现逻辑:
    1. 获取当前时间
    2. 计算 last_activity 到现在的时间差
    3. 如果时间差 > idle_timeout (1800秒):
       返回 True
    4. 否则返回 False
    """
```

##### M05-M006: enter_background_mode

```python
async def enter_background_mode(self) -> None:
    """
    进入后台学习模式

    实现逻辑:
    1. 更新状态: state = 'background'
    2. 触发后台学习任务:
       - 技能提取
       - 经验整合
       - 写作练习
    3. 当有用户活动时自动退出
    """
```

---

#### M05-C03: BackgroundLearning

```python
class BackgroundLearning:
    """后台学习服务"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M05-M009 | `__init__` | `skill_learner, evaluator, memory_compaction` | `None` | 初始化 |
| M05-M010 | `extract_skills_from_history` | `None` | `int` | 提取技能 |
| M05-M011 | `consolidate_experiences` | `None` | `dict` | 整合经验 |
| M05-M012 | `practice_writing` | `None` | `dict` | 写作练习 |
| M05-M013 | `self_evaluate` | `None` | `dict` | 自我评估 |
| M05-M014 | `compact_memories` | `None` | `int` | 压缩记忆 |
| M05-M015 | `_find_high_score_sessions` | `None` | `list[dict]` | 查找高分会话 |
| M05-M016 | `_select_work_sample` | `None` | `str` | 选择作品样本 |
| M05-M017 | `_compare_writings` | `mine: str, original: str` | `dict` | 对比写作 |

**实现逻辑**:

##### M05-M012: practice_writing

```python
async def practice_writing(self) -> dict:
    """
    模仿写作练习

    实现逻辑:
    1. 调用 _select_work_sample() 选择热门作品片段
    2. 使用 opencode 总结剧情大纲
    3. 根据大纲自己重写
    4. 调用 _compare_writings() 与原文对比
    5. 记录差距和改进点到 experiences 表
    6. 返回对比结果
    """
```

---

#### M05-C04: TaskScheduler

```python
class TaskScheduler:
    """任务调度器"""
```

| 方法ID | 方法名 | 参数 | 返回值 | 描述 |
|--------|--------|------|--------|------|
| M05-M018 | `schedule` | `task: dict, trigger: str, interval: int` | `str` | 调度任务 |
| M05-M019 | `cancel` | `task_id: str` | `bool` | 取消任务 |
| M05-M020 | `run_pending` | `None` | `None` | 运行待执行 |
| M05-M021 | `get_next_run` | `task_id: str` | `int` | 获取下次运行时间 |

---

## 七、M06 - 写作 Skills

### 7.1 Skills 清单

| Skill ID | 名称 | 目录 | 触发条件 |
|----------|------|------|----------|
| SKILL-01 | 创意孵化 | `novel/creative` | "创意"、"点子"、"想法" |
| SKILL-02 | 大纲生成 | `novel/outline` | "大纲"、"规划"、"章节规划" |
| SKILL-03 | 章纲生成 | `novel/chapter` | "章纲"、"章节大纲"、"细化" |
| SKILL-04 | 正文写作 | `novel/writer` | "写正文"、"写内容"、"继续写" |
| SKILL-05 | 质量审查 | `novel/reviewer` | 写作完成、用户请求检查 |
| SKILL-06 | 自我进化 | `novel/evolution` | 反馈收集、技能提取 |

### 7.2 Skill 方法详情

每个 Skill 都是一个 SKILL.md 文件，包含：

1. **描述** - Skill 的功能说明
2. **触发条件** - 何时激活此 Skill
3. **输入格式** - 输入数据结构
4. **执行步骤** - 具体执行逻辑
5. **输出格式** - 输出数据结构
6. **示例** - 输入输出示例
7. **注意事项** - 使用注意点

---

## 八、M07 - 数据访问层

### 8.1 类清单

| 类ID | 类名 | 文件 | 描述 |
|------|------|------|------|
| M07-C01 | `CompactionIndexDAO` | `compaction_dao.py` | 压缩索引 DAO |
| M07-C02 | `TaskMemoryLinkDAO` | `link_dao.py` | 任务记忆关联 DAO |
| M07-C03 | `SkillDAO` | `skill_dao.py` | 技能 DAO |
| M07-C04 | `ExperienceDAO` | `experience_dao.py` | 经验 DAO |
| M07-C05 | `FeedbackDAO` | `feedback_dao.py` | 反馈 DAO |
| M07-C06 | `ExpertDAO` | `expert_dao.py` | 专家 DAO |
| M07-C07 | `NovelProjectDAO` | `project_dao.py` | 小说项目 DAO |
| M07-C08 | `NovelChapterDAO` | `chapter_dao.py` | 章节DAO |

### 8.2 通用 DAO 方法

每个 DAO 都包含以下通用方法：

| 方法ID | 方法名 | 描述 |
|--------|--------|------|
| M07-M001 | `create` | 创建记录 |
| M07-M002 | `get_by_id` | 按ID获取 |
| M07-M003 | `update` | 更新记录 |
| M07-M004 | `delete` | 删除记录 |
| M07-M005 | `list` | 列出记录 |

---

## 九、M08 - Web API 层

### 9.1 API 端点清单

| 端点ID | 方法 | 路径 | 描述 |
|--------|------|------|------|
| API-01 | POST | `/api/projects` | 创建项目 |
| API-02 | GET | `/api/projects` | 列出项目 |
| API-03 | GET | `/api/projects/:id` | 获取项目 |
| API-04 | PUT | `/api/projects/:id` | 更新项目 |
| API-05 | DELETE | `/api/projects/:id` | 删除项目 |
| API-06 | POST | `/api/projects/:id/chapters` | 创建章节 |
| API-07 | GET | `/api/projects/:id/chapters` | 列出章节 |
| API-08 | POST | `/api/feedback` | 提交反馈 |
| API-09 | GET | `/api/experts` | 列出专家 |
| API-10 | POST | `/api/experts/match` | 匹配专家 |
| API-11 | GET | `/api/skills` | 列出技能 |
| API-12 | GET | `/api/daemon/status` | 守护进程状态 |
| API-13 | POST | `/api/chat` | 聊天接口 |
| API-14 | GET | `/api/memories/search` | 记忆搜索 |
| API-15 | GET | `/api/memories/:id/trace` | 记忆追溯 |

### 9.2 API 方法详情

#### API-13: POST /api/chat

```python
async def chat(request: ChatRequest) -> ChatResponse:
    """
    聊天接口

    实现逻辑:
    1. 检查是否需要切换专家:
       - 调用 expert_matcher.match(request.message)
       - 如果匹配的专家与当前不同，询问用户是否切换
    2. 如果需要启动子 Agent:
       - 创建新的 ExpertSession
       - 判断是否需要迁移上下文
    3. 调用专家处理消息
    4. 检查是否需要记忆压缩
    5. 返回响应
    """
```

#### API-15: GET /api/memories/:id/trace

```python
async def trace_memory(memory_id: str) -> TraceResponse:
    """
    记忆追溯接口

    实现逻辑:
    1. 判断 memory_id 是消息还是压缩索引
    2. 如果是压缩索引:
       - 调用 memory_compaction.get_trace_path(memory_id)
       - 返回完整追溯路径
    3. 如果是消息:
       - 直接返回消息详情
    """
```

---

## 十、接口依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                       依赖关系图                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  M08 (Web API)                                                  │
│    ├── M03 (专家系统)                                           │
│    │     └── M01 (OpenCode 代理层)                              │
│    ├── M04 (自我进化)                                           │
│    │     ├── M01 (OpenCode 代理层)                              │
│    │     └── M07 (数据访问层)                                   │
│    ├── M02 (记忆扩展)                                           │
│    │     ├── M01 (OpenCode 代理层)                              │
│    │     └── M07 (数据访问层)                                   │
│    ├── M05 (守护进程)                                           │
│    │     ├── M02 (记忆扩展)                                     │
│    │     ├── M04 (自我进化)                                     │
│    │     └── M06 (写作 Skills)                                  │
│    └── M07 (数据访问层)                                         │
│                                                                 │
│  M06 (写作 Skills)                                              │
│    └── M01 (OpenCode 代理层)                                    │
│                                                                 │
│  M07 (数据访问层)                                               │
│    └── 数据库 (SQLite)                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 十一、开发顺序建议

| 阶段 | 模块 | 原因 |
|------|------|------|
| 1 | M01 (OpenCode 代理层) | 所有模块的基础依赖 |
| 2 | M07 (数据访问层) | 数据存储基础 |
| 3 | M02 (记忆扩展) | 核心能力，需要 M01 和 M07 |
| 4 | M03 (专家系统) | 需要 M01 |
| 5 | M04 (自我进化) | 需要 M01 和 M07 |
| 6 | M06 (写作 Skills) | 需要 M01 |
| 7 | M05 (守护进程) | 需要其他模块完成 |
| 8 | M08 (Web API) | 最后集成 |

---

**文档结束**
