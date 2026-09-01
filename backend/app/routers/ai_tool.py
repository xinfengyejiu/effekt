# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiToolController import AiToolController

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


@router.post("/ai/tool/create")
async def ai_tool_create(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:create")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(await request.json())
    return _ai_response(controller, controller.tool_create)


@router.post("/ai/tool/update")
async def ai_tool_update(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:update")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(await request.json())
    return _ai_response(controller, controller.tool_update)


@router.post("/ai/tool/delete")
async def ai_tool_delete(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:delete")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(await request.json())
    return _ai_response(controller, controller.tool_delete)


@router.get("/ai/tool/list")
async def ai_tool_list(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:list")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(dict(request.query_params))
    return _ai_response(controller, controller.tool_list)


@router.get("/ai/tool/detail")
async def ai_tool_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:detail")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(dict(request.query_params))
    return _ai_response(controller, controller.tool_detail)


@router.post("/ai/tool/execute")
async def ai_tool_execute(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:execute")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(await request.json())
    return _ai_response(controller, controller.tool_execute)


@router.get("/ai/tool/execution/list")
async def ai_tool_execution_list(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:detail")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(dict(request.query_params))
    return _ai_response(controller, controller.execution_list)


@router.get("/ai/tool/execution/detail")
async def ai_tool_execution_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_tool:detail")),
    db: Session = Depends(get_db),
):
    controller = AiToolController(dict(request.query_params))
    return _ai_response(controller, controller.execution_detail)
