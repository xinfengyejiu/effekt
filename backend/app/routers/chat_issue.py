# encoding: UTF-8
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.controller.chatIssueController import ChatIssueController
from app.core.ai_executor import run_in_ai_executor
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['chat-issue'])


def _response(controller, action, id_key='id'):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return api_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return api_success(data={id_key: ret})
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post('/chat-issue/import')
async def chat_issue_import(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:import')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ChatIssueController(body or {})
    return _response(controller, controller.import_text)


@router.post('/chat-issue/import-file')
async def chat_issue_import_file(
    request: Request,
    file: UploadFile = File(...),
    productId: str = Form(None),
    projectId: str = Form(None),
    productName: str = Form(None),
    projectName: str = Form(None),
    splitByDay: str = Form('true'),
    user: dict = Depends(require_permission('chat_issue:import')),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    try:
        text = raw.decode('utf-8')
    except Exception:
        text = raw.decode('gbk', errors='ignore')
    body = {
        'text': text,
        'productId': productId,
        'projectId': projectId,
        'productName': productName or '',
        'projectName': projectName or '',
        'sourceType': 'file',
        'splitByDay': splitByDay not in ('false', '0', 'False'),
        'title': (file.filename or '文件导入').rsplit('.', 1)[0][:120],
    }
    controller = ChatIssueController(body)
    return _response(controller, controller.import_text)


@router.get('/chat-issue/list')
async def chat_issue_list(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:list')),
    db: Session = Depends(get_db),
):
    controller = ChatIssueController(dict(request.query_params))
    return _response(controller, controller.import_list)


@router.get('/chat-issue/detail')
async def chat_issue_detail(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:list')),
    db: Session = Depends(get_db),
):
    controller = ChatIssueController(dict(request.query_params))
    return _response(controller, controller.import_detail)


@router.post('/chat-issue/item/update')
async def chat_issue_item_update(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:import')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ChatIssueController(body or {})
    return _response(controller, controller.item_update)


@router.post('/chat-issue/item/delete')
async def chat_issue_item_delete(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:import')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ChatIssueController(body or {})
    return _response(controller, controller.item_delete)


@router.post('/chat-issue/analyze')
async def chat_issue_analyze(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:analyze')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    user_id = (user or {}).get('user_id')

    def _job():
        # AI 线程池无请求中间件的 Flask context，访问 g 会报 Working outside of application context
        from flask import g
        from app.main import legacy_flask_app

        with legacy_flask_app.app_context():
            g.current_user_id = user_id
            controller = ChatIssueController(body or {})
            return _response(controller, controller.analyze)

    return await run_in_ai_executor(_job)


@router.post('/chat-issue/dismiss')
async def chat_issue_dismiss(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:generate')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ChatIssueController(body or {})
    return _response(controller, controller.dismiss)


@router.post('/chat-issue/confirm-to-bug')
async def chat_issue_confirm_to_bug(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:generate')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ChatIssueController(body or {})
    return _response(controller, controller.confirm_to_bug, id_key='bugId')


@router.post('/chat-issue/to-case')
async def chat_issue_to_case(
    request: Request,
    user: dict = Depends(require_permission('chat_issue:generate')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ChatIssueController(body or {})
    return _response(controller, controller.to_case)
