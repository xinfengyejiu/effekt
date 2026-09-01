# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiMcpController import AiMcpController

router = APIRouter()


def _ai_response(controller, action, id_key='id'):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return api_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return api_success(data={id_key: ret})
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/ai/mcp/create")
async def ai_mcp_create(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:create")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(await request.json())
    return _ai_response(controller, controller.mcp_create)


@router.post("/ai/mcp/update")
async def ai_mcp_update(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:update")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(await request.json())
    return _ai_response(controller, controller.mcp_update)


@router.post("/ai/mcp/delete")
async def ai_mcp_delete(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:delete")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(await request.json())
    return _ai_response(controller, controller.mcp_delete)


@router.get("/ai/mcp/list")
async def ai_mcp_list(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:list")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(dict(request.query_params))
    return _ai_response(controller, controller.mcp_list)


@router.get("/ai/mcp/detail")
async def ai_mcp_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:detail")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(dict(request.query_params))
    return _ai_response(controller, controller.mcp_detail)


@router.post("/ai/mcp/test")
async def ai_mcp_test(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:call")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(await request.json())
    return _ai_response(controller, controller.mcp_test)


@router.post("/ai/mcp/call")
async def ai_mcp_call(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:call")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(await request.json())
    return _ai_response(controller, controller.mcp_call)


@router.get("/ai/mcp/call/log/list")
async def ai_mcp_call_log_list(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:detail")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(dict(request.query_params))
    return _ai_response(controller, controller.call_log_list)


@router.get("/ai/mcp/call/log/detail")
async def ai_mcp_call_log_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_mcp:detail")),
    db: Session = Depends(get_db),
):
    controller = AiMcpController(dict(request.query_params))
    return _ai_response(controller, controller.call_log_detail)
