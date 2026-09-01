# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiTaskController import AiTaskController

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


@router.post("/ai/task/create")
async def ai_task_create(
    request: Request,
    user: dict = Depends(require_permission("ai_task:create")),
    db: Session = Depends(get_db),
):
    controller = AiTaskController(await request.json())
    return _ai_response(controller, controller.task_create)


@router.get("/ai/task/list")
async def ai_task_list(
    request: Request,
    user: dict = Depends(require_permission("ai_task:list")),
    db: Session = Depends(get_db),
):
    controller = AiTaskController(dict(request.query_params))
    return _ai_response(controller, controller.task_list)


@router.get("/ai/task/detail")
async def ai_task_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_task:detail")),
    db: Session = Depends(get_db),
):
    controller = AiTaskController(dict(request.query_params))
    return _ai_response(controller, controller.task_detail)


@router.post("/ai/task/execute")
async def ai_task_execute(
    request: Request,
    user: dict = Depends(require_permission("ai_task:execute")),
    db: Session = Depends(get_db),
):
    controller = AiTaskController(await request.json())
    return _ai_response(controller, controller.task_execute)


@router.post("/ai/task/cancel")
async def ai_task_cancel(
    request: Request,
    user: dict = Depends(require_permission("ai_task:cancel")),
    db: Session = Depends(get_db),
):
    controller = AiTaskController(await request.json())
    return _ai_response(controller, controller.task_cancel)
