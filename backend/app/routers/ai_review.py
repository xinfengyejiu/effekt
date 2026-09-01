# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiReviewController import AiReviewController

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


@router.post("/ai/review/create")
async def ai_review_create(
    request: Request,
    user: dict = Depends(require_permission("ai_review:create")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(await request.json())
    return _ai_response(controller, controller.review_create, id_key='reviewId')


@router.get("/ai/review/list")
async def ai_review_list(
    request: Request,
    user: dict = Depends(require_permission("ai_review:list")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(dict(request.query_params))
    return _ai_response(controller, controller.review_list)


@router.get("/ai/review/detail")
async def ai_review_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_review:detail")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(dict(request.query_params))
    return _ai_response(controller, controller.review_detail)


@router.post("/ai/review/execute")
async def ai_review_execute(
    request: Request,
    user: dict = Depends(require_permission("ai_review:execute")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(await request.json())
    return _ai_response(controller, controller.review_execute)


@router.post("/ai/review/confirm")
async def ai_review_confirm(
    request: Request,
    user: dict = Depends(require_permission("ai_review:confirm")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(await request.json())
    return _ai_response(controller, controller.review_confirm, id_key='reviewId')


@router.post("/ai/review/finding/update")
async def ai_review_finding_update(
    request: Request,
    user: dict = Depends(require_permission("ai_review:confirm")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(await request.json())
    return _ai_response(controller, controller.finding_update, id_key='findingId')


@router.post("/ai/review/case/import")
async def ai_review_case_import(
    request: Request,
    user: dict = Depends(require_permission("ai_review:case:import")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(await request.json())
    return _ai_response(controller, controller.case_import, id_key='caseId')


@router.post("/ai/review/case/link")
async def ai_review_case_link(
    request: Request,
    user: dict = Depends(require_permission("ai_review:case:import")),
    db: Session = Depends(get_db),
):
    controller = AiReviewController(await request.json())
    return _ai_response(controller, controller.case_link, id_key='suggestionId')
