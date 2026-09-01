# encoding: UTF-8
import io
from fastapi import APIRouter, Request, Depends, UploadFile, Form
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage, ImmutableMultiDict

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.knowledgeController import KnowledgeController

router = APIRouter(tags=["knowledge"])


class FlaskRequestAdapter:
    """将 FastAPI 上传文件适配为 Flask 风格 request，供 KnowledgeController 使用"""

    def __init__(self, file_content, filename, content_type, form_data=None):
        file_storage = FileStorage(
            stream=io.BytesIO(file_content),
            filename=filename,
            content_type=content_type,
        )
        self.files = ImmutableMultiDict([('file', file_storage)])
        self.form = ImmutableMultiDict(list((form_data or {}).items()))


def _knowledge_response(controller, action, id_key='id'):
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


# ==================== Document routes ====================

@router.get("/knowledge/document/list")
async def knowledge_document_list(
    request: Request,
    user: dict = Depends(require_permission("knowledge:list")),
    db: Session = Depends(get_db),
):
    """文档列表"""
    controller = KnowledgeController(dict(request.query_params))
    return _knowledge_response(controller, controller.document_list)


@router.post("/knowledge/document/upload")
async def knowledge_document_upload(
    request: Request,
    file: UploadFile,
    auto_parse: str = Form(None),
    user: dict = Depends(require_permission("knowledge:upload")),
    db: Session = Depends(get_db),
):
    """上传文档"""
    contents = await file.read()
    form_data = {'autoParse': auto_parse} if auto_parse else {}
    mock_req = FlaskRequestAdapter(contents, file.filename, file.content_type, form_data)
    controller = KnowledgeController(mock_req)
    return _knowledge_response(controller, controller.document_upload)


@router.post("/knowledge/document/parse")
async def knowledge_document_parse(
    request: Request,
    user: dict = Depends(require_permission("knowledge:parse")),
    db: Session = Depends(get_db),
):
    """解析文档"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.document_parse)


@router.post("/knowledge/document/delete")
async def knowledge_document_delete(
    request: Request,
    user: dict = Depends(require_permission("knowledge:delete")),
    db: Session = Depends(get_db),
):
    """删除文档"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.document_delete)


# ==================== Search & Chat routes ====================

@router.post("/knowledge/search")
async def knowledge_search(
    request: Request,
    user: dict = Depends(require_permission("knowledge:search")),
    db: Session = Depends(get_db),
):
    """知识搜索"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.search)


@router.post("/knowledge/chat")
async def knowledge_chat(
    request: Request,
    user: dict = Depends(require_permission("knowledge:chat")),
    db: Session = Depends(get_db),
):
    """知识对话"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.chat)


@router.get("/knowledge/chat/session/list")
async def knowledge_chat_session_list(
    request: Request,
    user: dict = Depends(require_permission("knowledge:chat")),
    db: Session = Depends(get_db),
):
    """对话会话列表"""
    controller = KnowledgeController(dict(request.query_params))
    return _knowledge_response(controller, controller.session_list)


@router.get("/knowledge/chat/message/list")
async def knowledge_chat_message_list(
    request: Request,
    user: dict = Depends(require_permission("knowledge:chat")),
    db: Session = Depends(get_db),
):
    """对话消息列表"""
    controller = KnowledgeController(dict(request.query_params))
    return _knowledge_response(controller, controller.message_list)


@router.post("/knowledge/chat/session/delete")
async def knowledge_chat_session_delete(
    request: Request,
    user: dict = Depends(require_permission("knowledge:chat")),
    db: Session = Depends(get_db),
):
    """删除对话会话"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.session_delete)


# ==================== Model Setting routes ====================

@router.get("/knowledge/model-setting/detail")
async def knowledge_model_setting_detail(
    request: Request,
    user: dict = Depends(require_permission("knowledge:setting")),
    db: Session = Depends(get_db),
):
    """模型设置详情"""
    controller = KnowledgeController(dict(request.query_params))
    return _knowledge_response(controller, controller.model_setting_detail)


@router.post("/knowledge/model-setting/save")
async def knowledge_model_setting_save(
    request: Request,
    user: dict = Depends(require_permission("knowledge:setting")),
    db: Session = Depends(get_db),
):
    """保存模型设置"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.model_setting_save)


@router.post("/knowledge/model-setting/test")
async def knowledge_model_setting_test(
    request: Request,
    user: dict = Depends(require_permission("knowledge:setting")),
    db: Session = Depends(get_db),
):
    """测试模型设置"""
    body = await request.json()
    controller = KnowledgeController(body)
    return _knowledge_response(controller, controller.model_setting_test)
