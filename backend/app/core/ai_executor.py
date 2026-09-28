# encoding: UTF-8
"""专用 AI / 知识库工作线程池。

FastAPI 路由若是 async，却在事件循环里直接跑同步 LLM / 向量检索 / git+AI，
会堵死整个 worker，导致其它接口一起卡住。

约定：
- 需要「等结果再返回」的 AI 接口：await run_in_ai_executor(...)
- 可后台完成的 AI 步骤：submit_ai_background(...)
"""
from __future__ import unicode_literals

import atexit
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from logger import logger

_MAX_WORKERS = int(os.environ.get('EFFEKT_AI_WORKERS', '4') or 4)
_AI_POOL = ThreadPoolExecutor(max_workers=max(2, _MAX_WORKERS), thread_name_prefix='effekt-ai')


def get_ai_executor():
    return _AI_POOL


async def run_in_ai_executor(func, *args, **kwargs):
    """在专用 AI 线程池中执行同步函数，不阻塞事件循环。"""
    loop = asyncio.get_running_loop()
    if kwargs:
        bound = partial(func, *args, **kwargs)
        return await loop.run_in_executor(_AI_POOL, bound)
    return await loop.run_in_executor(_AI_POOL, func, *args)


def submit_ai_background(func, *args, **kwargs):
    """提交后台 AI 任务（不等待结果）。返回 Future。"""
    if kwargs:
        bound = partial(func, *args, **kwargs)
        future = _AI_POOL.submit(bound)
    else:
        future = _AI_POOL.submit(func, *args)

    def _done(fut):
        try:
            fut.result()
        except Exception as exc:
            logger.exception('后台 AI 任务失败: %s', exc)

    future.add_done_callback(_done)
    return future


def shutdown_ai_executor(wait=False):
    try:
        _AI_POOL.shutdown(wait=wait)
    except Exception:
        pass


atexit.register(shutdown_ai_executor)
