# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.testAssetGovernanceController import TestAssetGovernanceController

router = APIRouter(tags=["test_asset"])


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


# ==================== Scan routes ====================

@router.post("/test-asset/governance/scan/create")
async def test_asset_scan_create(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:create")),
    db: Session = Depends(get_db),
):
    """创建扫描"""
    body = await request.json()
    controller = TestAssetGovernanceController(body)
    return _ai_response(controller, controller.scan_create, id_key='scanId')


@router.get("/test-asset/governance/scan/list")
async def test_asset_scan_list(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:list")),
    db: Session = Depends(get_db),
):
    """扫描列表"""
    controller = TestAssetGovernanceController(dict(request.query_params))
    return _ai_response(controller, controller.scan_list)


@router.get("/test-asset/governance/scan/detail")
async def test_asset_scan_detail(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:detail")),
    db: Session = Depends(get_db),
):
    """扫描详情"""
    controller = TestAssetGovernanceController(dict(request.query_params))
    return _ai_response(controller, controller.scan_detail)


@router.post("/test-asset/governance/scan/execute")
async def test_asset_scan_execute(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:execute")),
    db: Session = Depends(get_db),
):
    """执行扫描"""
    body = await request.json()
    controller = TestAssetGovernanceController(body)
    return _ai_response(controller, controller.scan_execute)


# ==================== Issue routes ====================

@router.get("/test-asset/governance/issue/list")
async def test_asset_issue_list(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:list")),
    db: Session = Depends(get_db),
):
    """问题列表"""
    controller = TestAssetGovernanceController(dict(request.query_params))
    return _ai_response(controller, controller.issue_list)


@router.post("/test-asset/governance/issue/update")
async def test_asset_issue_update(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:issue:update")),
    db: Session = Depends(get_db),
):
    """更新问题"""
    body = await request.json()
    controller = TestAssetGovernanceController(body)
    return _ai_response(controller, controller.issue_update, id_key='issueId')


# ==================== Action routes ====================

@router.post("/test-asset/governance/action/apply")
async def test_asset_action_apply(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:action")),
    db: Session = Depends(get_db),
):
    """应用变更"""
    body = await request.json()
    controller = TestAssetGovernanceController(body)
    return _ai_response(controller, controller.action_apply)


@router.post("/test-asset/governance/action/rollback")
async def test_asset_action_rollback(
    request: Request,
    user: dict = Depends(require_permission("test_asset_governance:action")),
    db: Session = Depends(get_db),
):
    """回滚变更"""
    body = await request.json()
    controller = TestAssetGovernanceController(body)
    return _ai_response(controller, controller.action_rollback)
