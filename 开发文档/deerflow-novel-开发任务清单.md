# DeerFlow Novel 开发任务清单

> 版本: 2.0.0
> 日期: 2026-03-16
> 基础框架: DeerFlow 2.0 + OpenCode
> 状态: 开发中 (M1 里程碑已完成)

---

## 任务状态说明

| 状态 | 标记 | 描述 |
|------|------|------|
| 待开发 | `[ ]` | 任务未开始 |
| 开发中 | `[-]` | 正在开发 |
| 开发完成 | `[x]` | 代码完成，待测试 |
| 待测试 | `[t]` | 已提交测试 |
| 测试通过 | `[✓]` | 测试验证通过 |

---

## 一、Phase 1 - OpenCode 代理层 (P0)

### 1.1 基础配置

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P1-OC-001 | 创建 `backend/src/opencode/` 目录结构 | [✓] | TC-P1-OC-001 |
| P1-OC-002 | 实现 `OpenCodeConfig` Pydantic 模型 | [✓] | TC-P1-OC-002 |
| P1-OC-003 | 配置文件 `config.yaml` 添加 opencode 配置项 | [✓] | TC-P1-OC-003 |

### 1.2 OpenCodeExecutor 核心实现

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P1-OC-004 | 实现 `OpenCodeExecutor.__init__` 初始化方法 | [✓] | TC-P1-OC-004 |
| P1-OC-005 | 实现 `OpenCodeExecutor.execute` 基础执行方法 | [✓] | TC-P1-OC-005 |
| P1-OC-006 | 实现 `OpenCodeExecutor._build_prompt` 提示词构建 | [✓] | TC-P1-OC-006 |
| P1-OC-007 | 实现 `OpenCodeExecutor._run_subprocess` 子进程执行 | [✓] | TC-P1-OC-007 |
| P1-OC-008 | 实现 `OpenCodeExecutor._handle_error` 错误处理 | [✓] | TC-P1-OC-008 |
| P1-OC-009 | 实现 `OpenCodeExecutor.set_model` 模型切换 | [✓] | TC-P1-OC-009 |

### 1.3 带确认的执行

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P1-OC-010 | 实现 `OpenCodeExecutor.execute_with_confirmation` 确认循环逻辑 | [✓] | TC-P1-OC-010 |
| P1-OC-011 | 实现确认提示词模板生成 | [✓] | TC-P1-OC-011 |
| P1-OC-012 | 实现 CONFIRMED/REVISION 结果解析 | [✓] | TC-P1-OC-012 |

### 1.4 批量执行

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P1-OC-013 | 实现 `OpenCodeExecutor.execute_batch` 并行执行 | [✓] | TC-P1-OC-013 |
| P1-OC-014 | 实现并发控制信号量 | [✓] | TC-P1-OC-014 |

### 1.5 预定义任务封装

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P1-OC-015 | 创建 `OpenCodeTasks` 类框架 | [✓] | TC-P1-OC-015 |
| P1-OC-016 | 实现 `OpenCodeTasks.compact_memories` 记忆压缩任务 | [✓] | TC-P1-OC-016 |
| P1-OC-017 | 实现 `OpenCodeTasks.extract_skill` 技能提取任务 | [✓] | TC-P1-OC-017 |
| P1-OC-018 | 实现 `OpenCodeTasks.evaluate_writing` 写作评估任务 | [✓] | TC-P1-OC-018 |
| P1-OC-019 | 实现 `OpenCodeTasks.analyze_feedback` 反馈分析任务 | [✓] | TC-P1-OC-019 |
| P1-OC-020 | 实现 `OpenCodeTasks.match_expert` 专家匹配任务 | [✓] | TC-P1-OC-020 |
| P1-OC-021 | 实现 `OpenCodeTasks.generate_outline` 大纲生成任务 | [✓] | TC-P1-OC-021 |
| P1-OC-022 | 实现 `OpenCodeTasks.expand_chapter` 章节扩展任务 | [✓] | TC-P1-OC-022 |
| P1-OC-023 | 实现 `OpenCodeTasks.self_evaluate` 自我评估任务 | [✓] | TC-P1-OC-023 |

### 1.6 执行器连接池

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P1-OC-024 | 实现 `OpenCodePool` 连接池 | [✓] | TC-P1-OC-024 |
| P1-OC-025 | 实现 `OpenCodePool.get_executor` 获取执行器 | [✓] | TC-P1-OC-025 |

---

## 二、Phase 2 - 记忆系统扩展 (P0)

### 2.1 数据库表结构

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P2-MEM-001 | 创建 `compaction_index` 表 | [ ] | TC-P2-MEM-001 |
| P2-MEM-002 | 创建 `task_memory_link` 表 | [ ] | TC-P2-MEM-002 |
| P2-MEM-003 | 创建 `compaction_fts` FTS5 全文索引 | [ ] | TC-P2-MEM-003 |
| P2-MEM-004 | 创建相关数据库索引 | [ ] | TC-P2-MEM-004 |

### 2.2 压缩索引模型

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P2-MEM-005 | 实现 `CompactionIndex` Pydantic 模型 | [✓] | TC-P2-MEM-005 |
| P2-MEM-006 | 实现 token 计数方法 | [✓] | TC-P2-MEM-006 |
| P2-MEM-007 | 实现压缩比计算 | [✓] | TC-P2-MEM-007 |

### 2.3 记忆压缩服务

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P2-MEM-008 | 创建 `MemoryCompaction` 服务类 | [✓] | TC-P2-MEM-008 |
| P2-MEM-009 | 实现 `check_compaction_needed` 压缩检查 | [✓] | TC-P2-MEM-009 |
| P2-MEM-010 | 实现 `compact_layer1` Layer 1 压缩 | [✓] | TC-P2-MEM-010 |
| P2-MEM-011 | 实现 `compact_layer2` Layer 2 压缩 | [✓] | TC-P2-MEM-011 |
| P2-MEM-012 | 实现 `compact_layer3` Layer 3 压缩 | [✓] | TC-P2-MEM-012 |
| P2-MEM-013 | 实现 `_compress_messages` 消息压缩核心逻辑 | [✓] | TC-P2-MEM-013 |
| P2-MEM-014 | 实现 `_save_index` 索引保存 | [✓] | TC-P2-MEM-014 |
| P2-MEM-015 | 实现 `get_trace_path` 追溯路径获取 | [✓] | TC-P2-MEM-015 |

### 2.4 记忆回顾服务

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P2-MEM-016 | 创建 `MemoryReview` 服务类 | [✓] | TC-P2-MEM-016 |
| P2-MEM-017 | 实现 `review_by_task` 任务驱动检索 | [✓] | TC-P2-MEM-017 |
| P2-MEM-018 | 实现 `review_by_keywords` 关键词检索 | [✓] | TC-P2-MEM-018 |
| P2-MEM-019 | 实现 `review_by_time` 时间范围检索 | [✓] | TC-P2-MEM-019 |
| P2-MEM-020 | 实现 `_rank_relevance` 相关性排序 | [✓] | TC-P2-MEM-020 |
| P2-MEM-021 | 实现 `update_recall_count` 召回计数更新 | [✓] | TC-P2-MEM-021 |

### 2.5 索引管理器

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P2-MEM-022 | 创建 `IndexManager` 类 | [✓] | TC-P2-MEM-022 |
| P2-MEM-023 | 实现 `create_index` 创建索引 | [✓] | TC-P2-MEM-023 |
| P2-MEM-024 | 实现 `get_index` 获取索引 | [✓] | TC-P2-MEM-024 |
| P2-MEM-025 | 实现 `search_fts` 全文搜索 | [✓] | TC-P2-MEM-025 |
| P2-MEM-026 | 实现 `delete_index` 删除索引 | [✓] | TC-P2-MEM-026 |
| P2-MEM-027 | 实现 `get_session_indexes` 获取会话索引 | [✓] | TC-P2-MEM-027 |
| P2-MEM-028 | 实现 `get_layer_indexes` 获取层级索引 | [✓] | TC-P2-MEM-028 |

### 2.6 任务-记忆关联器

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P2-MEM-029 | 创建 `TaskMemoryLinker` 类 | [✓] | TC-P2-MEM-029 |
| P2-MEM-030 | 实现 `create_link` 创建关联 | [✓] | TC-P2-MEM-030 |
| P2-MEM-031 | 实现 `get_task_memories` 获取任务记忆 | [✓] | TC-P2-MEM-031 |
| P2-MEM-032 | 实现 `calculate_signature` 计算任务签名 | [✓] | TC-P2-MEM-032 |
| P2-MEM-033 | 实现 `increment_recall` 增加召回计数 | [✓] | TC-P2-MEM-033 |

---

## 三、Phase 3 - 领域专家系统 (P1)

### 3.1 数据库表结构

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P3-EXP-001 | 创建 `experts` 表 | [ ] | TC-P3-EXP-001 |
| P3-EXP-002 | 创建专家相关索引 | [ ] | TC-P3-EXP-002 |

### 3.2 专家模型与注册表

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P3-EXP-003 | 实现 `Expert` Pydantic 模型 | [ ] | TC-P3-EXP-003 |
| P3-EXP-004 | 创建 `ExpertRegistry` 注册表类 | [ ] | TC-P3-EXP-004 |
| P3-EXP-005 | 实现 `register` 注册专家 | [ ] | TC-P3-EXP-005 |
| P3-EXP-006 | 实现 `unregister` 注销专家 | [ ] | TC-P3-EXP-006 |
| P3-EXP-007 | 实现 `get_expert` 获取专家 | [ ] | TC-P3-EXP-007 |
| P3-EXP-008 | 实现 `list_experts` 列出专家 | [ ] | TC-P3-EXP-008 |
| P3-EXP-009 | 实现 `get_builtin_experts` 内置专家列表 | [ ] | TC-P3-EXP-009 |

### 3.3 需求-专家匹配

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P3-EXP-010 | 创建 `ExpertMatcher` 匹配器类 | [ ] | TC-P3-EXP-010 |
| P3-EXP-011 | 实现 `match` 匹配最合适专家 | [ ] | TC-P3-EXP-011 |
| P3-EXP-012 | 实现 `_keyword_match` 关键词匹配 | [ ] | TC-P3-EXP-012 |
| P3-EXP-013 | 实现 `_semantic_match` 语义匹配 | [ ] | TC-P3-EXP-013 |
| P3-EXP-014 | 实现 `suggest_switch` 建议切换专家 | [ ] | TC-P3-EXP-014 |

### 3.4 专家会话管理

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P3-EXP-015 | 创建 `ExpertSession` 会话类 | [ ] | TC-P3-EXP-015 |
| P3-EXP-016 | 实现 `start` 启动会话 | [ ] | TC-P3-EXP-016 |
| P3-EXP-017 | 实现 `send_message` 发送消息 | [ ] | TC-P3-EXP-017 |
| P3-EXP-018 | 实现 `get_context` 获取上下文 | [ ] | TC-P3-EXP-018 |
| P3-EXP-019 | 实现 `should_spawn_subagent` 判断子Agent需求 | [ ] | TC-P3-EXP-019 |

### 3.5 内置专家定义

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P3-EXP-020 | 定义"创意策划师"专家 | [ ] | TC-P3-EXP-020 |
| P3-EXP-021 | 定义"大纲规划师"专家 | [ ] | TC-P3-EXP-021 |
| P3-EXP-022 | 定义"章节细化师"专家 | [ ] | TC-P3-EXP-022 |
| P3-EXP-023 | 定义"正文写手"专家 | [ ] | TC-P3-EXP-023 |
| P3-EXP-024 | 定义"质量审查员"专家 | [ ] | TC-P3-EXP-024 |
| P3-EXP-025 | 定义"世界观架构师"专家 | [ ] | TC-P3-EXP-025 |
| P3-EXP-026 | 定义"人物设计师"专家 | [ ] | TC-P3-EXP-026 |

---

## 四、Phase 4 - 自我进化系统 (P1)

### 4.1 数据库表结构

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P4-EVO-001 | 创建 `skills` 表 | [ ] | TC-P4-EVO-001 |
| P4-EVO-002 | 创建 `experiences` 表 | [ ] | TC-P4-EVO-002 |
| P4-EVO-003 | 创建 `feedback_records` 表 | [ ] | TC-P4-EVO-003 |
| P4-EVO-004 | 创建相关数据库索引 | [ ] | TC-P4-EVO-004 |

### 4.2 反馈模型与处理器

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P4-EVO-005 | 实现 `FeedbackRecord` Pydantic 模型 | [ ] | TC-P4-EVO-005 |
| P4-EVO-006 | 创建 `FeedbackProcessor` 处理器类 | [ ] | TC-P4-EVO-006 |
| P4-EVO-007 | 实现 `record_score` 记录评分 | [ ] | TC-P4-EVO-007 |
| P4-EVO-008 | 实现 `record_comment` 记录评论 | [ ] | TC-P4-EVO-008 |
| P4-EVO-009 | 实现 `record_modification` 记录修改 | [ ] | TC-P4-EVO-009 |
| P4-EVO-010 | 实现 `analyze_feedback` 分析反馈 | [ ] | TC-P4-EVO-010 |
| P4-EVO-011 | 实现 `get_session_feedback` 获取会话反馈 | [ ] | TC-P4-EVO-011 |
| P4-EVO-012 | 实现 `calculate_feedback_weight` 计算反馈权重 | [ ] | TC-P4-EVO-012 |

### 4.3 技能模型与学习器

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P4-EVO-013 | 实现 `Skill` Pydantic 模型 | [ ] | TC-P4-EVO-013 |
| P4-EVO-014 | 创建 `SkillLearner` 学习器类 | [ ] | TC-P4-EVO-014 |
| P4-EVO-015 | 实现 `extract_from_success` 从成功提取技能 | [ ] | TC-P4-EVO-015 |
| P4-EVO-016 | 实现 `extract_from_feedback` 从反馈提取技能 | [ ] | TC-P4-EVO-016 |
| P4-EVO-017 | 实现 `validate_skill` 验证技能 | [ ] | TC-P4-EVO-017 |
| P4-EVO-018 | 实现 `save_skill` 保存技能 | [ ] | TC-P4-EVO-018 |
| P4-EVO-019 | 实现 `get_skill` 获取技能 | [ ] | TC-P4-EVO-019 |
| P4-EVO-020 | 实现 `list_skills` 列出技能 | [ ] | TC-P4-EVO-020 |
| P4-EVO-021 | 实现 `update_success_rate` 更新成功率 | [ ] | TC-P4-EVO-021 |

### 4.4 策略优化器

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P4-EVO-022 | 创建 `StrategyOptimizer` 优化器类 | [ ] | TC-P4-EVO-022 |
| P4-EVO-023 | 实现 `analyze_trends` 分析趋势 | [ ] | TC-P4-EVO-023 |
| P4-EVO-024 | 实现 `identify_patterns` 识别模式 | [ ] | TC-P4-EVO-024 |
| P4-EVO-025 | 实现 `suggest_improvements` 建议改进 | [ ] | TC-P4-EVO-025 |
| P4-EVO-026 | 实现 `apply_optimization` 应用优化 | [ ] | TC-P4-EVO-026 |
| P4-EVO-027 | 实现 `run_ab_test` A/B测试 | [ ] | TC-P4-EVO-027 |
| P4-EVO-028 | 实现 `generate_report` 生成报告 | [ ] | TC-P4-EVO-028 |

---

## 五、Phase 5 - 写作 Skills (P1)

### 5.1 Skills 目录结构

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-001 | 创建 `backend/src/skills/novel/` 目录 | [ ] | TC-P5-SKL-001 |
| P5-SKL-002 | 创建各子目录 (creative, outline, chapter, writer, reviewer, evolution) | [ ] | TC-P5-SKL-002 |

### 5.2 创意孵化 Skill

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-003 | 创建 `creative/SKILL.md` 文件 | [ ] | TC-P5-SKL-003 |
| P5-SKL-004 | 编写创意孵化触发条件 | [ ] | TC-P5-SKL-004 |
| P5-SKL-005 | 编写创意孵化执行步骤 | [ ] | TC-P5-SKL-005 |
| P5-SKL-006 | 编写创意孵化输入输出格式 | [ ] | TC-P5-SKL-006 |
| P5-SKL-007 | 编写创意孵化示例 | [ ] | TC-P5-SKL-007 |

### 5.3 大纲生成 Skill

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-008 | 创建 `outline/SKILL.md` 文件 | [ ] | TC-P5-SKL-008 |
| P5-SKL-009 | 编写大纲生成触发条件 | [ ] | TC-P5-SKL-009 |
| P5-SKL-010 | 编写大纲生成执行步骤 | [ ] | TC-P5-SKL-010 |
| P5-SKL-011 | 编写大纲生成输入输出格式 | [ ] | TC-P5-SKL-011 |
| P5-SKL-012 | 编写大纲生成示例 | [ ] | TC-P5-SKL-012 |

### 5.4 章纲生成 Skill

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-013 | 创建 `chapter/SKILL.md` 文件 | [ ] | TC-P5-SKL-013 |
| P5-SKL-014 | 编写章纲生成触发条件 | [ ] | TC-P5-SKL-014 |
| P5-SKL-015 | 编写章纲生成执行步骤 | [ ] | TC-P5-SKL-015 |
| P5-SKL-016 | 编写章纲生成输入输出格式 | [ ] | TC-P5-SKL-016 |
| P5-SKL-017 | 编写章纲生成示例 | [ ] | TC-P5-SKL-017 |

### 5.5 正文写作 Skill

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-018 | 创建 `writer/SKILL.md` 文件 | [ ] | TC-P5-SKL-018 |
| P5-SKL-019 | 编写正文写作触发条件 | [ ] | TC-P5-SKL-019 |
| P5-SKL-020 | 编写正文写作执行步骤 | [ ] | TC-P5-SKL-020 |
| P5-SKL-021 | 编写正文写作输入输出格式 | [ ] | TC-P5-SKL-021 |
| P5-SKL-022 | 编写正文写作示例 | [ ] | TC-P5-SKL-022 |

### 5.6 质量审查 Skill

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-023 | 创建 `reviewer/SKILL.md` 文件 | [ ] | TC-P5-SKL-023 |
| P5-SKL-024 | 编写质量审查触发条件 | [ ] | TC-P5-SKL-024 |
| P5-SKL-025 | 编写质量检查维度定义 | [ ] | TC-P5-SKL-025 |
| P5-SKL-026 | 编写质量审查执行步骤 | [ ] | TC-P5-SKL-026 |
| P5-SKL-027 | 编写质量审查输入输出格式 | [ ] | TC-P5-SKL-027 |
| P5-SKL-028 | 编写质量审查示例 | [ ] | TC-P5-SKL-028 |

### 5.7 自我进化 Skill

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P5-SKL-029 | 创建 `evolution/SKILL.md` 文件 | [ ] | TC-P5-SKL-029 |
| P5-SKL-030 | 编写自我进化触发条件 | [ ] | TC-P5-SKL-030 |
| P5-SKL-031 | 编写自我进化执行步骤 | [ ] | TC-P5-SKL-031 |
| P5-SKL-032 | 编写自我进化输入输出格式 | [ ] | TC-P5-SKL-032 |
| P5-SKL-033 | 编写自我进化示例 | [ ] | TC-P5-SKL-033 |

---

## 六、Phase 6 - 守护进程服务 (P2)

### 6.1 数据库表结构

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P6-DMN-001 | 创建 `daemon_state` 表 | [ ] | TC-P6-DMN-001 |

### 6.2 守护进程配置与服务

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P6-DMN-002 | 实现 `DaemonConfig` Pydantic 模型 | [ ] | TC-P6-DMN-002 |
| P6-DMN-003 | 创建 `DaemonService` 服务类 | [ ] | TC-P6-DMN-003 |
| P6-DMN-004 | 实现 `start` 启动服务 | [ ] | TC-P6-DMN-004 |
| P6-DMN-005 | 实现 `stop` 停止服务 | [ ] | TC-P6-DMN-005 |
| P6-DMN-006 | 实现 `record_activity` 记录活动 | [ ] | TC-P6-DMN-006 |
| P6-DMN-007 | 实现 `check_idle` 检查空闲 | [ ] | TC-P6-DMN-007 |
| P6-DMN-008 | 实现 `enter_background_mode` 进入后台模式 | [ ] | TC-P6-DMN-008 |
| P6-DMN-009 | 实现 `exit_background_mode` 退出后台模式 | [ ] | TC-P6-DMN-009 |
| P6-DMN-010 | 实现 `get_status` 获取状态 | [ ] | TC-P6-DMN-010 |

### 6.3 后台学习服务

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P6-DMN-011 | 创建 `BackgroundLearning` 服务类 | [ ] | TC-P6-DMN-011 |
| P6-DMN-012 | 实现 `extract_skills_from_history` 从历史提取技能 | [ ] | TC-P6-DMN-012 |
| P6-DMN-013 | 实现 `consolidate_experiences` 整合经验 | [ ] | TC-P6-DMN-013 |
| P6-DMN-014 | 实现 `practice_writing` 写作练习 | [ ] | TC-P6-DMN-014 |
| P6-DMN-015 | 实现 `self_evaluate` 自我评估 | [ ] | TC-P6-DMN-015 |
| P6-DMN-016 | 实现 `compact_memories` 压缩记忆 | [ ] | TC-P6-DMN-016 |
| P6-DMN-017 | 实现 `_find_high_score_sessions` 查找高分会话 | [ ] | TC-P6-DMN-017 |
| P6-DMN-018 | 实现 `_select_work_sample` 选择作品样本 | [ ] | TC-P6-DMN-018 |
| P6-DMN-019 | 实现 `_compare_writings` 对比写作 | [ ] | TC-P6-DMN-019 |

### 6.4 任务调度器

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P6-DMN-020 | 创建 `TaskScheduler` 调度器类 | [ ] | TC-P6-DMN-020 |
| P6-DMN-021 | 实现 `schedule` 调度任务 | [ ] | TC-P6-DMN-021 |
| P6-DMN-022 | 实现 `cancel` 取消任务 | [ ] | TC-P6-DMN-022 |
| P6-DMN-023 | 实现 `run_pending` 运行待执行任务 | [ ] | TC-P6-DMN-023 |
| P6-DMN-024 | 实现 `get_next_run` 获取下次运行时间 | [ ] | TC-P6-DMN-024 |

---

## 七、Phase 7 - 数据访问层 (P0)

### 7.1 DAO 基础

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P7-DAO-001 | 创建 `backend/src/dal/` 目录 | [✓] | TC-P7-DAO-001 |
| P7-DAO-002 | 实现 DAO 基类 `BaseDAO` | [✓] | TC-P7-DAO-002 |

### 7.2 各 DAO 实现

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P7-DAO-003 | 实现 `CompactionIndexDAO` | [✓] | TC-P7-DAO-003 |
| P7-DAO-004 | 实现 `TaskMemoryLinkDAO` | [✓] | TC-P7-DAO-004 |
| P7-DAO-005 | 实现 `SkillDAO` | [✓] | TC-P7-DAO-005 |
| P7-DAO-006 | 实现 `ExperienceDAO` | [✓] | TC-P7-DAO-006 |
| P7-DAO-007 | 实现 `FeedbackDAO` | [✓] | TC-P7-DAO-007 |
| P7-DAO-008 | 实现 `ExpertDAO` | [✓] | TC-P7-DAO-008 |
| P7-DAO-009 | 实现 `NovelProjectDAO` | [✓] | TC-P7-DAO-009 |
| P7-DAO-010 | 实现 `NovelChapterDAO` | [✓] | TC-P7-DAO-010 |

---

## 八、Phase 8 - Web API 层 (P0)

### 8.1 API 框架

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-001 | 创建 `backend/src/api/` 目录 | [ ] | TC-P8-API-001 |
| P8-API-002 | 配置 Hono/FastAPI 路由 | [ ] | TC-P8-API-002 |
| P8-API-003 | 实现请求/响应模型 | [ ] | TC-P8-API-003 |

### 8.2 项目管理 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-004 | 实现 POST `/api/projects` 创建项目 | [ ] | TC-P8-API-004 |
| P8-API-005 | 实现 GET `/api/projects` 列出项目 | [ ] | TC-P8-API-005 |
| P8-API-006 | 实现 GET `/api/projects/:id` 获取项目 | [ ] | TC-P8-API-006 |
| P8-API-007 | 实现 PUT `/api/projects/:id` 更新项目 | [ ] | TC-P8-API-007 |
| P8-API-008 | 实现 DELETE `/api/projects/:id` 删除项目 | [ ] | TC-P8-API-008 |

### 8.3 章节管理 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-009 | 实现 POST `/api/projects/:id/chapters` 创建章节 | [ ] | TC-P8-API-009 |
| P8-API-010 | 实现 GET `/api/projects/:id/chapters` 列出章节 | [ ] | TC-P8-API-010 |

### 8.4 反馈 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-011 | 实现 POST `/api/feedback` 提交反馈 | [ ] | TC-P8-API-011 |

### 8.5 专家 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-012 | 实现 GET `/api/experts` 列出专家 | [ ] | TC-P8-API-012 |
| P8-API-013 | 实现 POST `/api/experts/match` 匹配专家 | [ ] | TC-P8-API-013 |

### 8.6 技能 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-014 | 实现 GET `/api/skills` 列出技能 | [ ] | TC-P8-API-014 |

### 8.7 守护进程 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-015 | 实现 GET `/api/daemon/status` 守护进程状态 | [ ] | TC-P8-API-015 |

### 8.8 聊天 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-016 | 实现 POST `/api/chat` 聊天接口 | [ ] | TC-P8-API-016 |

### 8.9 记忆 API

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P8-API-017 | 实现 GET `/api/memories/search` 记忆搜索 | [ ] | TC-P8-API-017 |
| P8-API-018 | 实现 GET `/api/memories/:id/trace` 记忆追溯 | [ ] | TC-P8-API-018 |

---

## 九、小说项目数据结构

### 9.1 数据库表

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P9-DATA-001 | 创建 `novel_projects` 表 | [ ] | TC-P9-DATA-001 |
| P9-DATA-002 | 创建 `novel_chapters` 表 | [ ] | TC-P9-DATA-002 |

### 9.2 数据目录

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P9-DATA-003 | 创建 `novel-data/` 数据目录结构 | [ ] | TC-P9-DATA-003 |
| P9-DATA-004 | 创建 `novel-data/projects/` 项目目录 | [ ] | TC-P9-DATA-004 |
| P9-DATA-005 | 创建 `novel-data/skills/` 技能目录 | [ ] | TC-P9-DATA-005 |
| P9-DATA-006 | 创建 `novel-data/experiences/` 经验目录 | [ ] | TC-P9-DATA-006 |
| P9-DATA-007 | 创建 `novel-data/memory/` 记忆数据库目录 | [ ] | TC-P9-DATA-007 |

---

## 十、配置与文档

### 10.1 配置文件

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P10-CFG-001 | 扩展 `config.yaml` 添加 novel 配置 | [ ] | TC-P10-CFG-001 |
| P10-CFG-002 | 添加 opencode 配置项 | [ ] | TC-P10-CFG-002 |
| P10-CFG-003 | 添加 daemon 配置项 | [ ] | TC-P10-CFG-003 |
| P10-CFG-004 | 添加 memory 配置项 | [ ] | TC-P10-CFG-004 |
| P10-CFG-005 | 添加 evolution 配置项 | [ ] | TC-P10-CFG-005 |
| P10-CFG-006 | 添加 learning_tasks 配置项 | [ ] | TC-P10-CFG-006 |

### 10.2 文档

| 任务ID | 任务描述 | 状态 | 测试用例ID |
|--------|----------|------|------------|
| P10-DOC-001 | 编写 README.md | [ ] | - |
| P10-DOC-002 | 编写 API 文档 | [ ] | - |
| P10-DOC-003 | 编写配置说明文档 | [ ] | - |
| P10-DOC-004 | 编写部署指南 | [ ] | - |

---

## 十一、任务统计

| Phase | 模块 | 任务数 | 优先级 | 完成状态 |
|-------|------|--------|--------|----------|
| 1 | OpenCode 代理层 | 25 | P0 | ✅ 25/25 |
| 2 | 记忆系统扩展 | 33 | P0 | ✅ 29/33 |
| 3 | 领域专家系统 | 26 | P1 | 0/26 |
| 4 | 自我进化系统 | 28 | P1 | 0/28 |
| 5 | 写作 Skills | 33 | P1 | 0/33 |
| 6 | 守护进程服务 | 24 | P2 | 0/24 |
| 7 | 数据访问层 | 10 | P0 | ✅ 10/10 |
| 8 | Web API 层 | 18 | P0 | 0/18 |
| 9 | 小说数据结构 | 7 | P0 | 0/7 |
| 10 | 配置与文档 | 10 | P1 | 0/10 |

**总任务数: 214** | **已完成: 64** | **进度: 29.9%**

---

## 十二、测试用例映射规范

### 12.1 测试用例 ID 格式

```
TC-{Phase}-{Module}-{Number}
```

例如: `TC-P1-OC-005` 表示 Phase 1 的 OpenCode 模块第 5 个测试用例

### 12.2 测试用例文件结构

```
tests/
├── unit/
│   ├── opencode/
│   │   ├── test_executor.py
│   │   └── test_tasks.py
│   ├── memory/
│   │   ├── test_compaction.py
│   │   ├── test_review.py
│   │   └── test_index_manager.py
│   ├── expert/
│   │   ├── test_registry.py
│   │   └── test_matcher.py
│   ├── evolution/
│   │   ├── test_feedback.py
│   │   ├── test_skill_learner.py
│   │   └── test_optimizer.py
│   └── daemon/
│       ├── test_service.py
│       └── test_learning.py
├── integration/
│   ├── test_opencode_integration.py
│   ├── test_memory_flow.py
│   └── test_evolution_flow.py
└── e2e/
    ├── test_writing_workflow.py
    └── test_feedback_loop.py
```

---

## 十三、里程碑

| 里程碑 | 目标 | 包含 Phase | 预计完成 |
|--------|------|------------|----------|
| M1 | 基础架构 | P1, P7 | 第1周 |
| M2 | 记忆系统 | P2 | 第2周 |
| M3 | 专家+进化 | P3, P4 | 第3-4周 |
| M4 | 写作能力 | P5 | 第5周 |
| M5 | 后台服务 | P6 | 第6周 |
| M6 | API 集成 | P8, P9 | 第7周 |
| M7 | 文档完善 | P10 | 第8周 |

---

**文档结束**
