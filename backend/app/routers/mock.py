# encoding: UTF-8
"""
智能 Mock 服务路由
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.core.response import api_success, api_failure
from logger import logger
import traceback

router = APIRouter(prefix="/mock", tags=["mock"])


@router.post("/document/import")
async def mock_document_import(
    request: Request,
    user: dict = Depends(require_permission("mock:document:import")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.document_import()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/document/upload-import")
async def mock_document_upload_import(
    request: Request,
    user: dict = Depends(require_permission("mock:document:import")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.document_upload_import()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/document/url-import")
async def mock_document_url_import(
    request: Request,
    user: dict = Depends(require_permission("mock:document:import")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.document_url_import()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/document/list")
async def mock_document_list(
    request: Request,
    user: dict = Depends(require_permission("mock:document:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    controller = MockController(dict(request.query_params))
    try:
        return api_success(data=controller.document_list())
    finally:
        controller.close_session()


@router.get("/interface/list")
async def mock_interface_list(
    request: Request,
    user: dict = Depends(require_permission("mock:interface:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    controller = MockController(dict(request.query_params))
    try:
        return api_success(data=controller.interface_list())
    finally:
        controller.close_session()


@router.get("/interface/detail")
async def mock_interface_detail(
    request: Request,
    user: dict = Depends(require_permission("mock:interface:detail")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    controller = MockController(dict(request.query_params))
    try:
        ret, err_msg = controller.interface_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/interface/update")
async def mock_interface_update(
    request: Request,
    user: dict = Depends(require_permission("mock:interface:update")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.interface_update()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={"id": ret})
    finally:
        controller.close_session()


@router.post("/interface/enable")
async def mock_interface_enable(
    request: Request,
    user: dict = Depends(require_permission("mock:interface:enable")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.interface_enable()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={"id": ret})
    finally:
        controller.close_session()


@router.post("/interface/disable")
async def mock_interface_disable(
    request: Request,
    user: dict = Depends(require_permission("mock:interface:disable")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.interface_disable()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={"id": ret})
    finally:
        controller.close_session()


@router.get("/scene/list")
async def mock_scene_list(
    request: Request,
    user: dict = Depends(require_permission("mock:scene:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    controller = MockController(dict(request.query_params))
    try:
        return api_success(data=controller.scene_list())
    finally:
        controller.close_session()


@router.post("/scene/update")
async def mock_scene_update(
    request: Request,
    user: dict = Depends(require_permission("mock:scene:update")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.scene_update()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={"id": ret})
    finally:
        controller.close_session()


@router.post("/scene/enable")
async def mock_scene_enable(
    request: Request,
    user: dict = Depends(require_permission("mock:scene:enable")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.scene_enable()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={"id": ret})
    finally:
        controller.close_session()


@router.post("/scene/disable")
async def mock_scene_disable(
    request: Request,
    user: dict = Depends(require_permission("mock:scene:disable")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    body = await request.json()
    controller = MockController(body)
    try:
        ret, err_msg = controller.scene_disable()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={"id": ret})
    finally:
        controller.close_session()


@router.get("/log/list")
async def mock_log_list(
    request: Request,
    user: dict = Depends(require_permission("mock:log:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    controller = MockController(dict(request.query_params))
    try:
        return api_success(data=controller.log_list())
    finally:
        controller.close_session()


@router.get("/parse-issue/list")
async def mock_parse_issue_list(
    request: Request,
    user: dict = Depends(require_permission("mock:parse-issue:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    controller = MockController(dict(request.query_params))
    try:
        return api_success(data=controller.parse_issue_list())
    finally:
        controller.close_session()


@router.api_route("/runtime/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def mock_runtime(
    path: str,
    request: Request,
    user: dict = Depends(require_permission("mock:runtime:access")),
    db: Session = Depends(get_db),
):
    from app.api.controller.mockController import MockController
    try:
        body = await request.json()
    except Exception:
        body = {}
    headers = dict(request.headers)
    query = dict(request.query_params)
    controller = MockController({})
    try:
        response, err_msg = controller.runtime(request.method, path, query, body, headers)
        if err_msg:
            logger.warning(f"mock_runtime提示：{err_msg}, path={path}, query={query}")
        return response
    except Exception as e:
        logger.error(f"mock_runtime异常：{str(e)}, path={path}, query={query}, 堆栈：{traceback.format_exc()}")
        return api_failure(40008, msg=str(e))
    finally:
        controller.close_session()
