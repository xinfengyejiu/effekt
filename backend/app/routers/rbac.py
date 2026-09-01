# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission, get_current_user
from app.core.response import api_success, api_failure
from app.api.controller.rbacController import RbacController

router = APIRouter(tags=["rbac"])


# ==================== Role CRUD ====================

@router.get("/role/list")
async def role_list(
    request: Request,
    user: dict = Depends(require_permission("role:list")),
    db: Session = Depends(get_db),
):
    """角色列表"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.role_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/role/page/list")
async def role_page_list(
    request: Request,
    user: dict = Depends(require_permission("role:list")),
    db: Session = Depends(get_db),
):
    """角色分页列表"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.role_page_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/role/detail")
async def role_detail(
    request: Request,
    user: dict = Depends(require_permission("role:detail")),
    db: Session = Depends(get_db),
):
    """角色详情"""
    controller = RbacController(dict(request.query_params))
    try:
        ret, err_msg = controller.role_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/role/create")
async def role_create(
    request: Request,
    user: dict = Depends(require_permission("role:create")),
    db: Session = Depends(get_db),
):
    """创建角色"""
    body = await request.json()
    controller = RbacController(body)
    try:
        create_id, err_msg = controller.role_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/role/update")
async def role_update(
    request: Request,
    user: dict = Depends(require_permission("role:update")),
    db: Session = Depends(get_db),
):
    """更新角色"""
    body = await request.json()
    controller = RbacController(body)
    try:
        update_id, err_msg = controller.role_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/role/delete")
async def role_delete(
    request: Request,
    user: dict = Depends(require_permission("role:delete")),
    db: Session = Depends(get_db),
):
    """删除角色"""
    body = await request.json()
    controller = RbacController(body)
    try:
        delete_id, err_msg = controller.role_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


# ==================== Permission CRUD ====================

@router.get("/permission/list")
async def permission_list(
    request: Request,
    user: dict = Depends(require_permission("permission:list")),
    db: Session = Depends(get_db),
):
    """权限列表"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.permission_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/permission/detail")
async def permission_detail(
    request: Request,
    user: dict = Depends(require_permission("permission:detail")),
    db: Session = Depends(get_db),
):
    """权限详情"""
    controller = RbacController(dict(request.query_params))
    try:
        ret, err_msg = controller.permission_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/permission/create")
async def permission_create(
    request: Request,
    user: dict = Depends(require_permission("permission:create")),
    db: Session = Depends(get_db),
):
    """创建权限"""
    body = await request.json()
    controller = RbacController(body)
    try:
        create_id, err_msg = controller.permission_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/permission/update")
async def permission_update(
    request: Request,
    user: dict = Depends(require_permission("permission:update")),
    db: Session = Depends(get_db),
):
    """更新权限"""
    body = await request.json()
    controller = RbacController(body)
    try:
        update_id, err_msg = controller.permission_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/permission/delete")
async def permission_delete(
    request: Request,
    user: dict = Depends(require_permission("permission:delete")),
    db: Session = Depends(get_db),
):
    """删除权限"""
    body = await request.json()
    controller = RbacController(body)
    try:
        delete_id, err_msg = controller.permission_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


# ==================== Menu CRUD ====================

@router.get("/menu/tree")
async def menu_tree(
    request: Request,
    user: dict = Depends(require_permission("menu:list")),
    db: Session = Depends(get_db),
):
    """菜单树"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.menu_tree()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/menu/current/list")
async def current_menu_list(
    request: Request,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户菜单列表"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.current_menu_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/role/menu/tree")
async def role_menu_tree(
    request: Request,
    user: dict = Depends(require_permission("role_menu:list")),
    db: Session = Depends(get_db),
):
    """角色菜单树"""
    controller = RbacController(dict(request.query_params))
    try:
        ret, err_msg = controller.role_menu_tree()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/menu/detail")
async def menu_detail(
    request: Request,
    user: dict = Depends(require_permission("menu:detail")),
    db: Session = Depends(get_db),
):
    """菜单详情"""
    controller = RbacController(dict(request.query_params))
    try:
        ret, err_msg = controller.menu_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/menu/create")
async def menu_create(
    request: Request,
    user: dict = Depends(require_permission("menu:create")),
    db: Session = Depends(get_db),
):
    """创建菜单"""
    body = await request.json()
    controller = RbacController(body)
    try:
        create_id, err_msg = controller.menu_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/menu/update")
async def menu_update(
    request: Request,
    user: dict = Depends(require_permission("menu:update")),
    db: Session = Depends(get_db),
):
    """更新菜单"""
    body = await request.json()
    controller = RbacController(body)
    try:
        update_id, err_msg = controller.menu_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/menu/delete")
async def menu_delete(
    request: Request,
    user: dict = Depends(require_permission("menu:delete")),
    db: Session = Depends(get_db),
):
    """删除菜单"""
    body = await request.json()
    controller = RbacController(body)
    try:
        delete_id, err_msg = controller.menu_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


# ==================== Role-Permission Assignment ====================

@router.get("/role/permission/list")
async def role_permission_list(
    request: Request,
    user: dict = Depends(require_permission("role_permission:list")),
    db: Session = Depends(get_db),
):
    """角色权限列表"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.role_permission_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/role/permission/assign")
async def role_permission_assign(
    request: Request,
    user: dict = Depends(require_permission("role_permission:assign")),
    db: Session = Depends(get_db),
):
    """分配角色权限"""
    body = await request.json()
    controller = RbacController(body)
    try:
        create_id, err_msg = controller.role_permission_assign()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


# ==================== Role-Menu Assignment ====================

@router.get("/role/menu/list")
async def role_menu_list(
    request: Request,
    user: dict = Depends(require_permission("role_menu:list")),
    db: Session = Depends(get_db),
):
    """角色菜单列表"""
    controller = RbacController(dict(request.query_params))
    try:
        result = controller.role_menu_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/role/menu/assign")
async def role_menu_assign(
    request: Request,
    user: dict = Depends(require_permission("role_menu:assign")),
    db: Session = Depends(get_db),
):
    """分配角色菜单"""
    body = await request.json()
    controller = RbacController(body)
    try:
        create_id, err_msg = controller.role_menu_assign()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()
