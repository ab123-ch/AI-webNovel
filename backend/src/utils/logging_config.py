"""
运行时日志配置模块

每次运行生成一个新的日志文件，文件名格式：年月日_时分秒_运行日志.log
日志文件存放在工程根目录的 logs/ 目录下

使用方式:
    from src.utils.logging_config import setup_runtime_logging

    # 在程序入口处调用
    setup_runtime_logging()
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    # 当前文件: backend/src/utils/logging_config.py
    # 项目根目录: 向上3级
    return Path(__file__).parent.parent.parent.parent


def get_logs_dir() -> Path:
    """获取日志目录"""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def generate_log_filename() -> str:
    """生成日志文件名：年月日_时分秒_运行日志.log"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_运行日志.log"


def setup_runtime_logging(
    level: int = logging.DEBUG,
    format_string: str = None,
    console_output: bool = True
) -> logging.Logger:
    """
    配置运行时日志

    Args:
        level: 日志级别，默认 DEBUG
        format_string: 自定义格式字符串
        console_output: 是否同时输出到控制台

    Returns:
        根日志记录器

    Example:
        >>> from src.utils.logging_config import setup_runtime_logging
        >>> setup_runtime_logging()
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("这是一条日志")
    """
    # 默认格式
    if format_string is None:
        format_string = (
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )

    # 生成日志文件路径
    logs_dir = get_logs_dir()
    log_filename = generate_log_filename()
    log_filepath = logs_dir / log_filename

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除已有的处理器（避免重复）
    root_logger.handlers.clear()

    # 创建格式器
    formatter = logging.Formatter(
        fmt=format_string,
        datefmt='%H:%M:%S'
    )

    # 1. 文件处理器
    file_handler = logging.FileHandler(
        log_filepath,
        mode='a',
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 2. 控制台处理器（可选）
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 记录日志文件位置
    root_logger.info(f"=" * 70)
    root_logger.info(f"运行时日志系统已初始化")
    root_logger.info(f"日志文件: {log_filepath}")
    root_logger.info(f"日志级别: {logging.getLevelName(level)}")
    root_logger.info(f"=" * 70)

    return root_logger


def get_log_files() -> list[Path]:
    """获取所有日志文件列表"""
    logs_dir = get_logs_dir()
    return sorted(logs_dir.glob("*_运行日志.log"), reverse=True)


def cleanup_old_logs(keep_count: int = 10) -> int:
    """
    清理旧日志文件，只保留最近的 N 个

    Args:
        keep_count: 保留的日志文件数量

    Returns:
        删除的文件数量
    """
    log_files = get_log_files()
    deleted_count = 0

    for log_file in log_files[keep_count:]:
        try:
            log_file.unlink()
            deleted_count += 1
        except Exception:
            pass

    return deleted_count


# 便捷函数：获取当前日志文件路径
def get_current_log_path() -> Path:
    """获取当前会话的日志文件路径（需要在 setup_runtime_logging 之后调用）"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return Path(handler.baseFilename)
    return None
