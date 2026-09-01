# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.skillController import SkillController

router = APIRouter(tags=["skill"])


# ==================== Skill routes ====================

@router.post("/skill/create")
async def skill_create(
    request: Request,
    user: dict = Depends(require_permission("skill:create")),
    db: Session = Depends(get_db),
):
    """创建技能"""
    body = await request.json()
    controller = SkillController(body)
    try:
        create_id, err_msg = controller.skill_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/skill/update")
async def skill_update(
    request: Request,
    user: dict = Depends(require_permission("skill:update")),
    db: Session = Depends(get_db),
):
    """更新技能"""
    body = await request.json()
    controller = SkillController(body)
    try:
        update_id, err_msg = controller.skill_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/skill/delete")
async def skill_delete(
    request: Request,
    user: dict = Depends(require_permission("skill:delete")),
    db: Session = Depends(get_db),
):
    """删除技能"""
    body = await request.json()
    controller = SkillController(body)
    try:
        delete_id, err_msg = controller.skill_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.get("/skill/detail")
async def skill_detail(
    request: Request,
    user: dict = Depends(require_permission("skill:detail")),
    db: Session = Depends(get_db),
):
    """技能详情"""
    controller = SkillController(dict(request.query_params))
    try:
        ret, err_msg = controller.skill_detail()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/skill/list")
async def skill_list(
    request: Request,
    user: dict = Depends(require_permission("skill:list")),
    db: Session = Depends(get_db),
):
    """技能列表"""
    controller = SkillController(dict(request.query_params))
    try:
        result = controller.skill_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/skill-rule/list")
async def skill_rule_list(
    request: Request,
    user: dict = Depends(require_permission("skill:list")),
    db: Session = Depends(get_db),
):
    """技能规则列表"""
    controller = SkillController(dict(request.query_params))
    try:
        ret, err_msg = controller.skill_rule_list()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


# ==================== Business Rule routes ====================

@router.post("/business-rule/create")
async def business_rule_create(
    request: Request,
    user: dict = Depends(require_permission("business-rule:create")),
    db: Session = Depends(get_db),
):
    """创建业务规则"""
    body = await request.json()
    controller = SkillController(body)
    try:
        create_id, err_msg = controller.business_rule_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/business-rule/update")
async def business_rule_update(
    request: Request,
    user: dict = Depends(require_permission("business-rule:update")),
    db: Session = Depends(get_db),
):
    """更新业务规则"""
    body = await request.json()
    controller = SkillController(body)
    try:
        update_id, err_msg = controller.business_rule_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/business-rule/delete")
async def business_rule_delete(
    request: Request,
    user: dict = Depends(require_permission("business-rule:delete")),
    db: Session = Depends(get_db),
):
    """删除业务规则"""
    body = await request.json()
    controller = SkillController(body)
    try:
        delete_id, err_msg = controller.business_rule_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.get("/business-rule/detail")
async def business_rule_detail(
    request: Request,
    user: dict = Depends(require_permission("business-rule:detail")),
    db: Session = Depends(get_db),
):
    """业务规则详情"""
    controller = SkillController(dict(request.query_params))
    try:
        ret, err_msg = controller.business_rule_detail()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/business-rule/list")
async def business_rule_list(
    request: Request,
    user: dict = Depends(require_permission("business-rule:list")),
    db: Session = Depends(get_db),
):
    """业务规则列表"""
    controller = SkillController(dict(request.query_params))
    try:
        result = controller.business_rule_list()
        return api_success(data=result)
    finally:
        controller.close_session()
