# DeerFlow Novel 代码修复日志

> 修复日期: 2026-03-16
> 修复人: Claude (AI 记忆优化专家)
> 检查范围: Phase 1 (OpenCode), Phase 2 (Memory), Phase 7 (DAL)

---

## 零、运行时日志示例

以下是从实际运行中捕获的日志，展示了降级路径和执行流程。

### 0.1 FTS5 搜索 - 表不存在降级

```
21:26:06 | INFO     | src.dal.compaction_dao | [CompactionIndexDAO] 开始 FTS5 搜索: query='修仙', limit=5
21:26:06 | DEBUG    | src.dal.compaction_dao | [CompactionIndexDAO] 步骤1: 检查 compaction_fts 表是否存在
21:26:06 | WARNING  | src.dal.compaction_dao | [CompactionIndexDAO][降级] FTS5 表不存在 | 原因: 表 'compaction_fts' 未初始化 | 降级方案: _fallback_search() | 耗时: 0.000s
21:26:06 | INFO     | src.dal.compaction_dao | [CompactionIndexDAO][降级搜索] 开始内存匹配搜索: query='修仙'
21:26:06 | INFO     | src.dal.compaction_dao | [CompactionIndexDAO][降级搜索] 完成 | 候选数量: 1 | 匹配数量: 1 | 返回数量: 1 | 耗时: 0.000s
```

### 0.2 FTS5 搜索 - 中文分词降级（重要！）

```
21:26:06 | INFO     | src.dal.compaction_dao | [CompactionIndexDAO] 开始 FTS5 搜索: query='修仙', limit=5
21:26:06 | DEBUG    | src.dal.compaction_dao | [CompactionIndexDAO] 步骤1: 检查 compaction_fts 表是否存在
21:26:06 | DEBUG    | src.dal.compaction_dao | [CompactionIndexDAO] 步骤1完成: FTS5 表存在
21:26:06 | DEBUG    | src.dal.compaction_dao | [CompactionIndexDAO] 步骤2: 构建 FTS 查询 '修仙'
21:26:06 | DEBUG    | src.dal.compaction_dao | [CompactionIndexDAO] 步骤3: 执行 FTS5 SQL 查询
21:26:06 | DEBUG    | src.dal.compaction_dao | [CompactionIndexDAO] FTS5 无结果，可能原因：中文分词不支持
21:26:06 | WARNING  | src.dal.compaction_dao | [CompactionIndexDAO][降级] FTS5 返回 0 条结果 | 原因: 可能是中文分词器不支持| 降级方案: _fallback_search() | 耗时: 0.000s
21:26:06 | INFO     | src.dal.compaction_dao | [CompactionIndexDAO][降级搜索] 完成 | 候选数量: 1 | 匹配数量: 1 | 返回数量: 1
```

**重要说明**: SQLite FTS5 默认使用 unicode61 分词器，**不支持中文分词**。当搜索中文关键词时，FTS5 MATCH 查询会返回 0 条结果，此时系统会自动降级到内存匹配搜索。

### 0.3 Token 估算 - tiktoken 路径

```
21:26:06 | DEBUG    | src.memory.compaction | [MemoryCompaction] 开始估算 token 数量，消息数: 2
21:26:06 | DEBUG    | src.memory.compaction | [MemoryCompaction] 使用 tiktoken 进行精确计算
21:26:07 | INFO     | src.memory.compaction | [MemoryCompaction][tiktoken] Token 估算完成 | 消息数: 2 | 总 token: 64 | 耗时: 0.087s
```

### 0.4 CLI 可用性检查 - 失败路径

```
21:26:07 | INFO     | src.opencode.executor | [OpenCodeExecutor] 开始检查 CLI 可用性...
21:26:07 | ERROR    | src.opencode.executor | [OpenCodeExecutor][错误] opencode 命令未找到 | 错误类型: FileNotFoundError | 错误信息: [WinError 2] 系统找不到指定的文件。 | 解决方案: pip install opencode | 耗时: 0.002s
```

### 0.5 CLI 可用性检查 - 缓存命中

```
21:26:07 | DEBUG    | src.opencode.executor | [OpenCodeExecutor][缓存] CLI 可用性已检查 | 结果: 不可用
```

---

## 一、修复概览

| 优先级 | 问题数 | 状态 |
|--------|--------|------|
| P0 | 3 | ✅ 已完成 |
| P1 | 3 | ✅ 已完成 |
| P2 | 3 | ✅ 已完成 |
| **总计** | **9** | **✅ 全部完成** |

---

## 二、关键发现：中文分词问题

### 问题描述

SQLite FTS5 默认分词器 `unicode61` **不支持中文分词**。当搜索中文关键词时，`MATCH` 查询无法正确匹配。

### 解决方案

实现了**自动降级机制**：

```
FTS5 搜索流程:
1. 检查 FTS 表是否存在 → 不存在则降级
2. 执行 FTS5 MATCH 查询
3. 如果返回 0 条结果 → 自动降级到内存匹配
4. 内存匹配使用 LIKE 查询 + 关键词匹配
```

### 日志标识

```
[CompactionIndexDAO][降级] FTS5 返回 0 条结果 | 原因: 可能是中文分词器不支持
```

---

## 三、降级方案汇总

| 功能 | 降级条件 | 降级方案 | 日志标识 |
|------|----------|----------|----------|
| FTS5 搜索 | FTS 表不存在 | `_fallback_search()` | `[降级]` |
| FTS5 搜索 | 中文分词不支持（返回0条） | `_fallback_search()` | `[降级]` |
| Token 估算 | tiktoken 未安装 | `_smart_estimate_messages()` | `[降级]` |
| CLI 检查 | 命令未找到 | 抛出友好错误提示 | `[错误]` |

---

## 四、测试验证

### 测试结果

```
--- 场景 1.1: FTS5 表不存在时的降级搜索 ---
搜索结果数: 1

--- 场景 1.2: FTS5 表存在后的搜索 ---
搜索结果数: 1
搜索'灵气'结果数: 2
```

### 测试命令

```bash
cd backend && PYTHONPATH=. python tests/test_runtime_logging.py
```

---

## 五、后续建议

1. **FTS5 中文分词**: 集成 jieba 分词器，或使用 SQLite 的 `simple` tokenizer
2. **tiktoken 依赖**: 添加为可选依赖
3. **连接池**: 考虑使用 aiosqlite

---

**文档结束**
