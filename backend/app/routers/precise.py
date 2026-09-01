# encoding: UTF-8
"""
精准测试路由
"""
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.core.response import api_success, api_failure

router = APIRouter(prefix="/precise", tags=["precise"])


def _precise_response(controller, action, id_key="id"):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ""
        if err_msg:
            return api_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return api_success(data={id_key: ret})
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/analysis/create")
async def precise_analysis_create(
    request: Request,
    user: dict = Depends(require_permission("precise:analysis:create")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.analysis_create, "analysisId")


@router.get("/analysis/list")
async def precise_analysis_list(
    request: Request,
    user: dict = Depends(require_permission("precise:analysis:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, controller.analysis_list)


@router.get("/analysis/{analysis_id}")
async def precise_analysis_detail(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:analysis:detail")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, lambda: controller.analysis_detail(analysis_id))


@router.post("/analysis/{analysis_id}/parse-diff")
async def precise_analysis_parse_diff(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:analysis:parse")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.parse_diff(analysis_id))


@router.post("/analysis/{analysis_id}/ai-impact")
async def precise_analysis_ai_impact(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:analysis:ai")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.ai_impact(analysis_id))


@router.get("/relations/list")
async def precise_relation_list(
    request: Request,
    user: dict = Depends(require_permission("precise:relation:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, controller.relation_list)


@router.post("/relations/create")
async def precise_relation_create(
    request: Request,
    user: dict = Depends(require_permission("precise:relation:create")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.relation_create, "relationId")


@router.put("/relations/{relation_id}")
async def precise_relation_update(
    relation_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:relation:update")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.relation_update(relation_id), "relationId")


@router.delete("/relations/{relation_id}")
async def precise_relation_delete(
    relation_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:relation:delete")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    try:
        body = await request.json()
    except Exception:
        body = {}
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.relation_delete(relation_id), "relationId")


@router.post("/relations/import")
async def precise_relation_import(
    request: Request,
    user: dict = Depends(require_permission("precise:relation:import")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.relation_import)


@router.post("/analysis/{analysis_id}/recommend")
async def precise_recommendation_generate(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:recommend:create")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.recommendation_generate(analysis_id))


@router.get("/analysis/{analysis_id}/recommendations")
async def precise_recommendation_list(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:recommend:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, lambda: controller.recommendation_list(analysis_id))


@router.post("/recommendations/accept")
async def precise_recommendation_accept(
    request: Request,
    user: dict = Depends(require_permission("precise:recommend:accept")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.recommendation_accept)


@router.post("/analysis/{analysis_id}/execute")
async def precise_execute(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:execute:create")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.execute(analysis_id))


@router.post("/executions/sync-jenkins")
async def precise_execution_sync_jenkins(
    request: Request,
    user: dict = Depends(require_permission("precise:execution:sync")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.sync_jenkins)


@router.get("/executions/list")
async def precise_execution_list(
    request: Request,
    user: dict = Depends(require_permission("precise:execution:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, controller.execution_list)


@router.get("/executions/{execution_id}")
async def precise_execution_detail(
    execution_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:execution:list")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, lambda: controller.execution_detail(execution_id))


@router.post("/coverage/upload")
async def precise_coverage_upload(
    request: Request,
    user: dict = Depends(require_permission("precise:coverage:upload")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.coverage_upload)


@router.get("/coverage/list")
async def precise_coverage_list(
    request: Request,
    user: dict = Depends(require_permission("precise:coverage:detail")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, controller.coverage_list)


@router.post("/coverage/pull-from-jenkins")
async def precise_coverage_pull_from_jenkins(
    request: Request,
    user: dict = Depends(require_permission("precise:coverage:pull")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, controller.coverage_pull_from_jenkins)


@router.get("/coverage/{coverage_id}")
async def precise_coverage_detail(
    coverage_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:coverage:detail")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, lambda: controller.coverage_detail(coverage_id))


@router.post("/coverage/{coverage_id}/calculate-incremental")
async def precise_coverage_calculate_incremental(
    coverage_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:coverage:calculate")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.calculate_incremental(coverage_id))


@router.post("/coverage/{coverage_id}/ai-risk-analysis")
async def precise_coverage_ai_risk_analysis(
    coverage_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:coverage:ai")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.ai_risk_analysis(coverage_id))


@router.post("/gate/evaluate")
async def precise_gate_evaluate(
    request: Request,
    user: dict = Depends(require_permission("precise:gate:evaluate")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    body = await request.json()
    analysis_id = body.get("analysis_id") or body.get("analysisId")
    controller = PreciseTestController(body)
    return _precise_response(controller, lambda: controller.gate_evaluate(analysis_id))


@router.get("/gate/result/{analysis_id}")
async def precise_gate_result(
    analysis_id: int,
    request: Request,
    user: dict = Depends(require_permission("precise:gate:result")),
    db: Session = Depends(get_db),
):
    from app.api.controller.preciseTestController import PreciseTestController
    controller = PreciseTestController(dict(request.query_params))
    return _precise_response(controller, lambda: controller.gate_result(analysis_id))
