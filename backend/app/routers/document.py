# encoding: UTF-8
from fastapi import APIRouter, Request, Depends, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.documentSourceController import DocumentSourceController

router = APIRouter(tags=["document"])


@router.get("/document/list")
async def document_list(
    request: Request,
    user: dict = Depends(require_permission("document:list")),
    db: Session = Depends(get_db),
):
    """文档列表"""
    controller = DocumentSourceController(dict(request.query_params))
    try:
        result = controller.document_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/document/detail")
async def document_detail(
    request: Request,
    user: dict = Depends(require_permission("document:detail")),
    db: Session = Depends(get_db),
):
    """文档详情"""
    controller = DocumentSourceController(dict(request.query_params))
    try:
        ret, err_msg = controller.document_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/document/create")
async def document_create(
    request: Request,
    user: dict = Depends(require_permission("document:create")),
    db: Session = Depends(get_db),
):
    """创建文档"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        create_id, err_msg = controller.document_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/document/update")
async def document_update(
    request: Request,
    user: dict = Depends(require_permission("document:update")),
    db: Session = Depends(get_db),
):
    """更新文档"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        update_id, err_msg = controller.document_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/document/delete")
async def document_delete(
    request: Request,
    user: dict = Depends(require_permission("document:delete")),
    db: Session = Depends(get_db),
):
    """删除文档"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        delete_id, err_msg = controller.document_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.post("/document/refresh")
async def document_refresh(
    request: Request,
    user: dict = Depends(require_permission("document:update")),
    db: Session = Depends(get_db),
):
    """刷新文档"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        success, err_msg = controller.document_refresh()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'success': success})
    finally:
        controller.close_session()


@router.post("/document/generate-cases")
async def document_generate_cases(
    request: Request,
    user: dict = Depends(require_permission("document:generate")),
    db: Session = Depends(get_db),
):
    """生成测试用例"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        ret, err_msg = controller.document_generate_cases()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/document/generate-cases-streaming")
async def document_generate_cases_streaming(
    request: Request,
    user: dict = Depends(require_permission("document:generate")),
    db: Session = Depends(get_db),
):
    """生成测试用例（流式响应）"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        result = controller.document_generate_cases_streaming()
        return StreamingResponse(
            result.response,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    finally:
        controller.close_session()


@router.get("/document/generation-status")
async def document_generation_status(
    request: Request,
    user: dict = Depends(require_permission("document:generate")),
    db: Session = Depends(get_db),
):
    """文档生成状态"""
    controller = DocumentSourceController(dict(request.query_params))
    try:
        result = controller.document_generation_status()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/document/cancel-generate-cases")
async def document_cancel_generate_cases(
    request: Request,
    user: dict = Depends(require_permission("document:generate")),
    db: Session = Depends(get_db),
):
    """取消生成测试用例"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        success, err_msg = controller.document_cancel_generate_cases()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'success': success})
    finally:
        controller.close_session()


@router.post("/document/match-modules")
async def document_match_modules(
    request: Request,
    user: dict = Depends(require_permission("document:generate")),
    db: Session = Depends(get_db),
):
    """匹配模块"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        result = controller.document_match_modules()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/document/import-cases")
async def document_import_cases(
    request: Request,
    user: dict = Depends(require_permission("document:import")),
    db: Session = Depends(get_db),
):
    """导入用例"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        count, err_msg = controller.document_import_cases()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'count': count})
    finally:
        controller.close_session()


@router.post("/document/batch-create-modules")
async def document_batch_create_modules(
    request: Request,
    user: dict = Depends(require_permission("module:create")),
    db: Session = Depends(get_db),
):
    """批量创建模块"""
    body = await request.json()
    controller = DocumentSourceController(body)
    try:
        ret, err_msg = controller.document_batch_create_modules()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/document/upload")
async def document_upload(
    request: Request,
    file: UploadFile,
    product_id: str = Form(...),
    project_id: str = Form(...),
    created_by: str = Form(None),
    user: dict = Depends(require_permission("document:create")),
    db: Session = Depends(get_db),
):
    """上传文档"""
    import os
    import uuid
    import re
    from datetime import datetime as dt
    from app.api.model.productModel import Product
    from app.api.model.projectModel import Project

    UPLOAD_FOLDER = 'attachment/documents'
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'md', 'markdown'}

    if not file.filename:
        return api_failure(40009, msg='文件名不能为空')

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return api_failure(40009, msg='不支持的文件格式，仅支持：pdf、xlsx、xls、md、markdown')

    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_upload_path = os.path.join(root_dir, UPLOAD_FOLDER)

        product = db.query(Product).filter(Product.id == int(product_id), Product.is_delete == 0).first()
        project = db.query(Project).filter(Project.id == int(project_id), Project.is_delete == 0).first()

        if not product:
            return api_failure(40009, msg='产品不存在')
        if not project:
            return api_failure(40009, msg='项目不存在')

        product_folder = os.path.join(base_upload_path, product.name)
        project_folder = os.path.join(product_folder, project.name)
        os.makedirs(project_folder, exist_ok=True)

        timestamp = dt.now().strftime('%Y%m%d%H%M%S')
        original_name = file.filename.rsplit('.', 1)[0]
        safe_name = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', original_name)[:50]
        new_filename = f'{timestamp}-{safe_name}-{uuid.uuid4().hex[:8]}.{ext}'
        file_path = os.path.join(project_folder, new_filename)

        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)

        relative_path = f'{UPLOAD_FOLDER}/{product.name}/{project.name}/{new_filename}'

        doc_type = 1  # PDF default
        if ext in ('xlsx', 'xls'):
            doc_type = 3
        elif ext in ('md', 'markdown'):
            doc_type = 4

        req_data = {
            'productId': product_id,
            'projectId': project_id,
            'name': original_name,
            'type': doc_type,
            'source': 1,
            'filePath': relative_path,
            'createdBy': created_by,
        }

        controller = DocumentSourceController(req_data)
        try:
            create_id, err_msg = controller.document_create()
            if err_msg:
                return api_failure(40009, msg=err_msg)
            return api_success(data={'id': create_id, 'documentId': create_id})
        finally:
            controller.close_session()
    except Exception as e:
        return api_failure(40009, msg=f'上传失败：{str(e)}')
