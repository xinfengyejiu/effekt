# encoding: UTF-8
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.controller.weakNetworkAiController import WeakNetworkAiController
from app.core.ai_executor import run_in_ai_executor
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['weak-network-ai'])


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


@router.get('/weak-network-ai/tasks')
async def wn_ai_task_list(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:list')),
    db: Session = Depends(get_db),
):
    controller = WeakNetworkAiController(dict(request.query_params))
    return _response(controller, controller.list_tasks)


@router.post('/weak-network-ai/tasks')
async def wn_ai_task_create(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkAiController(body or {})
    return _response(controller, controller.create_task, id_key='taskId')


@router.get('/weak-network-ai/tasks/detail')
async def wn_ai_task_detail(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:list')),
    db: Session = Depends(get_db),
):
    controller = WeakNetworkAiController(dict(request.query_params))
    return _response(controller, controller.detail)


@router.post('/weak-network-ai/tasks/update')
async def wn_ai_task_update(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkAiController(body or {})
    return _response(controller, controller.update_task)


@router.post('/weak-network-ai/tasks/orchestrate')
async def wn_ai_task_orchestrate(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    user_id = (user or {}).get('user_id')

    def _job():
        from flask import g
        from app.main import legacy_flask_app
        with legacy_flask_app.app_context():
            g.current_user_id = user_id
            controller = WeakNetworkAiController(body or {})
            return _response(controller, controller.orchestrate)

    return await run_in_ai_executor(_job)


@router.post('/weak-network-ai/tasks/confirm')
async def wn_ai_task_confirm(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkAiController(body or {})
    return _response(controller, controller.confirm)


@router.post('/weak-network-ai/tasks/evidence')
async def wn_ai_task_evidence_json(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:judge')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkAiController(body or {})
    return _response(controller, lambda: controller.add_evidence())


@router.post('/weak-network-ai/tasks/evidence-upload')
async def wn_ai_task_evidence_upload(
    file: UploadFile = File(...),
    taskId: str = Form(...),
    checkpointId: str = Form(None),
    note: str = Form(''),
    mobileExecutionId: str = Form(None),
    user: dict = Depends(require_permission('weak_network_ai:judge')),
    db: Session = Depends(get_db),
):
    body = {
        'taskId': taskId,
        'checkpointId': checkpointId,
        'note': note or '',
        'mobileExecutionId': mobileExecutionId,
    }
    raw = await file.read()
    controller = WeakNetworkAiController(body)
    return _response(
        controller,
        lambda: controller.add_evidence(upload_bytes=raw, filename=file.filename),
    )


@router.post('/weak-network-ai/tasks/judge')
async def wn_ai_task_judge(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:judge')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    user_id = (user or {}).get('user_id')

    def _job():
        from flask import g
        from app.main import legacy_flask_app
        with legacy_flask_app.app_context():
            g.current_user_id = user_id
            controller = WeakNetworkAiController(body or {})
            return _response(controller, controller.judge)

    return await run_in_ai_executor(_job)


@router.post('/weak-network-ai/findings/dismiss')
async def wn_ai_finding_dismiss(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:generate')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkAiController(body or {})
    return _response(controller, controller.dismiss)


@router.post('/weak-network-ai/findings/confirm-to-bug')
async def wn_ai_finding_confirm_to_bug(
    request: Request,
    user: dict = Depends(require_permission('weak_network_ai:generate')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkAiController(body or {})
    return _response(controller, controller.confirm_to_bug, id_key='bugId')
