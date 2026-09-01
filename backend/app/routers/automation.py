# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.automationController import AutomationController

router = APIRouter(tags=["automation"])


@router.post("/automation/case/run")
async def automation_case_run(
    request: Request,
    user: dict = Depends(require_permission("automation:run")),
    db: Session = Depends(get_db),
):
    """自动化用例执行"""
    body = await request.json()
    controller = AutomationController(body)
    try:
        ret, err_msg = controller.case_run()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/automation/plan/run")
async def automation_plan_run(
    request: Request,
    user: dict = Depends(require_permission("automation:run")),
    db: Session = Depends(get_db),
):
    """自动化计划执行"""
    body = await request.json()
    controller = AutomationController(body)
    try:
        ret, err_msg = controller.plan_run()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/automation/execution/list")
async def automation_execution_list(
    request: Request,
    user: dict = Depends(require_permission("automation:list")),
    db: Session = Depends(get_db),
):
    """自动化执行列表"""
    controller = AutomationController(dict(request.query_params))
    try:
        result = controller.execution_list()
        return api_success(data=result)
    finally:
        controller.close_session()


@router.get("/automation/execution/detail")
async def automation_execution_detail(
    request: Request,
    user: dict = Depends(require_permission("automation:detail")),
    db: Session = Depends(get_db),
):
    """自动化执行详情"""
    controller = AutomationController(dict(request.query_params))
    try:
        ret, err_msg = controller.execution_detail()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.get("/automation/execution/case/list")
async def automation_execution_case_list(
    request: Request,
    user: dict = Depends(require_permission("automation:detail")),
    db: Session = Depends(get_db),
):
    """自动化执行用例列表"""
    controller = AutomationController(dict(request.query_params))
    try:
        ret, err_msg = controller.execution_case_list()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/automation/execution/poll")
async def automation_execution_poll(
    request: Request,
    user: dict = Depends(require_permission("automation:detail")),
    db: Session = Depends(get_db),
):
    """自动化执行轮询"""
    from app.api.service.jenkinsPollService import JenkinsPollService
    from app.api.dao.automationDao import AutomationDao
    from app.api.controller.baseCrudController import BaseCrudController

    req_data = await request.json()
    execution_id = req_data.get('executionId') or req_data.get('execution_id')
    controller = BaseCrudController(req_data)
    try:
        if execution_id:
            success, msg = JenkinsPollService.poll_jenkins_build_status(controller.session, execution_id)
            if not success:
                return api_failure(40012, msg=msg)
            execution = AutomationDao.get_execution_by_id(controller.session, execution_id)
            return api_success(data=execution.to_dict() if execution else {'id': execution_id, 'message': msg})
        else:
            JenkinsPollService.poll_all_pending_executions(controller.session)
            return api_success(data={'message': '轮询完成'})
    finally:
        controller.close_session()


@router.get("/automation/execution/case/pull")
async def automation_execution_case_pull(
    request: Request,
):
    """回调接口，无需认证"""
    req_data = dict(request.query_params)
    req_data['_callback_token'] = request.headers.get('X-CALLBACK-TOKEN', '')
    controller = AutomationController(req_data)
    try:
        ret, err_msg = controller.execution_case_pull()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    finally:
        controller.close_session()


@router.post("/automation/execution/queued")
async def automation_execution_queued(request: Request):
    """回调接口，无需认证，使用 X-CALLBACK-SECRET 验证"""
    req_data = await request.json()
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return api_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_queued()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/automation/execution/start")
async def automation_execution_start(request: Request):
    """回调接口，无需认证，使用 X-CALLBACK-SECRET 验证"""
    req_data = await request.json()
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return api_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_start()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/automation/execution/case/result")
async def automation_execution_case_result(request: Request):
    """回调接口，无需认证，使用 X-CALLBACK-SECRET 验证"""
    req_data = await request.json()
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return api_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_case_result()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/automation/execution/finish")
async def automation_execution_finish(request: Request):
    """回调接口，无需认证，使用 X-CALLBACK-SECRET 验证"""
    req_data = await request.json()
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return api_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_finish()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()


@router.post("/automation/execution/abort")
async def automation_execution_abort(request: Request):
    """回调接口，无需认证，使用 X-CALLBACK-SECRET 验证"""
    req_data = await request.json()
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return api_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_abort()
        if err_msg:
            return api_failure(40012, msg=err_msg)
        return api_success(data={'id': update_id})
    finally:
        controller.close_session()
