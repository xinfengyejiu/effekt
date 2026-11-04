# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiCaseQualityController import AiCaseQualityController

router = APIRouter(tags=['ai-case-quality'])


@router.get('/ai-case-quality/summary')
async def ai_case_quality_summary(
    request: Request,
    user: dict = Depends(require_permission('case:list')),
    db: Session = Depends(get_db),
):
    controller = AiCaseQualityController(dict(request.query_params))
    try:
        ret, err = controller.summary()
        if err:
            return api_failure(40011, msg=err)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get('/ai-case-quality/rewritten-list')
async def ai_case_quality_rewritten_list(
    request: Request,
    user: dict = Depends(require_permission('case:list')),
    db: Session = Depends(get_db),
):
    controller = AiCaseQualityController(dict(request.query_params))
    try:
        ret, err = controller.rewritten_list()
        if err:
            return api_failure(40011, msg=err)
        return api_success(data=ret)
    finally:
        controller.close_session()
