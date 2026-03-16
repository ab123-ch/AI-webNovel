#!/usr/bin/env python
"""
运行时日志测试脚本

测试修复后的代码在运行时的行为，包括：
- FTS5 搜索的降级路径
- Token 估算的降级路径
- CLI 可用性检查

运行方式:
    cd backend
    PYTHONPATH=. python tests/test_runtime_logging.py
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 使用运行时日志配置
from src.utils.logging_config import setup_runtime_logging, get_current_log_path

# 初始化日志系统（每次运行生成新文件）
setup_runtime_logging()

import logging
logger = logging.getLogger(__name__)


def test_fts5_search():
    """测试 FTS5 搜索的运行时日志"""
    print("\n" + "="*70)
    print("测试 1: FTS5 全文搜索")
    print("="*70)

    from src.dal.compaction_dao import CompactionIndexDAO, CompactionIndex
    import time

    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    dao = None
    try:
        dao = CompactionIndexDAO(db_path)

        # 初始化表结构
        conn = dao.get_connection()
        conn.executescript(dao.create_sql)
        conn.commit()

        # 插入测试数据
        test_index = CompactionIndex(
            id="test-001",
            session_id="session-001",
            layer=1,
            source_memory_ids=["m1", "m2"],
            summary="这是一个关于修仙的测试摘要，包含了境界突破的内容",
            key_topics=["修仙", "境界", "突破"],
            key_entities=["主角", "灵气"],
            key_decisions=["选择修炼路线"],
            key_conclusions=["突破成功"],
            original_token_count=100,
            compressed_token_count=50,
            compression_ratio=0.5,
            created_at=int(time.time())
        )
        dao.create(test_index)

        print("\n--- 场景 1.1: 单关键词 LIKE 搜索 ---")
        # 使用 LIKE 查询进行中文搜索
        results = dao.search_fts("修仙", limit=5)
        print(f"搜索'修仙'结果数: {len(results)}")

        print("\n--- 场景 1.2: 多关键词 LIKE 搜索 ---")
        # 插入第二条数据测试多结果返回
        test_index2 = CompactionIndex(
            id="test-002",
            session_id="session-001",
            layer=1,
            source_memory_ids=["m3"],
            summary="修仙者在灵气充裕的山洞中修炼，准备突破到下一个境界",
            key_topics=["修仙", "灵气", "修炼"],
            key_entities=["修仙者"],
            key_decisions=["闭关修炼"],
            key_conclusions=["境界提升"],
            original_token_count=150,
            compressed_token_count=60,
            compression_ratio=0.4,
            created_at=int(time.time())
        )
        dao.create(test_index2)

        # 搜索新数据
        results = dao.search_fts("灵气", limit=5)
        print(f"搜索'灵气'结果数: {len(results)}")

    except Exception as e:
        logger.error(f"FTS5 测试失败: {e}", exc_info=True)
    finally:
        # 关闭连接后再删除文件
        if dao:
            dao.close()
        try:
            os.unlink(db_path)
        except:
            pass


def test_token_estimation():
    """测试 Token 估算的运行时日志"""
    print("\n" + "="*70)
    print("测试 2: Token 估算")
    print("="*70)

    from src.memory.compaction import MemoryCompaction
    from unittest.mock import MagicMock

    # 创建模拟依赖
    mock_tasks = MagicMock()
    mock_dao = MagicMock()
    mock_link_dao = MagicMock()

    compaction = MemoryCompaction(mock_tasks, mock_dao, mock_link_dao)

    test_messages = [
        {"role": "user", "content": "请帮我写一段关于修仙者突破境界的故事情节"},
        {"role": "assistant", "content": "好的，这是一段描述修仙者在灵气充裕的山洞中突破境界的内容..."},
    ]

    print("\n--- 场景 2.1: 消息 Token 估算 ---")
    # 检查 tiktoken 是否可用
    try:
        import tiktoken
        print("tiktoken 已安装，将使用精确计算")
    except ImportError:
        print("tiktoken 未安装，将使用降级估算")

    tokens = compaction._estimate_tokens(test_messages)
    print(f"估算 Token 数: {tokens}")

    print("\n--- 场景 2.2: 文本 Token 估算 ---")
    test_text = "这是一段测试文本，包含中文和 English content，用于测试 token 估算功能。"
    tokens = compaction._estimate_text_tokens(test_text)
    print(f"估算 Token 数: {tokens}")


def test_cli_check():
    """测试 CLI 可用性检查的运行时日志"""
    print("\n" + "="*70)
    print("测试 3: CLI 可用性检查")
    print("="*70)

    import asyncio
    from src.opencode.executor import OpenCodeExecutor

    async def run_check():
        executor = OpenCodeExecutor()

        print("\n--- 场景 3.1: 首次检查 CLI ---")
        result1 = await executor._check_cli_available()
        print(f"CLI 可用: {result1}")

        print("\n--- 场景 3.2: 再次检查 CLI (使用缓存) ---")
        result2 = await executor._check_cli_available()
        print(f"CLI 可用: {result2}")

    asyncio.run(run_check())


def main():
    print("\n" + "#"*70)
    print("#运行时日志测试脚本")
    print("#"*70)

    # 测试 1: FTS5 搜索
    try:
        test_fts5_search()
    except Exception as e:
        logger.error(f"FTS5 测试失败: {e}", exc_info=True)

    # 测试 2: Token 估算
    try:
        test_token_estimation()
    except Exception as e:
        logger.error(f"Token 估算测试失败: {e}", exc_info=True)

    # 测试 3: CLI 检查
    try:
        test_cli_check()
    except Exception as e:
        logger.error(f"CLI 检查测试失败: {e}", exc_info=True)

    print("\n" + "#"*70)
    print("# 测试完成")
    print("#"*70)


if __name__ == "__main__":
    main()
