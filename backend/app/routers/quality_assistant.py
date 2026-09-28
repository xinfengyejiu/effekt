# encoding: UTF-8
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.controller.qualityAssistantController import QualityAssistantController
from app.core.ai_executor import run_in_ai_executor
from app.core.database import get_db, get_session_factory
from app.core.response import api_failure, api_success
from app.core.security import require_permission, get_current_user

router = APIRouter(tags=['quality-assistant'])


def _result(action):
    result = action()
    if isinstance(result, tuple):
        data, err_msg = result
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=data)
    return api_success(data=result)


@router.get('/quality-assistant/examples')
async def examples(user=Depends(get_current_user)):
    return api_success(data=QualityAssistantController.examples())


@router.post('/quality-assistant/chat')
async def chat(request: Request, db: Session = Depends(get_db),
               user=Depends(require_permission('qa:assistant:chat'))):
    body = await request.json()
    user_copy = dict(user or {})

    def _job():
        # 工作线程内独立开 session，避免跨线程复用 FastAPI 注入的 db
        session = get_session_factory()()
        try:
            return _result(lambda: QualityAssistantController.chat(session, body, user_copy))
        finally:
            session.close()

    return await run_in_ai_executor(_job)


@router.get('/quality-assistant/session/detail')
async def session_detail(request: Request, db: Session = Depends(get_db),
                         user=Depends(require_permission('qa:assistant:chat'))):
    session_id = request.query_params.get('session_id') or request.query_params.get('id')
    if not session_id:
        return api_failure(40009, msg='缺少 session_id')
    return _result(lambda: QualityAssistantController.session_detail(db, session_id, user.get('user_id')))


@router.get('/quality-assistant/session/latest')
async def session_latest(db: Session = Depends(get_db),
                         user=Depends(require_permission('qa:assistant:chat'))):
    return _result(lambda: QualityAssistantController.latest_session(db, user.get('user_id')))


@router.post('/quality-assistant/session/clear')
async def session_clear(request: Request, db: Session = Depends(get_db),
                        user=Depends(require_permission('qa:assistant:chat'))):
    body = await request.json()
    session_id = body.get('session_id') or body.get('id')
    if not session_id:
        return api_failure(40009, msg='缺少 session_id')
    return _result(lambda: QualityAssistantController.clear_session(db, session_id, user.get('user_id')))


@router.post('/quality-assistant/action/execute')
async def action_execute(request: Request, db: Session = Depends(get_db),
                         user=Depends(require_permission('qa:assistant:action'))):
    body = await request.json()
    action_type = (body or {}).get('type') or (body or {}).get('action_type')
    if action_type == 'run_contract_suite':
        codes = user.get('permission_codes') or []
        if codes and 'contract:suite:run' not in codes:
            return api_failure(40003, msg='无契约套件执行权限')
    return _result(lambda: QualityAssistantController.execute_action(db, body, user))
