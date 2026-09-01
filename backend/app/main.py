# encoding: UTF-8
"""
FastAPI 主入口文件
"""
from contextlib import asynccontextmanager
from contextvars import ContextVar
from itertools import count
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from flask import Flask
from flask.globals import _app_ctx_stack, _request_ctx_stack
import os

from logger import logger
from app.core.config import BE_URL


# Flask 1.x / Werkzeug 1.x 默认用线程 ID 存 Local 栈。
# uvicorn 同线程并发处理多个 ASGI 请求时会互相 pop 错上下文。
# 改为按 asyncio Task 的 ContextVar 隔离，保证 push/pop 成对。
_flask_async_ident_var: ContextVar = ContextVar('effekt_flask_async_ident')
_flask_async_ident_seq = count(1)


def _flask_async_ident():
    ident = _flask_async_ident_var.get(None)
    if ident is None:
        ident = next(_flask_async_ident_seq)
        _flask_async_ident_var.set(ident)
    return ident


_app_ctx_stack.__ident_func__ = _flask_async_ident
_request_ctx_stack.__ident_func__ = _flask_async_ident


# 迁移期间部分旧控制器仍依赖 Flask 的 g/current_app。
legacy_flask_app = Flask("effekt_interface_legacy_context")


class LegacyFlaskContextMiddleware:
    """在同一 ASGI 调用链中成对管理 Flask application context。"""

    def __init__(self, app, flask_app):
        self.app = app
        self.flask_app = flask_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        # 每个请求 Task 先分配独立 ident，再 push 上下文
        _flask_async_ident_var.set(next(_flask_async_ident_seq))
        ctx = self.flask_app.app_context()
        ctx.push()
        try:
            await self.app(scope, receive, send)
        finally:
            ctx.pop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("FastAPI app starting...")
    # 启动巡检调度器
    try:
        from app.core.inspectionScheduler import inspection_scheduler
        inspection_scheduler.start()
    except Exception as e:
        logger.warning("巡检调度器启动失败（非致命）: %s", str(e))
    yield
    logger.info("FastAPI app shutting down...")
    # 停止巡检调度器
    try:
        from app.core.inspectionScheduler import inspection_scheduler
        inspection_scheduler.stop()
    except Exception:
        pass


# 创建 FastAPI 应用
app = FastAPI(
    title="Effekt Interface App",
    version="1.0.0",
    description="Effekt Interface App API (FastAPI)",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LegacyFlaskContextMiddleware, flask_app=legacy_flask_app)


# 静态文件服务（上传的文件）
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'attachment', 'bug_picture')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if os.path.exists(UPLOAD_FOLDER):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": 50000,
            "message": f"服务器内部错误: {str(exc)}",
            "data": {}
        }
    )


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "FastAPI is running"}


# 注册所有路由
from app.routers import (
    auth, user, project, product, case, plan, bug, document,
    rbac, automation, performance, mobile_automation, mock, precise,
    skill, knowledge, report, data_builder, test_asset, sql_project,
    ai_agent, ai_tool, ai_mcp, ai_flow, ai_task, ai_report,
    ai_review, ai_workload_estimate, inspection,
)

_API_PREFIX = "/it/api"

app.include_router(auth.router, prefix=_API_PREFIX)
app.include_router(user.router, prefix=_API_PREFIX)
app.include_router(project.router, prefix=_API_PREFIX)
app.include_router(product.router, prefix=_API_PREFIX)
app.include_router(case.router, prefix=_API_PREFIX)
app.include_router(plan.router, prefix=_API_PREFIX)
app.include_router(bug.router, prefix=_API_PREFIX)
app.include_router(document.router, prefix=_API_PREFIX)
app.include_router(rbac.router, prefix=_API_PREFIX)
app.include_router(automation.router, prefix=_API_PREFIX)
app.include_router(performance.router, prefix=_API_PREFIX)
app.include_router(mobile_automation.router, prefix=_API_PREFIX)
app.include_router(mock.router, prefix=_API_PREFIX)
app.include_router(precise.router, prefix=_API_PREFIX)
app.include_router(skill.router, prefix=_API_PREFIX)
app.include_router(knowledge.router, prefix=_API_PREFIX)
app.include_router(report.router, prefix=_API_PREFIX)
app.include_router(data_builder.router, prefix=_API_PREFIX)
app.include_router(test_asset.router, prefix=_API_PREFIX)
app.include_router(sql_project.router, prefix=_API_PREFIX)
app.include_router(ai_agent.router, prefix=_API_PREFIX)
app.include_router(ai_tool.router, prefix=_API_PREFIX)
app.include_router(ai_mcp.router, prefix=_API_PREFIX)
app.include_router(ai_flow.router, prefix=_API_PREFIX)
app.include_router(ai_task.router, prefix=_API_PREFIX)
app.include_router(ai_report.router, prefix=_API_PREFIX)
app.include_router(ai_review.router, prefix=_API_PREFIX)
app.include_router(ai_workload_estimate.router, prefix=_API_PREFIX)
app.include_router(inspection.router, prefix=_API_PREFIX)


if __name__ == "__main__":
    import uvicorn
    host, port = BE_URL.split(":")
    uvicorn.run(app, host=host, port=int(port), reload=False)
