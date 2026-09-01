# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiAgentController import AiAgentController

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


@router.post("/ai/agent/create")
async def ai_agent_create(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:create")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(await request.json())
    return _ai_response(controller, controller.agent_create)


@router.post("/ai/agent/update")
async def ai_agent_update(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:update")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(await request.json())
    return _ai_response(controller, controller.agent_update)


@router.post("/ai/agent/delete")
async def ai_agent_delete(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:delete")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(await request.json())
    return _ai_response(controller, controller.agent_delete)


@router.get("/ai/agent/list")
async def ai_agent_list(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:list")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(dict(request.query_params))
    return _ai_response(controller, controller.agent_list)


@router.get("/ai/agent/detail")
async def ai_agent_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:detail")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(dict(request.query_params))
    return _ai_response(controller, controller.agent_detail)


@router.post("/ai/agent/test")
async def ai_agent_test(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:execute")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(await request.json())
    return _ai_response(controller, controller.agent_test)


@router.post("/ai/agent/execute")
async def ai_agent_execute(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:execute")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(await request.json())
    return _ai_response(controller, controller.agent_execute)


@router.get("/ai/agent/execution/list")
async def ai_agent_execution_list(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:detail")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(dict(request.query_params))
    return _ai_response(controller, controller.execution_list)


@router.get("/ai/agent/execution/detail")
async def ai_agent_execution_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_agent:detail")),
    db: Session = Depends(get_db),
):
    controller = AiAgentController(dict(request.query_params))
    return _ai_response(controller, controller.execution_detail)
