# encoding: UTF-8
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.controller.mobileAutomationController import MobileAutomationController
from app.api.dao.mobileAutomationDao import MobileAutomationDao
from app.api.service.mobileArtifactService import MobileArtifactService
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['mobile_automation'])


def _result(action, id_key='id'):
    result = action()
    if isinstance(result, tuple):
        data, err_msg = result
        if err_msg:
            return api_failure(40009, msg=err_msg)
    else:
        data = result
    return api_success(data={id_key: data} if isinstance(data, int) else data)


@router.get('/mobile_automation/environment/check')
async def environment_check(user=Depends(require_permission('mobile_automation:device:list'))):
    return api_success(data=MobileAutomationController.environment_check())


@router.post('/mobile_automation/environment/start_appium')
async def environment_start_appium(user=Depends(require_permission('mobile_automation:device:list'))):
    return _result(lambda: MobileAutomationController.start_appium())


@router.get('/mobile_automation/device/scan')
async def device_scan(db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:device:manage'))):
    try:
        return api_success(data={'list': MobileAutomationController.scan_devices(db)})
    except Exception as exc:
        return api_failure(40011, msg='设备扫描失败：{0}'.format(str(exc)[:300]))


@router.get('/mobile_automation/device/list')
async def device_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:device:list'))):
    return api_success(data=MobileAutomationController.list_devices(db, dict(request.query_params)))


@router.post('/mobile_automation/device/update')
async def device_update(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:device:manage'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.update_device(db, body))


@router.post('/mobile_automation/page/snapshot')
async def page_snapshot(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.page_snapshot(db, body))


@router.get('/mobile_automation/app/list')
async def app_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:app:list'))):
    return api_success(data=MobileAutomationController.list_apps(db, dict(request.query_params)))


@router.post('/mobile_automation/app/create')
async def app_create(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:app:manage'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.create_app(db, body, user.get('user_id')), 'id')


@router.post('/mobile_automation/app/update')
async def app_update(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:app:manage'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.update_app(db, body), 'id')


@router.post('/mobile_automation/app/delete')
async def app_delete(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:app:manage'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.delete_app(db, body.get('id')), 'id')


@router.get('/mobile_automation/config/list')
async def config_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:list'))):
    return api_success(data=MobileAutomationController.list_configs(db, dict(request.query_params)))


@router.get('/mobile_automation/config/detail')
async def config_detail(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return _result(lambda: MobileAutomationController.get_config(db, request.query_params.get('id')))


@router.post('/mobile_automation/config/save')
async def config_save(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.save_config(db, body, user.get('user_id')))


@router.post('/mobile_automation/config/delete')
async def config_delete(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.delete_config(db, body.get('id')), 'id')


@router.post('/mobile_automation/config/run')
async def config_run(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.run_config(db, body.get('id'), user.get('user_id')))


@router.post('/mobile_automation/execution/create')
async def execution_create(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.create_execution(db, body, user.get('user_id')))


@router.post('/mobile_automation/execution/retry')
async def execution_retry(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.retry_execution(db, body.get('execution_id'), user.get('user_id')))


@router.post('/mobile_automation/execution/cancel')
async def execution_cancel(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:cancel'))):
    body = await request.json()
    return _result(lambda: MobileAutomationController.cancel_execution(db, body.get('execution_id')), 'execution_id')


@router.get('/mobile_automation/execution/list')
async def execution_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:list'))):
    return api_success(data=MobileAutomationController.list_executions(db, dict(request.query_params)))


@router.get('/mobile_automation/execution/detail')
async def execution_detail(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return _result(lambda: MobileAutomationController.execution_detail(db, request.query_params.get('execution_id')))


@router.get('/mobile_automation/execution/progress')
async def execution_progress(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return _result(lambda: MobileAutomationController.execution_progress(db, request.query_params.get('execution_id')))


@router.get('/mobile_automation/execution/case/list')
async def execution_case_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return api_success(data=MobileAutomationController.execution_cases(db, request.query_params.get('execution_id')))


@router.get('/mobile_automation/execution/step/list')
async def execution_step_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return api_success(data=MobileAutomationController.execution_steps(
        db, request.query_params.get('execution_id'), request.query_params.get('execution_case_id')
    ))


@router.get('/mobile_automation/artifact/list')
async def artifact_list(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return api_success(data=MobileAutomationController.execution_artifacts(
        db, request.query_params.get('execution_id'), request.query_params.get('execution_case_id')
    ))


@router.get('/mobile_automation/artifact/download')
async def artifact_download(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    artifact = MobileAutomationDao.get_artifact(db, request.query_params.get('artifact_id'))
    if not artifact:
        return api_failure(40011, msg='产物不存在')
    try:
        return FileResponse(MobileArtifactService.resolve_relative_path(artifact.relative_path), filename=artifact.relative_path.rsplit('/', 1)[-1])
    except ValueError as exc:
        return api_failure(40011, msg=str(exc))


@router.get('/mobile_automation/artifact/preview')
async def artifact_preview(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    return await artifact_download(request, db, user)


# ── AI 相关 ─────────────────────────────────────────────────

@router.post('/mobile_automation/ai/verify')
async def ai_verify_case(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:detail'))):
    body = await request.json()
    case_id = body.get('execution_case_id')
    if not case_id:
        return api_failure(40009, msg='execution_case_id 为必传参数')
    result, error = MobileAutomationController.ai_verify_execution_case(db, case_id)
    if error:
        return api_failure(40011, msg=error)
    return api_success(data=result)


@router.post('/mobile_automation/ai/generate-scripts')
async def ai_generate_scripts(request: Request, db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    body = await request.json()
    result, error = MobileAutomationController.ai_generate_scripts(db, body, user.get('user_id'))
    if error:
        return api_failure(40011, msg=error)
    return api_success(data=result)


@router.post('/mobile_automation/ai/generate-and-debug-scripts')
def ai_generate_and_debug_scripts(body: dict = Body(...), db: Session = Depends(get_db), user=Depends(require_permission('mobile_automation:run'))):
    result, error = MobileAutomationController.ai_generate_and_debug_scripts(db, body, user.get('user_id'))
    if error:
        return api_failure(40011, msg=error)
    return api_success(data=result)
