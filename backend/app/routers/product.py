# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.productController import ProductController
from app.api.controller.caseController import CaseController

router = APIRouter(tags=["product"])


# ==================== ProductController routes ====================

@router.get("/product/list")
async def product_list(
    request: Request,
    user: dict = Depends(require_permission("product:list")),
    db: Session = Depends(get_db),
):
    """产品列表"""
    controller = ProductController(dict(request.query_params))
    try:
        result = controller.product_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/product/detail")
async def product_detail(
    request: Request,
    user: dict = Depends(require_permission("product:detail")),
    db: Session = Depends(get_db),
):
    """产品详情"""
    controller = ProductController(dict(request.query_params))
    try:
        ret, err_msg = controller.product_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/product/create")
async def product_create(
    request: Request,
    user: dict = Depends(require_permission("product:create")),
    db: Session = Depends(get_db),
):
    """创建产品"""
    body = await request.json()
    controller = ProductController(body)
    try:
        create_id, err_msg = controller.product_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/product/update")
async def product_update(
    request: Request,
    user: dict = Depends(require_permission("product:update")),
    db: Session = Depends(get_db),
):
    """更新产品"""
    body = await request.json()
    controller = ProductController(body)
    try:
        update_id, err_msg = controller.product_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/product/delete")
async def product_delete(
    request: Request,
    user: dict = Depends(require_permission("product:delete")),
    db: Session = Depends(get_db),
):
    """删除产品"""
    body = await request.json()
    controller = ProductController(body)
    try:
        delete_id, err_msg = controller.product_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


# ==================== Module routes (CaseController) ====================

@router.get("/module/tree")
async def module_tree(
    request: Request,
    user: dict = Depends(require_permission("module:list")),
    db: Session = Depends(get_db),
):
    """模块树"""
    controller = CaseController(dict(request.query_params))
    try:
        result = controller.module_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/module/create")
async def module_create(
    request: Request,
    user: dict = Depends(require_permission("module:create")),
    db: Session = Depends(get_db),
):
    """创建模块"""
    body = await request.json()
    controller = CaseController(body)
    try:
        create_id, err_msg = controller.module_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/module/update")
async def module_update(
    request: Request,
    user: dict = Depends(require_permission("module:update")),
    db: Session = Depends(get_db),
):
    """更新模块"""
    body = await request.json()
    controller = CaseController(body)
    try:
        update_id, err_msg = controller.module_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/module/delete")
async def module_delete(
    request: Request,
    user: dict = Depends(require_permission("module:delete")),
    db: Session = Depends(get_db),
):
    """删除模块"""
    body = await request.json()
    controller = CaseController(body)
    try:
        delete_id, err_msg = controller.module_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()
