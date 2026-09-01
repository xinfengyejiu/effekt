# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.projectController import ProjectController
from app.api.controller.projectHookController import ProjectHookController
from app.api.controller.projectCodePrdController import ProjectCodePrdController

router = APIRouter(tags=["project"])


# ==================== ProjectController routes ====================

@router.get("/project/list")
async def project_list(
    request: Request,
    user: dict = Depends(require_permission("project:list")),
    db: Session = Depends(get_db),
):
    """项目列表"""
    controller = ProjectController(dict(request.query_params))
    try:
        result = controller.project_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/project/detail")
async def project_detail(
    request: Request,
    user: dict = Depends(require_permission("project:detail")),
    db: Session = Depends(get_db),
):
    """项目详情"""
    controller = ProjectController(dict(request.query_params))
    try:
        ret, err_msg = controller.project_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/project/create")
async def project_create(
    request: Request,
    user: dict = Depends(require_permission("project:create")),
    db: Session = Depends(get_db),
):
    """创建项目"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        create_id, err_msg = controller.project_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/project/update")
async def project_update(
    request: Request,
    user: dict = Depends(require_permission("project:update")),
    db: Session = Depends(get_db),
):
    """更新项目"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        update_id, err_msg = controller.project_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/project/delete")
async def project_delete(
    request: Request,
    user: dict = Depends(require_permission("project:delete")),
    db: Session = Depends(get_db),
):
    """删除项目"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        delete_id, err_msg = controller.project_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


# ==================== Environment routes ====================

@router.get("/environment/list")
async def environment_list(
    request: Request,
    user: dict = Depends(require_permission("environment:list")),
    db: Session = Depends(get_db),
):
    """环境列表"""
    controller = ProjectController(dict(request.query_params))
    try:
        result = controller.environment_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/environment/create")
async def environment_create(
    request: Request,
    user: dict = Depends(require_permission("environment:create")),
    db: Session = Depends(get_db),
):
    """创建环境"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        create_id, err_msg = controller.environment_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/environment/update")
async def environment_update(
    request: Request,
    user: dict = Depends(require_permission("environment:update")),
    db: Session = Depends(get_db),
):
    """更新环境"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        update_id, err_msg = controller.environment_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/environment/delete")
async def environment_delete(
    request: Request,
    user: dict = Depends(require_permission("environment:delete")),
    db: Session = Depends(get_db),
):
    """删除环境"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        delete_id, err_msg = controller.environment_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


# ==================== Project Member routes ====================

@router.get("/project/member/list")
async def project_member_list(
    request: Request,
    user: dict = Depends(require_permission("project_member:list")),
    db: Session = Depends(get_db),
):
    """项目成员列表"""
    controller = ProjectController(dict(request.query_params))
    try:
        result = controller.member_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.post("/project/member/create")
async def project_member_create(
    request: Request,
    user: dict = Depends(require_permission("project_member:create")),
    db: Session = Depends(get_db),
):
    """创建项目成员"""
    body = await request.json()
    controller = ProjectController(body)
    try:
        result, err_msg = controller.member_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=result)
    finally:
        controller.close_session()


# ==================== ProjectHookController routes ====================

@router.get("/project/hook/list")
async def project_hook_list(
    request: Request,
    user: dict = Depends(require_permission("project_hook:list")),
    db: Session = Depends(get_db),
):
    """项目Hook列表"""
    controller = ProjectHookController(dict(request.query_params))
    try:
        result = controller.hook_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/project/hook/detail")
async def project_hook_detail(
    request: Request,
    user: dict = Depends(require_permission("project_hook:detail")),
    db: Session = Depends(get_db),
):
    """项目Hook详情"""
    controller = ProjectHookController(dict(request.query_params))
    try:
        ret, err_msg = controller.hook_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/project/hook/create")
async def project_hook_create(
    request: Request,
    user: dict = Depends(require_permission("project_hook:create")),
    db: Session = Depends(get_db),
):
    """创建项目Hook"""
    body = await request.json()
    controller = ProjectHookController(body)
    try:
        create_id, err_msg = controller.hook_create()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/project/hook/update")
async def project_hook_update(
    request: Request,
    user: dict = Depends(require_permission("project_hook:update")),
    db: Session = Depends(get_db),
):
    """更新项目Hook"""
    body = await request.json()
    controller = ProjectHookController(body)
    try:
        update_id, err_msg = controller.hook_update()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/project/hook/delete")
async def project_hook_delete(
    request: Request,
    user: dict = Depends(require_permission("project_hook:delete")),
    db: Session = Depends(get_db),
):
    """删除项目Hook"""
    body = await request.json()
    controller = ProjectHookController(body)
    try:
        delete_id, err_msg = controller.hook_delete()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': delete_id})
    finally:
        controller.close_session()


@router.post("/project/hook/send")
async def project_hook_send(
    request: Request,
    user: dict = Depends(require_permission("project_hook:send")),
    db: Session = Depends(get_db),
):
    """发送项目Hook"""
    body = await request.json()
    controller = ProjectHookController(body)
    try:
        success, result = controller.hook_send()
        if not success:
            return api_failure(40009, msg=str(result))
        return api_success(data=result)
    finally:
        controller.close_session()


# ==================== ProjectCodePrdController routes ====================

@router.get("/project/code-prd/config")
async def project_code_prd_config_detail(
    request: Request,
    user: dict = Depends(require_permission("project:detail")),
    db: Session = Depends(get_db),
):
    """代码PRD配置详情"""
    controller = ProjectCodePrdController(dict(request.query_params))
    try:
        ret, err_msg = controller.config_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/project/code-prd/config/save")
async def project_code_prd_config_save(
    request: Request,
    user: dict = Depends(require_permission("project:update")),
    db: Session = Depends(get_db),
):
    """保存代码PRD配置"""
    body = await request.json()
    controller = ProjectCodePrdController(body)
    try:
        save_id, err_msg = controller.config_save()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': save_id})
    finally:
        controller.close_session()


@router.get("/project/code-prd/branches")
async def project_code_prd_branches(
    request: Request,
    user: dict = Depends(require_permission("project:detail")),
    db: Session = Depends(get_db),
):
    """代码PRD分支列表"""
    controller = ProjectCodePrdController(dict(request.query_params))
    try:
        branches, err_msg = controller.branch_list()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data={'list': branches})
    finally:
        controller.close_session()


@router.get("/project/code-prd/list")
async def project_code_prd_list(
    request: Request,
    user: dict = Depends(require_permission("project:detail")),
    db: Session = Depends(get_db),
):
    """代码PRD记录列表"""
    controller = ProjectCodePrdController(dict(request.query_params))
    try:
        ret, err_msg = controller.record_list()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/project/code-prd/detail")
async def project_code_prd_detail(
    request: Request,
    user: dict = Depends(require_permission("project:detail")),
    db: Session = Depends(get_db),
):
    """代码PRD记录详情"""
    controller = ProjectCodePrdController(dict(request.query_params))
    try:
        ret, err_msg = controller.record_detail()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/project/code-prd/generate")
async def project_code_prd_generate(
    request: Request,
    user: dict = Depends(require_permission("project:update")),
    db: Session = Depends(get_db),
):
    """生成代码PRD"""
    body = await request.json()
    controller = ProjectCodePrdController(body)
    try:
        record_id, err_msg = controller.generate()
        if err_msg:
            return api_failure(40012, msg=err_msg, data={'id': record_id})
        return api_success(data={'id': record_id})
    finally:
        controller.close_session()


@router.get("/project/code-prd/export-docx")
async def project_code_prd_export_docx(
    request: Request,
    user: dict = Depends(require_permission("project:detail")),
    db: Session = Depends(get_db),
):
    """导出代码PRD文档"""
    controller = ProjectCodePrdController(dict(request.query_params))
    try:
        file_obj, filename, err_msg = controller.export_docx()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return StreamingResponse(
            file_obj,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return api_failure(40012, msg=f'导出失败：{str(e)[:100]}')
    finally:
        controller.close_session()
