# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.aiWorkloadEstimateController import AiWorkloadEstimateController

router = APIRouter()


def _ai_response(controller, action, id_key='id'):
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


@router.post("/ai/workload-estimate/create")
async def ai_workload_estimate_create(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:create")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.estimate_create, id_key='estimateId')


@router.get("/ai/workload-estimate/list")
async def ai_workload_estimate_list(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:list")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(dict(request.query_params))
    return _ai_response(controller, controller.estimate_list)


@router.get("/ai/workload-estimate/detail")
async def ai_workload_estimate_detail(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:detail")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(dict(request.query_params))
    return _ai_response(controller, controller.estimate_detail)


@router.get("/ai/workload-estimate/export")
async def ai_workload_estimate_export(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:detail")),
    db: Session = Depends(get_db),
):
    from fastapi.responses import StreamingResponse
    controller = AiWorkloadEstimateController(dict(request.query_params))
    try:
        file_obj, filename, err_msg = controller.estimate_export()
        if err_msg:
            return api_failure(40003, msg=err_msg)
        return StreamingResponse(file_obj, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    finally:
        controller.close_session()


@router.post("/ai/workload-estimate/execute")
async def ai_workload_estimate_execute(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:execute")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.estimate_execute)


@router.post("/ai/workload-estimate/assign")
async def ai_workload_estimate_assign(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:assign")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.estimate_assign, id_key='estimateId')


@router.post("/ai/workload-estimate/delete")
async def ai_workload_estimate_delete(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:delete")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.estimate_delete, id_key='estimateId')


@router.post("/ai/workload-estimate/actual/save")
async def ai_workload_estimate_actual_save(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:actual:update")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.actual_save)


@router.post("/ai/workload-estimate/confirm")
async def ai_workload_estimate_confirm(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:confirm")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.estimate_confirm, id_key='estimateId')


@router.post("/ai/workload-estimate/retry")
async def ai_workload_estimate_retry(
    request: Request,
    user: dict = Depends(require_permission("ai_workload_estimate:execute")),
    db: Session = Depends(get_db),
):
    controller = AiWorkloadEstimateController(await request.json())
    return _ai_response(controller, controller.estimate_retry)
