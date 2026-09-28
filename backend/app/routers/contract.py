# encoding: UTF-8
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.controller.contractController import ContractController
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['contract'])


def _result(action):
    result = action()
    if isinstance(result, tuple):
        data, err_msg = result
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=data)
    return api_success(data=result)


@router.get('/contract/suite/list')
async def suite_list(request: Request, db: Session = Depends(get_db),
                     user=Depends(require_permission('contract:suite:list'))):
    return api_success(data=ContractController.list_suites(db, dict(request.query_params)))


@router.get('/contract/suite/detail')
async def suite_detail(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('contract:suite:list'))):
    suite_id = request.query_params.get('id')
    if not suite_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = ContractController.get_suite(db, suite_id)
    if not data:
        return api_failure(40011, msg='套件不存在')
    return api_success(data=data)


@router.post('/contract/suite/create')
async def suite_create(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('contract:suite:manage'))):
    body = await request.json()
    return _result(lambda: ContractController.create_suite(db, body, user.get('user_id')))


@router.post('/contract/suite/update')
async def suite_update(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('contract:suite:manage'))):
    body = await request.json()
    suite_id = body.get('id')
    if not suite_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: ContractController.update_suite(db, suite_id, body))


@router.post('/contract/suite/delete')
async def suite_delete(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('contract:suite:manage'))):
    body = await request.json()
    suite_id = body.get('id')
    if not suite_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: ContractController.delete_suite(db, suite_id))


@router.post('/contract/suite/toggle')
async def suite_toggle(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('contract:suite:manage'))):
    body = await request.json()
    suite_id = body.get('id')
    if not suite_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: ContractController.toggle_suite(db, suite_id))


@router.post('/contract/source/preview')
async def source_preview(request: Request, db: Session = Depends(get_db),
                         user=Depends(require_permission('contract:suite:manage'))):
    body = await request.json()
    return _result(lambda: ContractController.preview_source(db, body))


@router.post('/contract/suite/run')
async def suite_run(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('contract:suite:run'))):
    body = await request.json()
    suite_id = body.get('id') or body.get('suite_id')
    if not suite_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: ContractController.run_suite(db, suite_id, user.get('user_id')))


@router.get('/contract/run/list')
async def run_list(request: Request, db: Session = Depends(get_db),
                   user=Depends(require_permission('contract:run:list'))):
    return api_success(data=ContractController.list_runs(db, dict(request.query_params)))


@router.get('/contract/run/detail')
async def run_detail(request: Request, db: Session = Depends(get_db),
                     user=Depends(require_permission('contract:run:list'))):
    run_id = request.query_params.get('id')
    if not run_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = ContractController.get_run(db, run_id)
    if not data:
        return api_failure(40011, msg='执行记录不存在')
    return api_success(data=data)


@router.post('/contract/ai/design')
async def ai_design(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('contract:suite:manage'))):
    body = await request.json()
    return _result(lambda: ContractController.ai_design(body))


@router.post('/contract/ai/analyze')
async def ai_analyze(request: Request, db: Session = Depends(get_db),
                     user=Depends(require_permission('contract:run:list'))):
    body = await request.json()
    return _result(lambda: ContractController.ai_analyze(db, body))
