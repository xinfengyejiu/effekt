# encoding: UTF-8
import io
from fastapi import APIRouter, Request, Depends, UploadFile
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage, ImmutableMultiDict

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.reportController import ReportController

router = APIRouter(tags=["report"])


# ==================== Report routes ====================

@router.get("/report/list")
async def report_list(
    request: Request,
    user: dict = Depends(require_permission("report:list")),
    db: Session = Depends(get_db),
):
    """报告列表"""
    controller = ReportController(dict(request.query_params))
    try:
        result = controller.report_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/report/detail")
async def report_detail(
    request: Request,
    user: dict = Depends(require_permission("report:detail")),
    db: Session = Depends(get_db),
):
    """报告详情"""
    controller = ReportController(dict(request.query_params))
    try:
        ret, err_msg = controller.report_detail()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/report/generate")
async def report_generate(
    request: Request,
    user: dict = Depends(require_permission("report:generate")),
    db: Session = Depends(get_db),
):
    """生成报告"""
    body = await request.json()
    controller = ReportController(body)
    try:
        create_id, err_msg = controller.report_generate()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/report/upload-html")
async def report_upload_html(
    request: Request,
    file: UploadFile,
    user: dict = Depends(require_permission("report:generate")),
    db: Session = Depends(get_db),
):
    """上传 HTML 报告"""
    contents = await file.read()
    flask_file = FileStorage(
        stream=io.BytesIO(contents),
        filename=file.filename,
        content_type=file.content_type,
    )

    class MockRequest:
        files = ImmutableMultiDict([('file', flask_file)])
        form = ImmutableMultiDict([])

    controller = ReportController(MockRequest())
    try:
        create_id, err_msg = controller.report_upload_html()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/report/delete")
async def report_delete(
    request: Request,
    user: dict = Depends(require_permission("report:delete")),
    db: Session = Depends(get_db),
):
    """删除报告"""
    body = await request.json()
    controller = ReportController(body)
    try:
        delete_id, err_msg = controller.report_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()
