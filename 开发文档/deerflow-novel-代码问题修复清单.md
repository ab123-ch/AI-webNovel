# DeerFlow Novel 代码问题修复清单

> 生成日期: 2026-03-16
> 检查范围: Phase 1 (OpenCode), Phase 2 (Memory), Phase 7 (DAL)

---

## 一、待修复问题

### 1.1 高优先级问题 (P0)

| 问题ID | 文件位置 | 问题描述 | 影响 |
|--------|----------|----------|------|
| FIX-001 | `src/memory/review.py:144` | FTS5 全文搜索未实现，使用简单的 LIKE 搜索替代 | 搜索效率低，无法使用高级搜索功能 |
| FIX-002 | `src/memory/index_manager.py:109` | FTS5 全文搜索未实现，使用简单关键词匹配 | 搜索效率低，无法使用语义搜索 |
| FIX-003 | `src/opencode/executor.py:302` | OpenCode CLI 命令格式未验证 | 可能导致执行失败 |

### 1.2 中优先级问题 (P1)

| 问题ID | 文件位置 | 问题描述 | 影响 |
|--------|----------|----------|------|
| FIX-004 | `src/memory/compaction.py:333-342` | Token 估算方法过于简单（字符/2） | 压缩比例计算不准确 |
| FIX-005 | `src/dal/base.py:57-67` | 数据库连接无连接池管理 | 高并发时可能阻塞 |
| FIX-006 | `src/opencode/executor.py` | 缺少 OpenCode CLI 不存在的错误提示 | 用户难以排查问题 |

### 1.3 低优先级问题 (P2)

| 问题ID | 文件位置 | 问题描述 | 影响 |
|--------|----------|----------|------|
| FIX-007 | `src/memory/linker.py:261` | 相似任务搜索使用全量扫描 | 大数据量时性能下降 |
| FIX-008 | `src/opencode/pool.py:47-56` | `__init__` 方法空实现，仅注释说明单例模式 | 代码可读性差 |
| FIX-009 | `src/dal/database.py:104-144` | FTS5 索引触发器可能不完整 | 更新操作可能不同步 |

---

## 二、问题详情与修复建议

### FIX-001: FTS5 全文搜索未实现 (review.py)

**当前代码**:
```python
# src/memory/review.py:140-146
# TODO: 实现实际的 FTS 搜索
# 目前使用简单的 LIKE 搜索
all_indexes = self.compaction_dao.list(limit=100)
```

**问题**: 使用简单的关键词匹配替代真正的 FTS5 搜索，效率低且功能有限。

**修复建议**:
1. 在 `CompactionIndexDAO` 中添加 FTS5 搜索方法
2. 使用 SQLite FTS5 的 MATCH 语法
3. 支持中文分词（可使用 simple tokenizer 或 jieba）

**修复示例**:
```python
def search_fts(self, query: str, limit: int = 10) -> list[CompactionIndex]:
    """FTS5 全文搜索"""
    conn = self.get_connection()
    sql = """
    SELECT c.* FROM compaction_index c
    JOIN compaction_fts fts ON c.id = fts.id
    WHERE compaction_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """
    cursor = conn.execute(sql, (query, limit))
    return [self._row_to_model(row) for row in cursor.fetchall()]
```

---

### FIX-002: FTS5 全文搜索未实现 (index_manager.py)

**当前代码**:
```python
# src/memory/index_manager.py:109-141
# TODO: 实现真正的 FTS5 搜索
# 目前使用简单的关键词匹配
all_indexes = self.dao.list(limit=200)
```

**问题**: 同 FIX-001，应复用 DAO 层的 FTS 搜索方法。

**修复建议**:
1. 在 `CompactionIndexDAO` 中实现 FTS5 搜索
2. `IndexManager.search_fts()` 直接调用 DAO 方法

---

### FIX-003: OpenCode CLI 命令格式未验证

**当前代码**:
```python
# src/opencode/executor.py:302
cmd = ["opencode", "run", "-m", model, "--non-interactive", prompt]
```

**问题**:
1. 未验证 `opencode` 命令是否存在
2. 未处理 prompt 中的特殊字符
3. 命令格式可能不正确

**修复建议**:
1. 添加 CLI 可用性检查
2. 考虑使用文件传递长 prompt
3. 添加详细的错误信息

**修复示例**:
```python
async def _check_cli_available(self) -> bool:
    """检查 OpenCode CLI 是否可用"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "opencode", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.wait(), timeout=5)
        return proc.returncode == 0
    except Exception:
        return False

async def _run_subprocess(self, prompt: str, model: str) -> str:
    # 检查 CLI
    if not await self._check_cli_available():
        raise OpenCodeError(
            "OpenCode CLI 未安装或不可用。请运行: pip install opencode",
            returncode=-1
        )
    # ... 继续执行
```

---

### FIX-004: Token 估算方法过于简单

**当前代码**:
```python
# src/memory/compaction.py:333-342
def _estimate_tokens(self, messages: list[dict]) -> int:
    """估算消息 token 数"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        # 简单估算：中文约 1.5 字符/token，英文约 4 字符/token
        total += len(content) // 2
    return total
```

**问题**: 简单的字符/2 估算不够准确，中英文混排时误差大。

**修复建议**:
1. 使用 tiktoken 库进行精确计算（推荐）
2. 或实现更智能的估算算法

**修复示例**:
```python
def _estimate_tokens(self, messages: list[dict]) -> int:
    """使用 tiktoken 估算 token 数"""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")  # GPT-4 编码
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            total += len(enc.encode(content))
        return total
    except ImportError:
        # 降级为简单估算
        return self._simple_estimate(messages)

def _simple_estimate(self, messages: list[dict]) -> int:
    """简单 token 估算（降级方案）"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        # 中文字符约 1.5 token，英文约 0.25 token
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        other_chars = len(content) - chinese_chars
        total += int(chinese_chars * 1.5 + other_chars * 0.25)
    return total
```

---

### FIX-005: 数据库连接无连接池管理

**当前代码**:
```python
# src/dal/base.py:57-67
def get_connection(self) -> sqlite3.Connection:
    if self._conn is None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
    return self._conn
```

**问题**: 单连接模式，高并发时可能阻塞。

**修复建议**:
1. 对于 SQLite，使用 WAL 模式和适当的超时
2. 考虑使用连接池（如 aiosqlite）

**修复示例**:
```python
def get_connection(self) -> sqlite3.Connection:
    if self._conn is None:
        self._conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # 增加超时
            check_same_thread=False  # 允许跨线程（配合锁）
        )
        self._conn.row_factory = sqlite3.Row
        # 启用 WAL 模式提高并发
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
    return self._conn
```

---

### FIX-006: 缺少 OpenCode CLI 错误提示

**当前代码**: 见 FIX-003，错误信息不够友好。

**修复建议**: 见 FIX-003 的修复示例。

---

### FIX-007: 相似任务搜索使用全量扫描

**当前代码**:
```python
# src/memory/linker.py:257-275
# 获取所有关联（简单实现）
all_links = self.dao.list(limit=200)
# 筛选前缀匹配的
matched = [...]
```

**问题**: 每次搜索都全量扫描，性能差。

**修复建议**:
1. 在数据库层添加前缀索引
2. 使用 SQL LIKE 查询替代内存筛选

**修复示例**:
```python
# 在 link_dao.py 中添加
def get_by_signature_prefix(self, prefix: str, limit: int = 10) -> list[TaskMemoryLink]:
    """按签名前缀查询"""
    sql = """
    SELECT * FROM task_memory_link
    WHERE task_signature LIKE ?
    ORDER BY relevance_score DESC, recall_count DESC
    LIMIT ?
    """
    conn = self.get_connection()
    cursor = conn.execute(sql, (f"{prefix}%", limit))
    return [self._row_to_model(row) for row in cursor.fetchall()]
```

---

### FIX-008: `__init__` 方法空实现

**当前代码**:
```python
# src/opencode/pool.py:47-56
def __init__(self, config: Optional[OpenCodeConfig] = None):
    """
    初始化连接池
    ...
    """
    # 单例模式下，__init__ 会被多次调用
    # 实际初始化在 __new__ 中完成
    pass
```

**问题**: 代码可读性差，新手可能困惑。

**修复建议**: 使用 `_initialized` 标志替代空 `__init__`。

**修复示例**:
```python
class OpenCodePool:
    _instance: Optional["OpenCodePool"] = None

    def __new__(cls, config: Optional[OpenCodeConfig] = None) -> "OpenCodePool":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, config: Optional[OpenCodeConfig] = None):
        if self._initialized:
            return
        self._executors = {}
        self._config = config or OpenCodeConfig()
        self._initialized = True
        logger.info("[OpenCodePool] 初始化连接池")
```

---

### FIX-009: FTS5 索引触发器不完整

**当前代码**:
```python
# src/dal/database.py:126-141
# 只有 INSERT 和 DELETE 触发器，缺少 UPDATE 触发器
```

**问题**: 更新操作时 FTS 索引不会同步更新。

**修复建议**: 添加 UPDATE 触发器。

**修复示例**:
```python
# 添加更新触发器
conn.execute("""
CREATE TRIGGER IF NOT EXISTS compaction_au AFTER UPDATE ON compaction_index
BEGIN
    INSERT INTO compaction_fts(compaction_fts, rowid, id, summary, key_topics, key_entities)
    VALUES('delete', old.rowid, old.id, old.summary, old.key_topics, old.key_entities);
    INSERT INTO compaction_fts(rowid, id, summary, key_topics, key_entities)
    VALUES (new.rowid, new.id, new.summary, new.key_topics, new.key_entities);
END;
""")
```

---

## 三、统计汇总

| 优先级 | 数量 | 预计修复时间 |
|--------|------|--------------|
| P0 | 3 | 4 小时 |
| P1 | 3 | 3 小时 |
| P2 | 3 | 2 小时 |
| **总计** | **9** | **9 小时** |

---

## 四、修复顺序建议

1. **第一批 (P0)**: FIX-001, FIX-002, FIX-003
   - 核心：FTS5 搜索和 CLI 验证

2. **第二批 (P1)**: FIX-004, FIX-005, FIX-006
   - 改进：Token 估算、连接池、错误提示

3. **第三批 (P2)**: FIX-007, FIX-008, FIX-009
   - 优化：性能和代码质量

---

**文档结束**
