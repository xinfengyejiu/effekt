# encoding: UTF-8
import io

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage, ImmutableMultiDict

from app.api.controller.exploreSessionController import ExploreSessionController
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['explore-session'])


class FlaskRequestAdapter(object):
    """将 FastAPI 上传适配为 Flask 风格 request，供 ExploreSessionService 使用。"""

    def __init__(self, file_content, filename, content_type, form_data=None):
        file_storage = FileStorage(
            stream=io.BytesIO(file_content),
            filename=filename,
            content_type=content_type,
        )
        self.files = ImmutableMultiDict([('file', file_storage)])
        self.form = ImmutableMultiDict(list((form_data or {}).items()))


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


@router.post('/explore/session/create')
async def explore_session_create(
    request: Request,
    user: dict = Depends(require_permission('explore_session:create')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.session_create, id_key='id')


@router.get('/explore/session/list')
async def explore_session_list(
    request: Request,
    user: dict = Depends(require_permission('explore_session:list')),
    db: Session = Depends(get_db),
):
    controller = ExploreSessionController(dict(request.query_params))
    return _response(controller, controller.session_list)


@router.get('/explore/session/detail')
async def explore_session_detail(
    request: Request,
    user: dict = Depends(require_permission('explore_session:detail')),
    db: Session = Depends(get_db),
):
    controller = ExploreSessionController(dict(request.query_params))
    return _response(controller, controller.session_detail)


@router.post('/explore/session/update')
async def explore_session_update(
    request: Request,
    user: dict = Depends(require_permission('explore_session:update')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.session_update, id_key='id')


@router.post('/explore/session/start')
async def explore_session_start(
    request: Request,
    user: dict = Depends(require_permission('explore_session:update')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.session_start, id_key='id')


@router.post('/explore/session/end')
async def explore_session_end(
    request: Request,
    user: dict = Depends(require_permission('explore_session:update')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.session_end, id_key='id')


@router.post('/explore/session/archive')
async def explore_session_archive(
    request: Request,
    user: dict = Depends(require_permission('explore_session:update')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.session_archive, id_key='id')


@router.post('/explore/session/entry/add')
async def explore_session_entry_add(
    request: Request,
    user: dict = Depends(require_permission('explore_session:entry')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.entry_add, id_key='id')


@router.post('/explore/session/entry/update')
async def explore_session_entry_update(
    request: Request,
    user: dict = Depends(require_permission('explore_session:entry')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.entry_update, id_key='id')


@router.post('/explore/session/entry/delete')
async def explore_session_entry_delete(
    request: Request,
    user: dict = Depends(require_permission('explore_session:entry')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.entry_delete, id_key='id')


@router.post('/explore/session/upload')
async def explore_session_upload(
    request: Request,
    file: UploadFile = File(...),
    sessionId: str = Form(None),
    session_id: str = Form(None),
    content: str = Form(None),
    user: dict = Depends(require_permission('explore_session:upload')),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    form_data = {
        'sessionId': sessionId or session_id or '',
        'content': content or '',
    }
    adapter = FlaskRequestAdapter(contents, file.filename, file.content_type, form_data)
    controller = ExploreSessionController({})
    return _response(controller, lambda: controller.upload(adapter), id_key='id')


@router.post('/explore/session/to-bug')
async def explore_session_to_bug(
    request: Request,
    user: dict = Depends(require_permission('explore_session:to_bug')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.to_bug, id_key='bugId')


@router.post('/explore/session/to-case-draft')
async def explore_session_to_case_draft(
    request: Request,
    user: dict = Depends(require_permission('explore_session:to_case')),
    db: Session = Depends(get_db),
):
    body = await request.json()
    controller = ExploreSessionController(body or {})
    return _response(controller, controller.to_case_draft, id_key='caseId')
