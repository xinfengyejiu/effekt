# encoding: UTF-8
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.controller.aiDataProbeController import AiDataProbeController
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission


router = APIRouter(tags=['ai-data-probe'])


def _bind_user(user):
    """把登录用户写入 Flask g，供 controller / AIService 读取个人模型偏好。"""
    try:
        from flask import g, has_app_context
        if has_app_context() and user and user.get('user_id') is not None:
            g.current_user_id = user.get('user_id')
    except Exception:
        pass


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


@router.get('/ai-data-probe/connections')
async def ai_data_probe_connections(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:list')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    controller = AiDataProbeController(dict(request.query_params))
    return _response(controller, controller.connection_list)


@router.post('/ai-data-probe/connections')
async def ai_data_probe_connection_create(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:manage')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.connection_create, id_key='connectionId')


@router.post('/ai-data-probe/connections/update')
async def ai_data_probe_connection_update(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:manage')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.connection_update, id_key='connectionId')


@router.post('/ai-data-probe/connections/delete')
async def ai_data_probe_connection_delete(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:manage')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.connection_delete, id_key='connectionId')


@router.post('/ai-data-probe/connections/test')
async def ai_data_probe_connection_test(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:list')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.connection_test)


@router.get('/ai-data-probe/connections/tables')
async def ai_data_probe_connection_tables(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:list')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    controller = AiDataProbeController(dict(request.query_params))
    return _response(controller, controller.connection_tables)


@router.get('/ai-data-probe/connections/table-columns')
async def ai_data_probe_connection_table_columns(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:list')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    controller = AiDataProbeController(dict(request.query_params))
    return _response(controller, controller.connection_table_columns)


@router.post('/ai-data-probe/connections/import-from-project')
async def ai_data_probe_connection_import(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:manage')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.connection_import, id_key='connectionId')


@router.get('/ai-data-probe/sessions')
async def ai_data_probe_sessions(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:list')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    controller = AiDataProbeController(dict(request.query_params))
    return _response(controller, controller.session_list)


@router.post('/ai-data-probe/sessions')
async def ai_data_probe_session_create(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:query')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.session_create, id_key='sessionId')


@router.get('/ai-data-probe/session/detail')
async def ai_data_probe_session_detail(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:list')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    controller = AiDataProbeController(dict(request.query_params))
    return _response(controller, controller.session_detail)


@router.post('/ai-data-probe/session/rename')
async def ai_data_probe_session_rename(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:query')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.session_rename, id_key='sessionId')


@router.post('/ai-data-probe/ask')
async def ai_data_probe_ask(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:query')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.ask)


@router.post('/ai-data-probe/ask-stream')
async def ai_data_probe_ask_stream(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:query')),
    db: Session = Depends(get_db),
):
    """智能问数流式输出（SSE）"""
    import json as _json
    from fastapi.responses import StreamingResponse

    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})

    def event_gen():
        try:
            for evt in controller.ask_stream():
                yield 'data: {}\n\n'.format(_json.dumps(evt, ensure_ascii=False, default=str))
        except Exception as exc:
            yield 'data: {}\n\n'.format(_json.dumps({
                'type': 'error',
                'message': '流式对号失败：{}'.format(exc),
            }, ensure_ascii=False))
        finally:
            controller.close_session()

    return StreamingResponse(
        event_gen(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@router.post('/ai-data-probe/rerun-sql')
async def ai_data_probe_rerun_sql(
    request: Request,
    user: dict = Depends(require_permission('ai_data_probe:query')),
    db: Session = Depends(get_db),
):
    _bind_user(user)
    body = await request.json()
    controller = AiDataProbeController(body or {})
    return _response(controller, controller.rerun_sql)
