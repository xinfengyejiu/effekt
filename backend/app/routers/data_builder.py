# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.dataBuilderController import DataBuilderController

router = APIRouter(tags=["data_builder"])


# ==================== DataBuilder routes ====================

@router.get("/data/builder/list")
async def data_builder_list(
    request: Request,
    user: dict = Depends(require_permission("data_builder:list")),
    db: Session = Depends(get_db),
):
    """数据构建列表"""
    controller = DataBuilderController(dict(request.query_params))
    try:
        result = controller.builder_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/data/builder/detail")
async def data_builder_detail(
    request: Request,
    user: dict = Depends(require_permission("data_builder:detail")),
    db: Session = Depends(get_db),
):
    """数据构建详情"""
    controller = DataBuilderController(dict(request.query_params))
    try:
        ret, err_msg = controller.builder_detail()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/data/builder/create")
async def data_builder_create(
    request: Request,
    user: dict = Depends(require_permission("data_builder:create")),
    db: Session = Depends(get_db),
):
    """创建数据构建"""
    body = await request.json()
    controller = DataBuilderController(body)
    try:
        create_id, err_msg = controller.builder_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/data/builder/update")
async def data_builder_update(
    request: Request,
    user: dict = Depends(require_permission("data_builder:update")),
    db: Session = Depends(get_db),
):
    """更新数据构建"""
    body = await request.json()
    controller = DataBuilderController(body)
    try:
        update_id, err_msg = controller.builder_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/data/builder/delete")
async def data_builder_delete(
    request: Request,
    user: dict = Depends(require_permission("data_builder:delete")),
    db: Session = Depends(get_db),
):
    """删除数据构建"""
    body = await request.json()
    controller = DataBuilderController(body)
    try:
        delete_id, err_msg = controller.builder_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.post("/data/builder/execute")
async def data_builder_execute(
    request: Request,
    user: dict = Depends(require_permission("data_builder:execute")),
    db: Session = Depends(get_db),
):
    """执行数据构建"""
    body = await request.json()
    controller = DataBuilderController(body)
    try:
        ret, err_msg = controller.builder_execute()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


# ==================== DataTask routes ====================

@router.get("/data/task/status")
async def data_task_status(
    request: Request,
    user: dict = Depends(require_permission("data_task:status")),
    db: Session = Depends(get_db),
):
    """数据任务状态"""
    controller = DataBuilderController(dict(request.query_params))
    try:
        ret, err_msg = controller.task_status()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()
