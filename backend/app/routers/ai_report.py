# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiReportController import AiReportController

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


@router.post("/ai/report/create")
async def ai_report_create(
    request: Request,
    user: dict = Depends(require_permission("ai_report:create")),
    db: Session = Depends(get_db),
):
    controller = AiReportController(await request.json())
    return _ai_response(controller, controller.report_create)


@router.get("/ai/report/list")
async def ai_report_list(
    request: Request,
    user: dict = Depends(require_permission("ai_report:list")),
    db: Session = Depends(get_db),
):
    controller = AiReportController(dict(request.query_params))
    return _ai_response(controller, controller.report_list)


@router.get("/ai/report/detail")
async def ai_report_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_report:detail")),
    db: Session = Depends(get_db),
):
    controller = AiReportController(dict(request.query_params))
    return _ai_response(controller, controller.report_detail)
