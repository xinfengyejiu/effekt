# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.planController import PlanController

router = APIRouter(tags=["plan"])


@router.get("/plan/list")
async def plan_list(
    request: Request,
    user: dict = Depends(require_permission("plan:list")),
    db: Session = Depends(get_db),
):
    """计划列表"""
    controller = PlanController(dict(request.query_params))
    try:
        result = controller.plan_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/plan/detail")
async def plan_detail(
    request: Request,
    user: dict = Depends(require_permission("plan:detail")),
    db: Session = Depends(get_db),
):
    """计划详情"""
    controller = PlanController(dict(request.query_params))
    try:
        ret, err_msg = controller.plan_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/plan/create")
async def plan_create(
    request: Request,
    user: dict = Depends(require_permission("plan:create")),
    db: Session = Depends(get_db),
):
    """创建计划"""
    body = await request.json()
    controller = PlanController(body)
    try:
        create_id, err_msg = controller.plan_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/plan/update")
async def plan_update(
    request: Request,
    user: dict = Depends(require_permission("plan:update")),
    db: Session = Depends(get_db),
):
    """更新计划"""
    body = await request.json()
    controller = PlanController(body)
    try:
        update_id, err_msg = controller.plan_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/plan/delete")
async def plan_delete(
    request: Request,
    user: dict = Depends(require_permission("plan:delete")),
    db: Session = Depends(get_db),
):
    """删除计划"""
    body = await request.json()
    controller = PlanController(body)
    try:
        delete_id, err_msg = controller.plan_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.post("/plan/round/create")
async def plan_round_create(
    request: Request,
    user: dict = Depends(require_permission("plan_round:create")),
    db: Session = Depends(get_db),
):
    """创建计划轮次"""
    body = await request.json()
    controller = PlanController(body)
    try:
        create_id, err_msg = controller.round_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.get("/plan/round/list")
async def plan_round_list(
    request: Request,
    user: dict = Depends(require_permission("plan_round:list")),
    db: Session = Depends(get_db),
):
    """计划轮次列表"""
    controller = PlanController(dict(request.query_params))
    try:
        result = controller.round_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/plan/case/add")
async def plan_case_add(
    request: Request,
    user: dict = Depends(require_permission("plan_case:add")),
    db: Session = Depends(get_db),
):
    """计划添加用例"""
    body = await request.json()
    controller = PlanController(body)
    try:
        added_count, err_msg = controller.plan_case_add()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'addedCount': added_count})
    finally:
        controller.close_session()


@router.get("/plan/case/list")
async def plan_case_list(
    request: Request,
    user: dict = Depends(require_permission("plan_case:list")),
    db: Session = Depends(get_db),
):
    """计划用例列表"""
    controller = PlanController(dict(request.query_params))
    try:
        result = controller.plan_case_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/plan/case/execute")
async def plan_case_execute(
    request: Request,
    user: dict = Depends(require_permission("plan_case:execute")),
    db: Session = Depends(get_db),
):
    """执行计划用例"""
    body = await request.json()
    controller = PlanController(body)
    try:
        create_id, err_msg = controller.plan_case_execute()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/plan/case/ai-execute")
async def plan_case_ai_execute(
    request: Request,
    user: dict = Depends(require_permission("plan_case:execute")),
    db: Session = Depends(get_db),
):
    """AI执行计划用例"""
    body = await request.json()
    controller = PlanController(body)
    try:
        ret, err_msg = controller.plan_case_ai_execute()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/plan/progress")
async def plan_progress(
    request: Request,
    user: dict = Depends(require_permission("plan:progress")),
    db: Session = Depends(get_db),
):
    """计划进度"""
    controller = PlanController(dict(request.query_params))
    try:
        ret, err_msg = controller.progress()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()
