# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.updateSqlProjectController import UpdateSqlProjectController

router = APIRouter(tags=["sql_project"])


# ==================== SqlProject routes ====================

@router.get("/list")
async def sql_project_list(
    request: Request,
    user: dict = Depends(require_permission("sql_project:list")),
    db: Session = Depends(get_db),
):
    """SQL 项目列表"""
    controller = UpdateSqlProjectController(dict(request.query_params))
    try:
        result = controller.query_smart_manage_sql_data()
        return api_success(data=result)
    except OperationalError as e:
        return api_failure(40009, msg=f'数据库操作异常：{str(e)[:200]}')
    finally:
        controller.close_session()


@router.post("/create")
async def sql_project_create(
    request: Request,
    user: dict = Depends(require_permission("sql_project:create")),
    db: Session = Depends(get_db),
):
    """创建 SQL 项目"""
    body = await request.json()
    controller = UpdateSqlProjectController(body)
    try:
        create_id, err_msg = controller.create_sql_project()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'sqlId': create_id})
    finally:
        controller.close_session()


@router.get("/detail")
async def sql_project_detail(
    request: Request,
    user: dict = Depends(require_permission("sql_project:detail")),
    db: Session = Depends(get_db),
):
    """SQL 项目详情"""
    controller = UpdateSqlProjectController(dict(request.query_params))
    try:
        ret, err_msg = controller.get_sql_project_detail()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/delete")
async def sql_project_delete(
    request: Request,
    user: dict = Depends(require_permission("sql_project:delete")),
    db: Session = Depends(get_db),
):
    """删除 SQL 项目"""
    body = await request.json()
    controller = UpdateSqlProjectController(body)
    try:
        delete_id, err_msg = controller.delete_sql_project()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'sqlId': delete_id})
    finally:
        controller.close_session()


@router.post("/execute")
async def sql_project_execute(
    request: Request,
    user: dict = Depends(require_permission("sql_project:execute")),
    db: Session = Depends(get_db),
):
    """执行 SQL 项目"""
    body = await request.json()
    controller = UpdateSqlProjectController(body)
    try:
        ret, err_msg = controller.execute_sql_project()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()
