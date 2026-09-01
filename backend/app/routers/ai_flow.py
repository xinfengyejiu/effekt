# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiFlowController import AiFlowController

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


@router.post("/ai/flow/create")
async def ai_flow_create(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:create")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(await request.json())
    return _ai_response(controller, controller.flow_create)


@router.post("/ai/flow/update")
async def ai_flow_update(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:update")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(await request.json())
    return _ai_response(controller, controller.flow_update)


@router.post("/ai/flow/delete")
async def ai_flow_delete(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:delete")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(await request.json())
    return _ai_response(controller, controller.flow_delete)


@router.get("/ai/flow/list")
async def ai_flow_list(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:list")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(dict(request.query_params))
    return _ai_response(controller, controller.flow_list)


@router.get("/ai/flow/detail")
async def ai_flow_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:detail")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(dict(request.query_params))
    return _ai_response(controller, controller.flow_detail)


@router.post("/ai/flow/execute")
async def ai_flow_execute(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:execute")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(await request.json())
    return _ai_response(controller, controller.flow_execute)


@router.get("/ai/flow/execution/list")
async def ai_flow_execution_list(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:detail")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(dict(request.query_params))
    return _ai_response(controller, controller.execution_list)


@router.get("/ai/flow/execution/detail")
async def ai_flow_execution_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_flow:detail")),
    db: Session = Depends(get_db),
):
    controller = AiFlowController(dict(request.query_params))
    return _ai_response(controller, controller.execution_detail)
