"""OpenCode 执行器模块

所有 LLM 调用通过 OpenCode CLI 代理层
"""

import asyncio
import functools
import logging
import os
import subprocess
import uuid
from typing import Optional

from .config import OpenCodeConfig

logger = logging.getLogger(__name__)


class OpenCodeError(Exception):
    """OpenCode 执行错误"""

    def __init__(self, message: str, returncode: int = 1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class OpenCodeExecutor:
    """
    OpenCode 执行器 - 所有 LLM 调用的代理层

    职责：
    - 执行 OpenCode CLI 命令
    - 管理模型切换
    - 处理超时和重试
    - 批量并行执行
    - 带确认的多轮执行

    Example:
        >>> config = OpenCodeConfig(model="glm-4.7")
        >>> executor = OpenCodeExecutor(config)
        >>> result = await executor.execute("帮我写一个修仙小说的开头")
    """

    def __init__(self, config: Optional[OpenCodeConfig] = None):
        """
        初始化执行器

        Args:
            config: OpenCode 配置，为空则使用默认配置
        """
        self.cfg = config or OpenCodeConfig()
        self._id = str(uuid.uuid4())[:8]
        logger.info(f"[OpenCodeExecutor:{self._id}] 初始化完成, model={self.cfg.model}")

    async def execute(
        self,
        task: str,
        context: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        执行 OpenCode 任务

        Args:
            task: 任务描述，非空
            context: 上下文信息，可选
            model: 指定模型，可选，默认使用配置中的模型

        Returns:
            执行结果字符串

        Raises:
            ValueError: task 为空
            OpenCodeError: OpenCode 执行失败
            TimeoutError: 执行超时

        Example:
            >>> result = await executor.execute("分析这段文字的主题", context="...")
            >>> print(result)
        """
        if not task or not task.strip():
            raise ValueError("task cannot be empty")

        prompt = self._build_prompt(task, context)
        mdl = model or self.cfg.model

        logger.debug(f"[OpenCodeExecutor:{self._id}] 执行任务, model={mdl}, task_len={len(task)}")

        return await self._run_with_retry(prompt, mdl)

    async def execute_with_confirmation(
        self,
        task: str,
        context: str,
        criteria: list[str],
        max_rounds: int = 2
    ) -> tuple[str, bool, int]:
        """
        带确认的执行 - 多轮确认直到满意

        Args:
            task: 任务描述
            context: 上下文
            criteria: 确认标准列表
            max_rounds: 最大确认轮数，默认 2

        Returns:
            (结果, 是否确认, 轮数)

        Example:
            >>> result, confirmed, rounds = await executor.execute_with_confirmation(
            ...     "生成一个创意点子",
            ...     "修仙小说背景",
            ...     ["创意新颖", "可扩展性好"]
            ... )
        """
        # 执行初始任务
        current_result = await self.execute(task, context)
        rounds = 0
        confirmed = False

        while rounds < max_rounds:
            # 构建确认提示词
            confirm_prompt = self._build_confirmation_prompt(
                task, criteria, current_result
            )

            # 请求确认
            response = await self.execute(confirm_prompt)

            if response.strip().startswith("CONFIRMED:"):
                confirmed = True
                # 提取最终结果
                current_result = response.strip()[10:].strip()
                break
            elif response.strip().startswith("REVISION:"):
                # 更新结果
                current_result = response.strip()[9:].strip()
                rounds += 1
            else:
                # 无法解析，视为需要继续改进
                current_result = response
                rounds += 1

        return current_result, confirmed, rounds

    async def execute_batch(
        self,
        tasks: list[dict],
        max_concurrent: int = 3
    ) -> list[str]:
        """
        批量执行任务（并行）

        Args:
            tasks: 任务列表，每个任务包含 task 和可选的 context
            max_concurrent: 最大并发数，默认 3

        Returns:
            结果列表，与输入任务顺序对应

        Example:
            >>> results = await executor.execute_batch([
            ...     {"task": "任务1"},
            ...     {"task": "任务2", "context": "上下文"}
            ... ])
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(task_item: dict) -> str:
            async with semaphore:
                return await self.execute(
                    task_item["task"],
                    task_item.get("context")
                )

        coros = [run_with_semaphore(t) for t in tasks]
        return await asyncio.gather(*coros)

    def set_model(self, model: str) -> None:
        """
        切换模型

        Args:
            model: 模型名称

        Raises:
            ValueError: 模型不在可用列表中
        """
        if model not in self.cfg.models:
            raise ValueError(
                f"模型 {model} 不可用，可用模型: {self.cfg.models}"
            )
        self.cfg.model = model
        logger.info(f"[OpenCodeExecutor:{self._id}] 切换模型到 {model}")

    def _build_prompt(self, task: str, context: Optional[str] = None) -> str:
        """
        构建完整提示词

        Args:
            task: 任务描述
            context: 上下文

        Returns:
            完整提示词字符串
        """
        if context:
            return f"上下文：\n{context}\n\n任务：\n{task}"
        return task

    def _build_confirmation_prompt(
        self,
        task: str,
        criteria: list[str],
        current_result: str
    ) -> str:
        """
        构建确认提示词

        Args:
            task: 原始任务
            criteria: 确认标准
            current_result: 当前结果

        Returns:
            确认提示词
        """
        criteria_str = "\n".join(f"- {c}" for c in criteria)
        return f"""请评估以下结果是否满足要求：

原始任务：
{task}

确认标准：
{criteria_str}

当前结果：
{current_result}

如果结果满足所有标准，请以 "CONFIRMED:" 开头回复最终结果。
如果需要改进，请以 "REVISION:" 开头提供改进后的结果。

你的回复："""

    async def _run_with_retry(self, prompt: str, model: str) -> str:
        """
        带重试的执行

        Args:
            prompt: 完整提示词
            model: 模型名称

        Returns:
            执行结果

        Raises:
            OpenCodeError: 重试后仍失败
            TimeoutError: 执行超时
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.cfg.max_retries + 1):
            try:
                return await self._run_subprocess(prompt, model)
            except TimeoutError:
                last_error = TimeoutError(
                    f"OpenCode 执行超时 ({self.cfg.timeout}s)"
                )
                logger.warning(
                    f"[OpenCodeExecutor:{self._id}] "
                    f"超时，重试 {attempt + 1}/{self.cfg.max_retries}"
                )
            except OpenCodeError as e:
                last_error = e
                logger.warning(
                    f"[OpenCodeExecutor:{self._id}] "
                    f"执行失败: {e.stderr}, 重试 {attempt + 1}/{self.cfg.max_retries}"
                )

            if attempt < self.cfg.max_retries:
                await asyncio.sleep(1 * (attempt + 1))

        raise last_error or OpenCodeError("未知错误")

    async def _run_subprocess(self, prompt: str, model: str) -> str:
        """
        执行子进程调用 OpenCode CLI

        Args:
            prompt: 完整提示词
            model: 模型名称

        Returns:
            stdout 内容

        Raises:
            OpenCodeError: 执行失败
            TimeoutError: 执行超时
        """
        cmd = ["opencode", "run", "-m", model, "--non-interactive", prompt]

        cwd = self.cfg.working_dir or os.getcwd()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.cfg.timeout
            )

            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8", errors="replace")
                raise OpenCodeError(
                    f"OpenCode 执行失败: {err_msg}",
                    returncode=proc.returncode,
                    stderr=err_msg
                )

            return stdout.decode("utf-8", errors="replace")

        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise TimeoutError(
                f"OpenCode 执行超时 ({self.cfg.timeout}s)"
            ) from exc


def with_retry(max_retries: int = 3, delay: float = 1.0):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒），每次翻倍

    Example:
        >>> @with_retry(max_retries=3, delay=1.0)
        ... async def my_task():
        ...     pass
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error: Optional[Exception] = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
            raise last_error or RuntimeError("未知错误")
        return wrapper
    return decorator
