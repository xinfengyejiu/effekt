# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.userController import UserController

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/list")
async def user_list(
    request: Request,
    user: dict = Depends(require_permission("user:list")),
    db: Session = Depends(get_db),
):
    """用户列表"""
    controller = UserController(dict(request.query_params))
    try:
        result = controller.user_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/detail")
async def user_detail(
    request: Request,
    user: dict = Depends(require_permission("user:detail")),
    db: Session = Depends(get_db),
):
    """用户详情"""
    controller = UserController(dict(request.query_params))
    try:
        ret, err_msg = controller.user_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/create")
async def user_create(
    request: Request,
    user: dict = Depends(require_permission("user:create")),
    db: Session = Depends(get_db),
):
    """创建用户"""
    body = await request.json()
    controller = UserController(body)
    try:
        create_id, err_msg = controller.user_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/update")
async def user_update(
    request: Request,
    user: dict = Depends(require_permission("user:update")),
    db: Session = Depends(get_db),
):
    """更新用户"""
    body = await request.json()
    controller = UserController(body)
    try:
        update_id, err_msg = controller.user_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/delete")
async def user_delete(
    request: Request,
    user: dict = Depends(require_permission("user:delete")),
    db: Session = Depends(get_db),
):
    """删除用户"""
    body = await request.json()
    controller = UserController(body)
    try:
        delete_id, err_msg = controller.user_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.get("/role/list")
async def user_role_list(
    request: Request,
    user: dict = Depends(require_permission("user_role:list")),
    db: Session = Depends(get_db),
):
    """用户角色列表"""
    controller = UserController(dict(request.query_params))
    try:
        result = controller.user_role_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/role/assign")
async def user_role_assign(
    request: Request,
    user: dict = Depends(require_permission("user_role:assign")),
    db: Session = Depends(get_db),
):
    """分配用户角色"""
    body = await request.json()
    controller = UserController(body)
    try:
        user_id, err_msg = controller.user_role_assign()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'user_id': user_id})
    finally:
        controller.close_session()
