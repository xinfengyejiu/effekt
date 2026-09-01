# encoding: UTF-8
import os
from fastapi import APIRouter, Request, Depends, UploadFile, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission, get_current_user
from app.core.response import api_success, api_failure
from app.api.controller.caseController import CaseController

router = APIRouter(tags=["case"])


@router.get("/case/list")
async def case_list(
    request: Request,
    user: dict = Depends(require_permission("case:list")),
    db: Session = Depends(get_db),
):
    """用例列表"""
    controller = CaseController(dict(request.query_params))
    try:
        result = controller.case_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/case/detail")
async def case_detail(
    request: Request,
    user: dict = Depends(require_permission("case:detail")),
    db: Session = Depends(get_db),
):
    """用例详情"""
    controller = CaseController(dict(request.query_params))
    try:
        ret, err_msg = controller.case_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/case/create")
async def case_create(
    request: Request,
    user: dict = Depends(require_permission("case:create")),
    db: Session = Depends(get_db),
):
    """创建用例"""
    body = await request.json()
    controller = CaseController(body)
    try:
        create_id, err_msg = controller.case_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/case/update")
async def case_update(
    request: Request,
    user: dict = Depends(require_permission("case:update")),
    db: Session = Depends(get_db),
):
    """更新用例"""
    body = await request.json()
    controller = CaseController(body)
    try:
        update_id, err_msg = controller.case_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/case/delete")
async def case_delete(
    request: Request,
    user: dict = Depends(require_permission("case:delete")),
    db: Session = Depends(get_db),
):
    """删除用例"""
    body = await request.json()
    controller = CaseController(body)
    try:
        ret, err_msg = controller.case_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/case/copy")
async def case_copy(
    request: Request,
    user: dict = Depends(require_permission("case:create")),
    db: Session = Depends(get_db),
):
    """复制用例"""
    body = await request.json()
    controller = CaseController(body)
    try:
        create_id, err_msg = controller.case_copy()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/case/restore")
async def case_restore(
    request: Request,
    user: dict = Depends(require_permission("case:update")),
    db: Session = Depends(get_db),
):
    """恢复用例"""
    body = await request.json()
    controller = CaseController(body)
    try:
        ret, err_msg = controller.case_restore()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/case/import")
async def case_import(
    request: Request,
    file: UploadFile,
    project_id: str = Form(...),
    product_id: str = Form(None),
    user: dict = Depends(require_permission("case:create")),
    db: Session = Depends(get_db),
):
    """导入用例"""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    attachment_dir = os.path.join(root_dir, 'attachment')
    os.makedirs(attachment_dir, exist_ok=True)
    temp_path = os.path.join(attachment_dir, 'temp_import.xlsx')
    try:
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
        controller = CaseController({})
        try:
            success_count, err_msg = controller.case_import(temp_path, project_id, product_id)
            if err_msg and ('失败' in err_msg or success_count == 0):
                return api_failure(40009, msg=err_msg)
            return api_success(data={'successCount': success_count, 'message': err_msg})
        finally:
            controller.close_session()
    except Exception as e:
        return api_failure(40009, msg=f'导入失败：{str(e)[:100]}')
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/import/template")
async def import_template(
    request: Request,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """下载导入模板"""
    template_path = CaseController.get_template_path()
    if not os.path.exists(template_path):
        return api_failure(40011, msg='模板文件不存在')
    return FileResponse(
        template_path,
        filename='测试用例模版.xlsx',
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.get("/case/export")
async def case_export(
    request: Request,
    user: dict = Depends(require_permission("case:list")),
    db: Session = Depends(get_db),
):
    """导出用例"""
    controller = CaseController(dict(request.query_params))
    try:
        project_id = request.query_params.get('projectId')
        product_id = request.query_params.get('productId')
        file_obj, filename, err_msg = controller.case_export(project_id, product_id)
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return StreamingResponse(
            file_obj,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return api_failure(40012, msg=f'导出失败：{str(e)[:100]}')
    finally:
        controller.close_session()


@router.post("/case/snapshot/create")
async def case_snapshot_create(
    request: Request,
    user: dict = Depends(require_permission("case_snapshot:create")),
    db: Session = Depends(get_db),
):
    """创建用例快照"""
    body = await request.json()
    controller = CaseController(body)
    try:
        create_id, err_msg = controller.snapshot_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.get("/case/snapshot/list")
async def case_snapshot_list(
    request: Request,
    user: dict = Depends(require_permission("case_snapshot:list")),
    db: Session = Depends(get_db),
):
    """用例快照列表"""
    controller = CaseController(dict(request.query_params))
    try:
        result = controller.snapshot_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/case/review/create")
async def case_review_create(
    request: Request,
    user: dict = Depends(require_permission("case_review:create")),
    db: Session = Depends(get_db),
):
    """创建用例评审"""
    body = await request.json()
    controller = CaseController(body)
    try:
        create_id, err_msg = controller.review_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/case/review/update")
async def case_review_update(
    request: Request,
    user: dict = Depends(require_permission("case_review:update")),
    db: Session = Depends(get_db),
):
    """更新用例评审"""
    body = await request.json()
    controller = CaseController(body)
    try:
        update_id, err_msg = controller.review_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.get("/case/review/list")
async def case_review_list(
    request: Request,
    user: dict = Depends(require_permission("case_review:list")),
    db: Session = Depends(get_db),
):
    """用例评审列表"""
    controller = CaseController(dict(request.query_params))
    try:
        result = controller.review_list()
        return api_success(data=result)
    finally:
        controller.close_session()
