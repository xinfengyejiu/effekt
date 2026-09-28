# encoding: UTF-8
import io

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.controller.weakNetworkController import WeakNetworkController
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['weak-network'])


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


@router.get('/weak-network/profiles')
async def weak_network_profiles(
    request: Request,
    user: dict = Depends(require_permission('weak_network:list')),
    db: Session = Depends(get_db),
):
    controller = WeakNetworkController(dict(request.query_params))
    return _response(controller, controller.profile_list)


@router.post('/weak-network/profiles')
async def weak_network_profile_create(
    request: Request,
    user: dict = Depends(require_permission('weak_network:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkController(body or {})
    return _response(controller, controller.profile_create, id_key='profileId')


@router.post('/weak-network/profiles/update')
async def weak_network_profile_update(
    request: Request,
    user: dict = Depends(require_permission('weak_network:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkController(body or {})
    return _response(controller, controller.profile_update, id_key='profileId')


@router.post('/weak-network/profiles/delete')
async def weak_network_profile_delete(
    request: Request,
    user: dict = Depends(require_permission('weak_network:manage')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkController(body or {})
    return _response(controller, controller.profile_delete, id_key='profileId')


@router.post('/weak-network/sessions')
async def weak_network_session_create(
    request: Request,
    user: dict = Depends(require_permission('weak_network:download')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = WeakNetworkController(body or {})
    return _response(controller, controller.session_create, id_key='sessionId')


@router.get('/weak-network/sessions')
async def weak_network_session_list(
    request: Request,
    user: dict = Depends(require_permission('weak_network:list')),
    db: Session = Depends(get_db),
):
    controller = WeakNetworkController(dict(request.query_params))
    return _response(controller, controller.session_list)


@router.get('/weak-network/sessions/{session_id}/download')
async def weak_network_session_download(
    session_id: int,
    user: dict = Depends(require_permission('weak_network:download')),
    db: Session = Depends(get_db),
):
    controller = WeakNetworkController({})
    try:
        content, filename, err = controller.session_download(session_id)
        if err:
            return api_failure(40009, msg=err)
        headers = {
            'Content-Disposition': 'attachment; filename="{}"'.format(filename or 'weaknet.zip'),
        }
        return StreamingResponse(io.BytesIO(content), media_type='application/zip', headers=headers)
    finally:
        controller.close_session()
