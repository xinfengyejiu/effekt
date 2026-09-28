# encoding: UTF-8
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.ai_executor import run_in_ai_executor
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.dataBuilderController import DataBuilderController

router = APIRouter(tags=["data_builder"])


def _with_controller(req_data, action):
    controller = DataBuilderController(req_data)
    try:
        return action(controller)
    finally:
        controller.close_session()


# ==================== DataBuilder routes ====================

@router.get("/data/builder/list")
async def data_builder_list(
    request: Request,
    user: dict = Depends(require_permission("data_builder:list")),
    db: Session = Depends(get_db),
):
    """数据构建列表"""
    result = _with_controller(dict(request.query_params), lambda c: c.builder_list())
    return api_success(data=result)


@router.get("/data/builder/detail")
async def data_builder_detail(
    request: Request,
    user: dict = Depends(require_permission("data_builder:detail")),
    db: Session = Depends(get_db),
):
    """数据构建详情"""
    ret, err_msg = _with_controller(dict(request.query_params), lambda c: c.builder_detail())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data=ret)


@router.post("/data/builder/create")
async def data_builder_create(
    request: Request,
    user: dict = Depends(require_permission("data_builder:create")),
    db: Session = Depends(get_db),
):
    """创建数据构建"""
    body = await request.json()
    create_id, err_msg = _with_controller(body, lambda c: c.builder_create())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data={'id': create_id})


@router.post("/data/builder/update")
async def data_builder_update(
    request: Request,
    user: dict = Depends(require_permission("data_builder:update")),
    db: Session = Depends(get_db),
):
    """更新数据构建"""
    body = await request.json()
    update_id, err_msg = _with_controller(body, lambda c: c.builder_update())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data={'id': update_id})


@router.post("/data/builder/delete")
async def data_builder_delete(
    request: Request,
    user: dict = Depends(require_permission("data_builder:delete")),
    db: Session = Depends(get_db),
):
    """删除数据构建"""
    body = await request.json()
    delete_id, err_msg = _with_controller(body, lambda c: c.builder_delete())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data={'id': delete_id})


@router.post("/data/builder/execute")
async def data_builder_execute(
    request: Request,
    user: dict = Depends(require_permission("data_builder:execute")),
    db: Session = Depends(get_db),
):
    """执行数据构建（含 sql/set_var/assert steps）"""
    body = await request.json()
    ret, err_msg = _with_controller(body, lambda c: c.builder_execute())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data=ret)


@router.post("/data/builder/ai-generate")
async def data_builder_ai_generate(
    request: Request,
    user: dict = Depends(require_permission("data_builder:create")),
    db: Session = Depends(get_db),
):
    """自然语言生成造数场景草稿（不落库、不执行）"""
    body = await request.json()

    def _job():
        ret, err_msg = _with_controller(body, lambda c: c.ai_generate())
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)

    return await run_in_ai_executor(_job)


@router.post("/data/builder/ai-refine")
async def data_builder_ai_refine(
    request: Request,
    user: dict = Depends(require_permission("data_builder:update")),
    db: Session = Depends(get_db),
):
    """基于当前草稿按指令改一版（不落库、不执行）"""
    body = await request.json()

    def _job():
        ret, err_msg = _with_controller(body, lambda c: c.ai_refine())
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=ret)

    return await run_in_ai_executor(_job)


@router.post("/data/builder/sql-draft")
async def data_builder_sql_draft(
    request: Request,
    user: dict = Depends(require_permission("data_builder:create")),
    db: Session = Depends(get_db),
):
    """直接 SQL 收成场景草稿（不落库、不执行）"""
    body = await request.json()
    ret, err_msg = _with_controller(body, lambda c: c.draft_from_sql())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data=ret)


@router.post("/data/builder/ocr-generate")
async def data_builder_ocr_generate(
    request: Request,
    user: dict = Depends(require_permission("data_builder:create")),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    projectId: str = Form(None),
    productId: str = Form(None),
    productName: str = Form(None),
    projectName: str = Form(None),
    dbProject: str = Form(None),
    env: str = Form(None),
    prompt: str = Form(None),
):
    """截图 OCR/识图生成造数草稿（不落库、不执行）"""
    image_bytes = await file.read()
    mime = file.content_type or 'image/png'
    body = {
        'projectId': projectId,
        'productId': productId,
        'productName': productName,
        'projectName': projectName,
        'dbProject': dbProject,
        'env': env,
        'prompt': prompt,
    }

    def _job():
        controller = DataBuilderController(body)
        try:
            ret, err_msg = controller.ocr_generate(image_bytes, mime)
            if err_msg:
                return api_failure(40009, msg=err_msg)
            return api_success(data=ret)
        finally:
            controller.close_session()

    return await run_in_ai_executor(_job)


@router.post("/data/builder/save-as-scene")
async def data_builder_save_as_scene(
    request: Request,
    user: dict = Depends(require_permission("data_builder:create")),
    db: Session = Depends(get_db),
):
    """将草稿/任务另存为场景模板"""
    body = await request.json()
    create_id, err_msg = _with_controller(body, lambda c: c.save_as_scene())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data={'id': create_id})


# ==================== DataTask routes ====================

@router.get("/data/task/status")
async def data_task_status(
    request: Request,
    user: dict = Depends(require_permission("data_task:status")),
    db: Session = Depends(get_db),
):
    """数据任务状态"""
    ret, err_msg = _with_controller(dict(request.query_params), lambda c: c.task_status())
    if err_msg:
        return api_failure(40009, msg=err_msg)
    return api_success(data=ret)


@router.get("/data/task/list")
async def data_task_list(
    request: Request,
    user: dict = Depends(require_permission("data_task:status")),
    db: Session = Depends(get_db),
):
    """造数任务列表"""
    result = _with_controller(dict(request.query_params), lambda c: c.task_list())
    return api_success(data=result)
