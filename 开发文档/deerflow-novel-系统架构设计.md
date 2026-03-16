# DeerFlow Novel 系统架构设计文档

> 版本: 2.0.0
> 日期: 2026-03-16
> 基础框架: DeerFlow 2.0 + OpenCode
> 状态: 设计阶段

---

## 一、项目概述

### 1.1 项目目标

基于 **DeerFlow 2.0 + OpenCode** 构建**自我进化的自动化写作助手**。

### 1.2 技术选型理由

| 组件 | 选择 | 理由 |
|------|------|------|
| **主框架** | DeerFlow 2.0 | 已有 Sub-Agent、Memory、Skills、Sandbox 完整架构 |
| **LLM 调用层** | OpenCode | 连接 GLM Coding 套餐，无需额外 API 费用 |
| **LLM Provider** | GLM (智谱) | Coding 套餐支持，高性价比 |

### 1.3 核心能力

| 能力 | 描述 |
|------|------|
| 长时间运行 | 交互式+后台混合模式，空闲时自动进入学习模式 |
| 自我进化 | 基于反馈、对比实验进行策略优化 |
| 技能学习 | 从成功/失败案例中提取可复用技能 |
| 人类反馈强化 | 评分 + 评论 + 修改示范 |

### 1.4 关键约束

```
┌─────────────────────────────────────────────────────────────────┐
│                   GLM Coding 套餐约束                            │
├─────────────────────────────────────────────────────────────────┤
│  ✅ 可用：OpenCode、Claude Code、OpenClaw 等指定工具             │
│  ❌ 不可用：DeerFlow 直接调用 API                               │
│  📌 解决方案：DeerFlow 所有 LLM 调用通过 OpenCode CLI 代理       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DeerFlow Novel System                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                      应用层 (Application Layer)                    │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │  Web UI     │ │  CLI        │ │  Daemon     │ │  Scheduler   │ │ │
│  │  │ (DeerFlow)  │ │  (扩展)     │ │  Service    │ │  Service     │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                   ↓                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   DeerFlow 2.0 核心层 (复用)                       │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ Sub-Agent   │ │ Long-Term   │ │ Skills      │ │ Sandbox     │ │ │
│  │  │ Orchestration│ │ Memory     │ │ System      │ │ Execution   │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ Context     │ │ LangGraph   │ │ Gateway     │ │ Thread      │ │ │
│  │  │ Engineering │ │ Runtime     │ │ API         │ │ Management  │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                   ↓                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   扩展开发层 (Custom Extensions)                   │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ Daemon      │ │ Background  │ │ Evolution   │ │ Memory      │ │ │
│  │  │ Service     │ │ Learning    │ │ System      │ │ Extension   │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ Novel       │ │ Expert      │ │ Feedback    │ │ Quality     │ │ │
│  │  │ Skills      │ │ Matcher     │ │ Processor   │ │ Reviewer    │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                   ↓                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   OpenCode 代理层 (LLM Gateway)                    │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │                    OpenCodeExecutor                         │ │ │
│  │  │  execute() | executeWithConfirmation() | executeBatch()     │ │ │
│  │  │  - 通过 subprocess 调用 opencode CLI                        │ │ │
│  │  │  - 支持 GLM-4.5/4.6/4.7/5 模型选择                         │ │ │
│  │  │  - 走 GLM Coding 套餐额度                                   │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                   ↓                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   GLM Coding 套餐 (智谱 AI)                        │ │
│  │  - GLM-5 / GLM-5-Turbo / GLM-4.7 / GLM-4.6 / GLM-4.5             │ │
│  │  - 专属 MCP (视觉理解、联网搜索、网页读取、开源仓库)              │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、目录结构

基于 DeerFlow 2.0 原有结构进行扩展：

```
deer-flow/
├── backend/                          # DeerFlow 后端 (原有)
│   ├── src/
│   │   ├── agent/                    # LangGraph Agent (原有)
│   │   │   ├── lead_agent.py         # 主 Agent
│   │   │   ├── sub_agent.py          # 子 Agent
│   │   │   └── ...
│   │   │
│   │   ├── memory/                   # 记忆系统 (原有 + 扩展)
│   │   │   ├── long_term.py          # 长期记忆 (原有)
│   │   │   ├── compaction.py         # 记忆压缩 (新增)
│   │   │   ├── review.py             # 记忆回顾 (新增)
│   │   │   └── index_manager.py      # 索引管理 (新增)
│   │   │
│   │   ├── skills/                   # Skills 系统 (原有 + 扩展)
│   │   │   ├── public/               # 内置 Skills (原有)
│   │   │   │   ├── research/
│   │   │   │   ├── report-generation/
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── novel/                # 写作 Skills (新增)
│   │   │       ├── creative/         # 创意孵化
│   │   │       │   └── SKILL.md
│   │   │       ├── outline/          # 大纲生成
│   │   │       │   └── SKILL.md
│   │   │       ├── chapter/          # 章纲生成
│   │   │       │   └── SKILL.md
│   │   │       ├── writer/           # 正文写作
│   │   │       │   └── SKILL.md
│   │   │       ├── reviewer/         # 质量审查
│   │   │       │   └── SKILL.md
│   │   │       └── evolution/        # 自我进化
│   │   │           └── SKILL.md
│   │   │
│   │   ├── evolution/                # 自我进化系统 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── feedback.py           # 反馈处理
│   │   │   ├── skill_learner.py      # 技能学习
│   │   │   ├── evaluator.py          # 评估器
│   │   │   ├── optimizer.py          # 策略优化
│   │   │   └── experience_store.py   # 经验存储
│   │   │
│   │   ├── expert/                   # 领域专家系统 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── registry.py           # 专家注册表
│   │   │   ├── matcher.py            # 需求-专家匹配
│   │   │   └── session.py            # 专家会话管理
│   │   │
│   │   ├── daemon/                   # 守护进程 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── service.py            # 主服务
│   │   │   ├── learning.py           # 后台学习
│   │   │   └── scheduler.py          # 任务调度
│   │   │
│   │   ├── opencode/                 # OpenCode 集成 (新增)
│   │   │   ├── __init__.py
│   │   │   ├── executor.py           # 执行器
│   │   │   └── tasks.py              # 任务封装
│   │   │
│   │   └── gateway/                  # Gateway API (原有)
│   │       └── ...
│   │
│   └── ...
│
├── frontend/                         # DeerFlow 前端 (原有)
│   └── ...
│
├── sandbox/                          # 沙箱镜像 (原有)
│   └── ...
│
├── novel-data/                       # 小说项目数据 (新增)
│   ├── projects/                     # 项目目录
│   │   └── {project-id}/
│   │       ├── outline.json          # 大纲
│   │       ├── chapters/             # 章节
│   │       └── settings.json         # 项目设置
│   │
│   ├── skills/                       # 学习到的技能
│   │   └── *.skill.md
│   │
│   ├── experiences/                  # 经验记录
│   │   └── *.exp.md
│   │
│   └── memory/                       # 记忆数据库
│       └── novel.db
│
└── config.yaml                       # 配置文件 (原有 + 扩展)
```

---

## 四、核心模块设计

### 4.1 OpenCode 代理层

**职责**：所有 LLM 调用通过 OpenCode CLI，使用 GLM Coding 套餐

```python
# backend/src/opencode/executor.py

import subprocess
import json
from typing import Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class OpenCodeConfig(BaseModel):
    model: str = "glm-4.7"  # glm-4.5, glm-4.6, glm-4.7, glm-5, glm-5-turbo
    timeout: int = 300
    max_retries: int = 3

class OpenCodeExecutor:
    """
    OpenCode 执行器 - 所有 LLM 调用的代理层

    通过 subprocess 调用 opencode CLI，使用 GLM Coding 套餐
    """

    def __init__(self, config: Optional[OpenCodeConfig] = None):
        self.config = config or OpenCodeConfig()

    async def execute(
        self,
        task: str,
        context: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        执行 OpenCode 任务

        Args:
            task: 任务描述
            context: 上下文内容
            model: 指定模型 (可选，默认使用配置中的模型)

        Returns:
            执行结果
        """
        prompt = self._build_prompt(task, context)
        model = model or self.config.model

        cmd = ["opencode", "run", "-m", model, "--non-interactive", prompt]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.config.timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"OpenCode execution failed: {result.stderr}")

        return result.stdout.strip()

    async def execute_with_confirmation(
        self,
        task: str,
        context: str,
        criteria: list[str],
        max_rounds: int = 2
    ) -> tuple[str, bool, int]:
        """
        带确认的执行 - 多轮确认直到满意

        Returns:
            (result, confirmed, rounds)
        """
        current_result = await self.execute(task, context)
        rounds = 1
        confirmed = False

        while not confirmed and rounds <= max_rounds:
            confirmation_prompt = f"""
请检查以下结果是否满足要求：

原始任务: {task}

确认标准:
{chr(10).join(f"- {c}" for c in criteria)}

当前结果:
{current_result}

如果满足要求，请回复 "CONFIRMED: [最终结果]"
如果不满足，请回复 "REVISION: [改进后的结果]"
"""
            confirmation = await self.execute(confirmation_prompt)
            rounds += 1

            if confirmation.startswith("CONFIRMED:"):
                confirmed = True
                current_result = confirmation.replace("CONFIRMED:", "").strip()
            elif confirmation.startswith("REVISION:"):
                current_result = confirmation.replace("REVISION:", "").strip()

        return current_result, confirmed, rounds

    async def execute_batch(
        self,
        tasks: list[dict],
        max_concurrent: int = 3
    ) -> list[str]:
        """
        批量执行任务（并行）
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(task):
            async with semaphore:
                return await self.execute(task["task"], task.get("context"))

        results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])
        return list(results)

    def _build_prompt(self, task: str, context: Optional[str]) -> str:
        """构建完整提示词"""
        if context:
            return f"{task}\n\n--- 内容 ---\n{context}"
        return task


# 预定义的 OpenCode 任务
class OpenCodeTasks:
    """预定义的 OpenCode 任务封装"""

    def __init__(self, executor: OpenCodeExecutor):
        self.executor = executor

    async def compact_memories(
        self,
        messages: list[dict],
        layer: int = 1
    ) -> dict:
        """记忆压缩任务"""
        content = "\n\n".join(
            f"[{m['role']}]: {m['content']}"
            for m in messages
        )

        task = f"""
请对以下对话内容进行压缩总结（第 {layer} 层压缩）

要求：
1. 保留关键信息、决策和结论
2. 提取涉及的人物、地点、事件
3. 标注任务类型和主题
4. 输出 JSON 格式

输出格式：
{{
  "summary": "压缩后的摘要",
  "key_topics": ["主题1", "主题2"],
  "key_decisions": ["决策1", "决策2"],
  "key_entities": ["实体1", "实体2"],
  "key_conclusions": ["结论1", "结论2"],
  "task_type": "任务类型",
  "task_description": "任务描述"
}}
"""
        result = await self.executor.execute(task, content)
        return json.loads(result)

    async def extract_skill(
        self,
        task_execution: dict
    ) -> dict:
        """技能提取任务"""
        context = f"""
任务: {task_execution['task']}
执行过程: {task_execution['execution']}
结果: {task_execution['result']}
用户评分: {task_execution.get('score', 'N/A')}
用户反馈: {task_execution.get('feedback', '无')}
"""
        task = """
分析以上成功完成的任务，提取可复用的技能。

请输出：
1. 技能名称
2. 适用场景
3. 执行步骤
4. 注意事项
5. 成功要素

JSON 格式输出。
"""
        result, confirmed, _ = await self.executor.execute_with_confirmation(
            task,
            context,
            criteria=["技能描述清晰可执行", "适用场景明确", "步骤可复用"]
        )
        return json.loads(result)

    async def evaluate_writing(
        self,
        content: str,
        dimensions: list[dict]
    ) -> dict:
        """写作质量评估"""
        dim_desc = "\n".join(
            f"- {d['name']}: {d['description']}"
            for d in dimensions
        )

        task = f"""
请评估以下写作内容的质量：

评估维度:
{dim_desc}

评分标准: 1-10 分

待评估内容:
{content[:5000]}  # 截断防止过长

请输出 JSON 格式：
{{
  "scores": {{"维度名": 分数}},
  "issues": [{{"dimension": "维度", "issue": "问题", "severity": "low/medium/high"}}],
  "suggestions": ["建议1", "建议2"],
  "overall_score": 总分
}}
"""
        result = await self.executor.execute(task)
        return json.loads(result)

    async def analyze_feedback(
        self,
        original: str,
        modified: str,
        comment: Optional[str] = None,
        score: Optional[int] = None
    ) -> dict:
        """分析用户反馈"""
        context = f"""
原始内容:
{original}

用户修改后:
{modified}

{f"用户评论: {comment}" if comment else ""}
{f"用户评分: {score}/10" if score else ""}
"""
        task = """
分析用户的修改反馈：

1. 用户修改了什么（具体差异）
2. 修改的意图是什么
3. 体现了用户的什么偏好
4. 如何在未来的写作中应用这些偏好

JSON 格式输出。
"""
        result = await self.executor.execute(task, context)
        return json.loads(result)
```

---

### 4.2 记忆系统扩展

**职责**：在 DeerFlow 原有 Memory 基础上，增加压缩索引和任务驱动检索

```python
# backend/src/memory/compaction.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from ..opencode.executor import OpenCodeTasks

class CompactionIndex(BaseModel):
    """压缩索引"""
    id: str
    session_id: str
    layer: int  # 1, 2, 3

    # 源映射（可追溯）
    source_memory_ids: list[str]
    source_compaction_ids: Optional[list[str]] = None

    # 压缩结果
    summary: str

    # 关键信息
    key_topics: list[str]
    key_decisions: list[str]
    key_entities: list[str]
    key_conclusions: list[str]

    # 任务关联
    task_type: str
    task_description: str

    # 统计
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float

    created_at: datetime


class MemoryCompaction:
    """记忆压缩服务"""

    def __init__(self, opencode_tasks: OpenCodeTasks):
        self.tasks = opencode_tasks
        self.thresholds = {
            1: 10,   # Layer 1: 每 10 条消息压缩一次
            2: 5,    # Layer 2: 每 5 个 L1 压缩合并
            3: 3,    # Layer 3: 每 3 个 L2 压缩合并
        }

    async def compact(
        self,
        messages: list[dict],
        session_id: str,
        layer: int = 1
    ) -> CompactionIndex:
        """执行压缩"""

        # 1. 通过 OpenCode 压缩
        result = await self.tasks.compact_memories(messages, layer)

        # 2. 创建压缩索引
        compaction = CompactionIndex(
            id=self._generate_id(),
            session_id=session_id,
            layer=layer,
            source_memory_ids=[m["id"] for m in messages],
            summary=result["summary"],
            key_topics=result["key_topics"],
            key_decisions=result["key_decisions"],
            key_entities=result["key_entities"],
            key_conclusions=result["key_conclusions"],
            task_type=result["task_type"],
            task_description=result["task_description"],
            original_token_count=sum(m.get("token_count", 0) for m in messages),
            compressed_token_count=len(result["summary"]) // 4,  # 估算
            compression_ratio=0,
            created_at=datetime.now()
        )
        compaction.compression_ratio = 1 - (
            compaction.compressed_token_count / compaction.original_token_count
        )

        # 3. 存储压缩索引
        await self._store_compaction(compaction)

        # 4. 标记源记忆
        await self._mark_compacted(compaction.source_memory_ids, compaction.id)

        return compaction

    async def hierarchical_compact(
        self,
        session_id: str,
        target_layer: int
    ) -> CompactionIndex:
        """分层压缩（高层压缩基于低层摘要）"""
        current_layer = target_layer - 1

        # 获取当前层的压缩记录
        compactions = await self._get_layer_compactions(session_id, current_layer)

        if len(compactions) < self.thresholds.get(target_layer, 3):
            raise ValueError(f"Not enough compactions at layer {current_layer}")

        # 构建 "消息" 列表（实际是压缩摘要）
        pseudo_messages = [
            {
                "id": c.id,
                "role": "system",
                "content": c.summary,
                "token_count": c.compressed_token_count
            }
            for c in compactions
        ]

        # 执行高层压缩
        result = await self.tasks.compact_memories(pseudo_messages, target_layer)

        # 创建高层压缩索引
        higher_compaction = CompactionIndex(
            id=self._generate_id(),
            session_id=session_id,
            layer=target_layer,
            source_memory_ids=[],
            source_compaction_ids=[c.id for c in compactions],
            summary=result["summary"],
            key_topics=result["key_topics"],
            key_decisions=result["key_decisions"],
            key_entities=result["key_entities"],
            key_conclusions=result["key_conclusions"],
            task_type=result["task_type"],
            task_description=result["task_description"],
            original_token_count=sum(c.compressed_token_count for c in compactions),
            compressed_token_count=len(result["summary"]) // 4,
            compression_ratio=0,
            created_at=datetime.now()
        )
        higher_compaction.compression_ratio = 1 - (
            higher_compaction.compressed_token_count / higher_compaction.original_token_count
        )

        await self._store_compaction(higher_compaction)
        return higher_compaction

    def should_compact(self, session: dict) -> bool:
        """判断是否需要压缩"""
        if session.get("current_tokens", 0) >= session.get("max_tokens", 80000):
            return True
        if session.get("state") == "idle" and session.get("idle_time", 0) > 30 * 60:
            return True
        return False
```

```python
# backend/src/memory/review.py

from typing import Optional
from pydantic import BaseModel
from ..opencode.executor import OpenCodeTasks

class MemoryReviewResult(BaseModel):
    """记忆回顾结果"""
    current_task: str
    related_memories: list[dict]
    suggestions: list[str]


class MemoryReview:
    """记忆回顾服务"""

    def __init__(self, opencode_tasks: OpenCodeTasks):
        self.tasks = opencode_tasks

    async def review(
        self,
        current_task: str,
        task_type: Optional[str] = None
    ) -> MemoryReviewResult:
        """
        记忆回顾：根据当前任务查找相关历史
        """
        # 1. 搜索相关压缩摘要
        compactions = await self._search_compactions(current_task, task_type)

        # 2. 通过 OpenCode 生成回顾建议
        if compactions:
            review_result = await self.tasks.opencode.executor.execute(
                f"""
当前任务: {current_task}

以下是相关的历史记忆，请分析它们对当前任务的参考价值：

{self._format_compactions(compactions)}

请输出：
1. 最相关的记忆及其原因
2. 可复用的经验
3. 需要避免的问题
4. 具体建议
"""
            )
        else:
            review_result = "未找到相关的历史记录"

        return MemoryReviewResult(
            current_task=current_task,
            related_memories=[
                {
                    "compaction_id": c.id,
                    "summary": c.summary,
                    "task_type": c.task_type,
                    "key_conclusions": c.key_conclusions
                }
                for c in compactions[:5]
            ],
            suggestions=self._extract_suggestions(review_result)
        )

    async def expand_compaction(
        self,
        compaction_id: str,
        depth: int = 1
    ) -> dict:
        """
        展开压缩，追溯原始记忆

        Args:
            compaction_id: 压缩 ID
            depth: 追溯深度
        """
        compaction = await self._get_compaction(compaction_id)

        result = {
            "compaction": compaction.dict(),
            "source_compactions": [],
            "source_messages": []
        }

        # 如果有源压缩，递归展开
        if compaction.source_compaction_ids and depth > 0:
            for source_id in compaction.source_compaction_ids:
                result["source_compactions"].append(
                    await self.expand_compaction(source_id, depth - 1)
                )

        # 如果有源消息，加载原始内容
        if compaction.source_memory_ids:
            result["source_messages"] = await self._get_messages(
                compaction.source_memory_ids
            )

        return result

    async def _search_compactions(
        self,
        query: str,
        task_type: Optional[str] = None
    ) -> list:
        """搜索相关压缩摘要"""
        # 实现 FTS 搜索或向量搜索
        pass

    def _format_compactions(self, compactions: list) -> str:
        """格式化压缩记录为可读文本"""
        lines = []
        for i, c in enumerate(compactions, 1):
            lines.append(f"""
[记忆 {i}]
- 任务类型: {c.task_type}
- 任务描述: {c.task_description}
- 摘要: {c.summary[:200]}...
- 结论: {', '.join(c.key_conclusions[:3])}
""")
        return "\n".join(lines)

    def _extract_suggestions(self, review_text: str) -> list[str]:
        """从回顾文本中提取建议"""
        # 简单提取，实际可以用 LLM 进一步处理
        suggestions = []
        for line in review_text.split("\n"):
            if line.strip().startswith(("建议", "建议:", "- 建议")):
                suggestions.append(line.strip())
        return suggestions
```

---

### 4.3 自我进化系统

```python
# backend/src/evolution/feedback.py

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..opencode.executor import OpenCodeTasks

class Feedback(BaseModel):
    """反馈"""
    id: str
    session_id: str
    memory_id: Optional[str]
    type: str  # 'score' | 'comment' | 'modification'
    score: Optional[int]
    comment: Optional[str]
    original_content: Optional[str]
    modified_content: Optional[str]
    analysis: Optional[dict]
    created_at: datetime


class FeedbackProcessor:
    """反馈处理器"""

    def __init__(self, opencode_tasks: OpenCodeTasks):
        self.tasks = opencode_tasks

    async def process(self, feedback: Feedback) -> dict:
        """处理反馈"""

        if feedback.type == "modification":
            # 分析修改内容
            analysis = await self.tasks.analyze_feedback(
                original=feedback.original_content,
                modified=feedback.modified_content,
                comment=feedback.comment,
                score=feedback.score
            )
        elif feedback.type == "score":
            analysis = {"type": "score", "value": feedback.score}
        else:
            analysis = {"type": "comment", "value": feedback.comment}

        # 存储反馈
        feedback.analysis = analysis
        await self._store_feedback(feedback)

        # 触发进化流程
        await self._trigger_evolution(feedback)

        return analysis

    async def _trigger_evolution(self, feedback: Feedback):
        """触发进化流程"""
        # 如果评分高，触发技能提取
        if feedback.score and feedback.score >= 8:
            # 投递到后台学习队列
            await self._enqueue_skill_extraction(feedback.session_id)
```

```python
# backend/src/evolution/skill_learner.py

from typing import Optional
from pydantic import BaseModel
from ..opencode.executor import OpenCodeTasks

class Skill(BaseModel):
    """技能"""
    id: str
    name: str
    description: Optional[str]
    expert_id: Optional[str]

    # 技能内容
    prompt: str
    examples: list[dict]
    conditions: list[str]
    steps: list[str]

    # 统计
    success_rate: float = 0
    usage_count: int = 0

    # 来源
    source: str  # 'extracted' | 'manual' | 'imported'
    source_session_id: Optional[str]


class SkillLearner:
    """技能学习器"""

    def __init__(self, opencode_tasks: OpenCodeTasks):
        self.tasks = opencode_tasks

    async def extract_from_success(
        self,
        task_execution: dict
    ) -> Skill:
        """从成功案例提取技能"""

        # 验证执行成功率
        if task_execution.get("score", 0) < 8:
            raise ValueError("Task score too low for skill extraction")

        # 通过 OpenCode 提取技能
        result = await self.tasks.extract_skill(task_execution)

        # 创建技能
        skill = Skill(
            id=self._generate_id(),
            name=result["name"],
            description=result.get("description"),
            prompt=result["prompt"],
            examples=result.get("examples", []),
            conditions=result.get("conditions", []),
            steps=result.get("steps", []),
            source="extracted",
            source_session_id=task_execution.get("session_id")
        )

        # 存储技能
        await self._store_skill(skill)

        # 写入技能文件
        await self._write_skill_file(skill)

        return skill

    async def refine_skill(
        self,
        skill_id: str,
        feedback: Feedback
    ) -> Skill:
        """优化技能"""
        skill = await self._get_skill(skill_id)

        # 通过 OpenCode 优化
        result = await self.tasks.opencode.executor.execute(
            f"""
请根据用户反馈优化以下技能：

技能名称: {skill.name}
当前提示词: {skill.prompt}
用户反馈: {feedback.comment}
用户评分: {feedback.score}

请输出优化后的：
1. 提示词
2. 新增示例
3. 调整后的步骤
""",
            criteria=["优化后的技能更符合用户需求", "保持了原有核心能力"]
        )

        # 更新技能
        # ...

        return skill

    async def _write_skill_file(self, skill: Skill):
        """写入技能文件"""
        content = f"""# {skill.name}

## 描述
{skill.description or '无'}

## 适用场景
{chr(10).join(f"- {c}" for c in skill.conditions)}

## 执行步骤
{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(skill.steps))}

## 示例
"""
        for ex in skill.examples:
            content += f"""
### 输入
{ex.get('input', '')}

### 输出
{ex.get('output', '')}

"""

        # 写入文件
        skill_path = f"novel-data/skills/{skill.id}.skill.md"
        # ...
```

---

### 4.4 守护进程服务

```python
# backend/src/daemon/service.py

import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional

class DaemonState(Enum):
    IDLE = "idle"
    INTERACTIVE = "interactive"
    BACKGROUND = "background"
    PAUSED = "paused"


class DaemonService:
    """守护进程服务"""

    IDLE_TIMEOUT = 30 * 60  # 30 分钟无操作进入后台模式

    def __init__(self):
        self.state = DaemonState.IDLE
        self.last_activity = datetime.now()
        self.current_session: Optional[dict] = None
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        """启动守护进程"""
        self._running = True
        self.state = DaemonState.INTERACTIVE

        # 启动监控任务
        self._tasks.append(asyncio.create_task(self._monitor_idle()))
        self._tasks.append(asyncio.create_task(self._run_scheduler()))

        print("Daemon service started")

    async def stop(self):
        """停止守护进程"""
        self._running = False

        for task in self._tasks:
            task.cancel()

        self._tasks = []
        print("Daemon service stopped")

    async def touch(self):
        """更新活动时间"""
        self.last_activity = datetime.now()

        # 如果在后台模式，恢复交互模式
        if self.state == DaemonState.BACKGROUND:
            await self.resume_interactive_mode()

    async def resume_interactive_mode(self):
        """恢复交互模式"""
        if self.state != DaemonState.BACKGROUND:
            return

        print("Resuming interactive mode...")

        # 1. 暂停后台学习任务
        await self._pause_learning_tasks()

        # 2. 恢复交互会话
        if self.current_session:
            # 加载相关记忆到上下文
            await self._load_session_context(self.current_session)

        self.state = DaemonState.INTERACTIVE
        print("Interactive mode resumed")

    async def enter_background_mode(self):
        """进入后台模式"""
        if self.state != DaemonState.INTERACTIVE:
            return

        print("Entering background mode...")

        # 1. 保存当前会话状态
        if self.current_session:
            await self._save_session_state(self.current_session)

        # 2. 启动后台学习任务
        await self._start_learning_tasks()

        self.state = DaemonState.BACKGROUND
        print("Background mode started")

    async def _monitor_idle(self):
        """监控空闲时间"""
        while self._running:
            await asyncio.sleep(60)  # 每分钟检查一次

            if self.state == DaemonState.INTERACTIVE:
                idle_time = (datetime.now() - self.last_activity).total_seconds()
                if idle_time > self.IDLE_TIMEOUT:
                    await self.enter_background_mode()

    async def _run_scheduler(self):
        """运行任务调度器"""
        from .scheduler import LearningScheduler
        scheduler = LearningScheduler()

        while self._running:
            await asyncio.sleep(60)

            if self.state == DaemonState.BACKGROUND:
                await scheduler.run_due_tasks()
```

```python
# backend/src/daemon/learning.py

from typing import Callable
from datetime import datetime, timedelta
from enum import Enum

class LearningTask:
    """学习任务"""
    name: str
    description: str
    trigger: str  # 'idle' | 'scheduled' | 'threshold'
    interval: int  # 毫秒，0 表示不定时
    handler: Callable


class BackgroundLearning:
    """后台学习服务"""

    def __init__(self, skill_learner, evaluator, memory_compaction):
        self.skill_learner = skill_learner
        self.evaluator = evaluator
        self.memory_compaction = memory_compaction

        self.tasks = [
            {
                "name": "skill_extraction",
                "description": "从历史对话中提取新技能",
                "trigger": "idle",
                "interval": 0,
                "handler": self.extract_skills_from_history
            },
            {
                "name": "experience_consolidation",
                "description": "整合零散经验",
                "trigger": "scheduled",
                "interval": 24 * 60 * 60 * 1000,  # 每天
                "handler": self.consolidate_experiences
            },
            {
                "name": "writing_practice",
                "description": "模仿写作练习",
                "trigger": "idle",
                "interval": 0,
                "handler": self.practice_writing
            },
            {
                "name": "self_evaluation",
                "description": "自我评估",
                "trigger": "scheduled",
                "interval": 7 * 24 * 60 * 60 * 1000,  # 每周
                "handler": self.self_evaluate
            },
            {
                "name": "memory_compaction",
                "description": "记忆压缩",
                "trigger": "threshold",
                "interval": 0,
                "handler": self.compact_memories
            }
        ]

    async def extract_skills_from_history(self) -> int:
        """从历史提取技能"""
        # 1. 扫描高分反馈的会话
        high_score_sessions = await self._find_high_score_sessions()

        extracted = 0
        for session in high_score_sessions:
            try:
                # 2. 提取技能
                skill = await self.skill_learner.extract_from_success(session)
                extracted += 1
            except Exception as e:
                print(f"Failed to extract skill: {e}")

        return extracted

    async def practice_writing(self) -> dict:
        """模仿写作练习"""
        # 1. 选择热门作品片段
        work_sample = await self._select_work_sample()

        # 2. 总结剧情大纲
        outline = await self._summarize_outline(work_sample)

        # 3. 根据大纲重写
        my_writing = await self._write_from_outline(outline)

        # 4. 与原文对比打分
        comparison = await self._compare_writings(my_writing, work_sample)

        # 5. 记录差距和改进点
        await self._record_practice_result(comparison)

        return comparison

    async def self_evaluate(self) -> dict:
        """自我评估"""
        # 1. 统计近期写作质量
        recent_stats = await self._get_recent_stats()

        # 2. 分析用户反馈趋势
        feedback_trend = await self._analyze_feedback_trend()

        # 3. 生成改进建议
        suggestions = await self._generate_suggestions(recent_stats, feedback_trend)

        return {
            "stats": recent_stats,
            "trend": feedback_trend,
            "suggestions": suggestions
        }
```

---

### 4.5 写作 Skills

```
# backend/src/skills/novel/creative/SKILL.md

# 创意孵化

## 描述
将用户模糊的创意转化为可执行的核心概念

## 触发条件
- 用户输入包含"创意"、"点子"、"想法"、"脑洞"等关键词
- 用户描述一个故事概念的初步想法

## 输入格式
```
用户创意: {用户输入的创意描述}
```

## 执行步骤

1. **分析创意核心**
   - 识别核心冲突
   - 提取独特卖点
   - 确定目标读者群

2. **扩展创意维度**
   - 世界观可能方向
   - 主角设定可能方向
   - 剧情发展可能方向

3. **验证可行性**
   - 检查是否有足够的发展空间
   - 检查是否有明显的逻辑矛盾
   - 评估市场接受度

4. **输出结构化创意文档**
   - 核心创意（一句话）
   - 核心冲突
   - 核心卖点（3-5个）
   - 建议类型标签
   - 扩展方向建议

## 输出格式
```json
{
  "core_idea": "核心创意一句话",
  "core_conflict": "核心冲突描述",
  "selling_points": ["卖点1", "卖点2", "卖点3"],
  "suggested_genres": ["类型1", "类型2"],
  "expansion_directions": [
    {"direction": "方向名", "description": "描述"}
  ]
}
```

## 示例

### 输入
```
用户创意: 一个程序员穿越到修仙世界，用代码理解修仙法则
```

### 输出
```json
{
  "core_idea": "用编程思维解构修仙体系",
  "core_conflict": "逻辑思维 vs 玄学法则",
  "selling_points": [
    "反套路：理性分析打破修仙常规",
    "爽点：用代码思维创建新功法",
    "代入感：程序员读者的共鸣"
  ],
  "suggested_genres": ["穿越", "修仙", "系统流"],
  "expansion_directions": [
    {"direction": "世界观", "description": "修仙体系可代码化，有底层规则"},
    {"direction": "主角", "description": "资深程序员，擅长架构思维"}
  ]
}
```

## 注意事项
- 不要过早否定创意，先扩展再筛选
- 保持创意的独特性，避免同质化
- 关注创意的可持续性，能否支撑长篇
```

```
# backend/src/skills/novel/reviewer/SKILL.md

# 质量审查

## 描述
检查写作内容的质量，发现问题并提供修改建议

## 触发条件
- 写作 Agent 完成章节内容
- 用户请求检查某段内容

## 检查维度

### 1. 剧情逻辑
- 是否有前后矛盾
- 是否有逻辑漏洞
- 是否符合人物性格发展

### 2. 剧情连贯性
- 是否有跳跃感
- 场景转换是否自然
- 时间线是否清晰

### 3. 视角问题
- 视角是否统一
- 视角切换是否有过渡
- 视角切换跨度过大

### 4. 代入感
- 是否有阅读障碍描写
- 是否有信息过载
- 是否有生硬说明

### 5. 文风问题
- 是否有现代词汇穿越
- 是否有重复表达
- 是否有节奏拖沓

## 执行步骤

1. **加载检查规则**
2. **逐项检查**
3. **记录问题**
4. **生成修改建议**
5. **输出检查报告**

## 输出格式
```json
{
  "passed": false,
  "overall_score": 7.5,
  "issues": [
    {
      "type": "perspective_switch",
      "severity": "medium",
      "location": "第三段",
      "description": "视角从主角突然切换到路人，无过渡",
      "suggestion": "添加过渡句或使用主角视角观察路人"
    }
  ],
  "suggestions": ["建议1", "建议2"]
}
```

## 问题严重程度
- **high**: 必须修改，影响阅读体验
- **medium**: 建议修改，影响沉浸感
- **low**: 可选修改，锦上添花
```

---

## 五、数据库设计

### 5.1 新增表

```sql
-- 压缩索引表
CREATE TABLE compaction_index (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  layer INTEGER NOT NULL,  -- 1, 2, 3

  source_memory_ids TEXT NOT NULL,      -- JSON
  source_compaction_ids TEXT,           -- JSON

  summary TEXT NOT NULL,
  key_topics TEXT,                      -- JSON
  key_decisions TEXT,                   -- JSON
  key_entities TEXT,                    -- JSON
  key_conclusions TEXT,                 -- JSON

  task_type TEXT,
  task_description TEXT,

  original_token_count INTEGER,
  compressed_token_count INTEGER,
  compression_ratio REAL,

  created_at INTEGER NOT NULL
);

-- 任务-记忆关联表
CREATE TABLE task_memory_link (
  id TEXT PRIMARY KEY,
  task_signature TEXT NOT NULL,
  task_type TEXT NOT NULL,
  task_keywords TEXT NOT NULL,          -- JSON
  memory_id TEXT NOT NULL,
  memory_type TEXT NOT NULL,            -- 'message' | 'compaction'
  relevance_score REAL,
  recall_count INTEGER DEFAULT 0,
  created_at INTEGER NOT NULL
);

-- 技能表
CREATE TABLE skills (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  expert_id TEXT,

  prompt TEXT NOT NULL,
  examples TEXT,                        -- JSON
  conditions TEXT,                      -- JSON
  steps TEXT,                           -- JSON

  success_rate REAL DEFAULT 0,
  usage_count INTEGER DEFAULT 0,

  source TEXT NOT NULL,                 -- 'extracted' | 'manual'
  source_session_id TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- 经验表
CREATE TABLE experiences (
  id TEXT PRIMARY KEY,
  scenario TEXT NOT NULL,
  action TEXT NOT NULL,
  outcome TEXT NOT NULL,
  rating INTEGER,
  feedback TEXT,
  expert_id TEXT,
  session_id TEXT,
  created_at INTEGER NOT NULL
);

-- 反馈表
CREATE TABLE feedback_records (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  memory_id TEXT,

  type TEXT NOT NULL,                   -- 'score' | 'comment' | 'modification'
  score INTEGER,
  comment TEXT,
  original_content TEXT,
  modified_content TEXT,
  analysis TEXT,                        -- JSON

  created_at INTEGER NOT NULL
);

-- 领域专家表
CREATE TABLE experts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT NOT NULL,
  description TEXT,
  keywords TEXT NOT NULL,               -- JSON
  system_prompt TEXT NOT NULL,
  capabilities TEXT,                    -- JSON
  is_builtin BOOLEAN DEFAULT FALSE,
  usage_count INTEGER DEFAULT 0,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- 写作项目表
CREATE TABLE novel_projects (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft',

  core_idea TEXT,
  outline TEXT,                         -- JSON
  worldbuilding TEXT,                   -- JSON
  characters TEXT,                      -- JSON

  total_chapters INTEGER DEFAULT 0,
  completed_chapters INTEGER DEFAULT 0,
  total_words INTEGER DEFAULT 0,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- 章节表
CREATE TABLE novel_chapters (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_number INTEGER NOT NULL,
  title TEXT,

  chapter_outline TEXT,                 -- JSON
  content TEXT,
  word_count INTEGER DEFAULT 0,

  status TEXT DEFAULT 'pending',
  quality_score REAL,
  review_notes TEXT,                    -- JSON

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (project_id) REFERENCES novel_projects(id)
);

-- 守护进程状态表
CREATE TABLE daemon_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  state TEXT NOT NULL,
  last_activity INTEGER NOT NULL,
  current_session_id TEXT,
  background_task TEXT,
  updated_at INTEGER NOT NULL
);

-- 创建索引
CREATE INDEX idx_compaction_session ON compaction_index(session_id);
CREATE INDEX idx_compaction_layer ON compaction_index(layer);
CREATE INDEX idx_task_signature ON task_memory_link(task_signature);
CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_feedback_session ON feedback_records(session_id);
CREATE INDEX idx_chapters_project ON novel_chapters(project_id);

-- FTS5 全文搜索
CREATE VIRTUAL TABLE compaction_fts USING fts5(
  compaction_id,
  summary,
  task_description,
  key_topics,
  tokenize='porter unicode61'
);
```

---

## 六、配置文件扩展

```yaml
# config.yaml (DeerFlow 原有 + 扩展)

# ... DeerFlow 原有配置 ...

# ========== Novel System 扩展配置 ==========

novel:
  # OpenCode 配置
  opencode:
    enabled: true
    model: "glm-4.7"              # 默认模型
    timeout: 300                   # 超时时间(秒)
    max_retries: 3                 # 最大重试次数
    models:                        # 可用模型
      - glm-4.5
      - glm-4.6
      - glm-4.7
      - glm-5
      - glm-5-turbo

  # 守护进程配置
  daemon:
    idle_timeout: 1800             # 空闲超时(秒)，30分钟
    max_lifetime: 86400            # 最大运行时间(秒)，24小时

  # 记忆配置
  memory:
    max_tokens: 80000              # 上下文窗口上限
    warning_tokens: 60000          # 警告阈值
    compaction_threshold: 10       # Layer 1 压缩阈值

  # 进化配置
  evolution:
    skill_extraction_threshold: 8  # 评分>=8 触发技能提取
    feedback_weight:               # 反馈权重
      score: 0.4
      comment: 0.3
      modification: 0.3

  # 写作配置
  writing:
    default_style: "网文风格"
    chapter_word_count:            # 章节字数范围
      min: 2000
      max: 5000

  # 后台学习任务
  learning_tasks:
    - name: skill_extraction
      trigger: idle
      enabled: true

    - name: experience_consolidation
      trigger: scheduled
      interval: 86400             # 每天
      enabled: true

    - name: writing_practice
      trigger: idle
      enabled: true

    - name: self_evaluation
      trigger: scheduled
      interval: 604800            # 每周
      enabled: true
```

---

## 七、实现优先级

| Phase | 模块 | 依赖 DeerFlow | 需要开发 | 优先级 |
|-------|------|---------------|----------|--------|
| 1 | OpenCode 代理层 | 无 | 全新开发 | P0 |
| 2 | 记忆系统扩展 | Memory | 压缩、回顾、索引 | P0 |
| 3 | 领域专家系统 | 无 | 全新开发 | P1 |
| 4 | 自我进化系统 | 无 | 全新开发 | P1 |
| 5 | 写作 Skills | Skills | 写作相关 Skills | P1 |
| 6 | 守护进程 | 无 | 全新开发 | P2 |

---

## 八、与 DeerFlow 的集成点

```
┌─────────────────────────────────────────────────────────────────┐
│                    DeerFlow 集成点                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Skills 系统集成                                              │
│     ┌─────────────────────────────────────────────────────────┐│
│     │ DeerFlow 原有 Skills:                                   ││
│     │ /mnt/skills/public/                                     ││
│     │ ├── research/SKILL.md                                   ││
│     │ ├── report-generation/SKILL.md                          ││
│     │ └── ...                                                 ││
│     │                                                         ││
│     │ 新增 Novel Skills:                                      ││
│     │ /mnt/skills/novel/                                      ││
│     │ ├── creative/SKILL.md                                   ││
│     │ ├── outline/SKILL.md                                    ││
│     │ ├── chapter/SKILL.md                                    ││
│     │ ├── writer/SKILL.md                                     ││
│     │ ├── reviewer/SKILL.md                                   ││
│     │ └── evolution/SKILL.md                                  ││
│     └─────────────────────────────────────────────────────────┘│
│                                                                 │
│  2. Memory 系统扩展                                              │
│     ┌─────────────────────────────────────────────────────────┐│
│     │ DeerFlow Long-Term Memory                               ││
│     │         ↓                                               ││
│     │ 新增: compaction_index 表                               ││
│     │ 新增: task_memory_link 表                               ││
│     │ 新增: MemoryCompaction 服务                             ││
│     │ 新增: MemoryReview 服务                                 ││
│     └─────────────────────────────────────────────────────────┘│
│                                                                 │
│  3. LLM 调用替换                                                 │
│     ┌─────────────────────────────────────────────────────────┐│
│     │ 原有: DeerFlow → LangChain → LLM API                   ││
│     │         ↓                                               ││
│     │ 替换: DeerFlow → OpenCodeExecutor → OpenCode CLI       ││
│     │                              → GLM Coding 套餐          ││
│     └─────────────────────────────────────────────────────────┘│
│                                                                 │
│  4. 新增独立服务                                                  │
│     ┌─────────────────────────────────────────────────────────┐│
│     │ backend/src/daemon/      - 守护进程                     ││
│     │ backend/src/evolution/   - 自我进化                     ││
│     │ backend/src/expert/       - 领域专家                    ││
│     │ backend/src/opencode/     - OpenCode 集成              ││
│     └─────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**文档结束**
