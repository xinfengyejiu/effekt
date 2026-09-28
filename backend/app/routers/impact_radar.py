# encoding: UTF-8
"""变更影响雷达 API。"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.service.impactRadarService import ImpactRadarService
from app.core.ai_executor import run_in_ai_executor
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import get_current_user, require_permission

router = APIRouter(prefix='/impact-radar', tags=['impact-radar'])


def _result(action):
    result = action()
    if isinstance(result, tuple):
        data, err_msg = result
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data=data)
    return api_success(data=result)


@router.post('/parse-url')
async def parse_url(request: Request, user=Depends(get_current_user)):
    body = await request.json()
    git_url = (body or {}).get('git_url') or (body or {}).get('gitUrl') or ''
    return _result(lambda: ImpactRadarService.parse_url(git_url))


@router.post('/trace')
async def trace_code(request: Request, db: Session = Depends(get_db),
                     user=Depends(require_permission('precise:radar:list'))):
    """输入文件路径 + 代码片段，追溯对应 Git commit id 与提交时间。"""
    body = await request.json()
    return await run_in_ai_executor(lambda: _result(lambda: ImpactRadarService.trace_code(body)))


@router.post('/run')
async def run_radar(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('precise:radar:run'))):
    body = await request.json()
    user_copy = dict(user or {})
    return await run_in_ai_executor(lambda: _result(lambda: ImpactRadarService.run(body, user_copy)))


@router.get('/run/list')
async def run_list(request: Request, db: Session = Depends(get_db),
                   user=Depends(require_permission('precise:radar:list'))):
    params = dict(request.query_params)
    page_no = int(params.get('pageNo') or params.get('page') or 1)
    page_size = int(params.get('pageSize') or params.get('size') or 20)
    return _result(lambda: ImpactRadarService.list_runs(params, page_no, page_size))


@router.get('/run/detail')
async def run_detail(request: Request, db: Session = Depends(get_db),
                     user=Depends(require_permission('precise:radar:list'))):
    params = dict(request.query_params)
    analysis_id = params.get('id') or params.get('analysis_id') or params.get('analysisId')
    if not analysis_id:
        return api_failure(40009, msg='缺少 id / analysis_id')
    return _result(lambda: ImpactRadarService.detail(int(analysis_id)))


@router.post('/run/lineage')
async def run_lineage(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('precise:radar:run'))):
    body = await request.json()
    analysis_id = body.get('id') or body.get('analysis_id') or body.get('analysisId')
    if not analysis_id:
        return api_failure(40009, msg='缺少 analysis_id')
    options = body.get('options') or {}
    return await run_in_ai_executor(
        lambda: _result(lambda: ImpactRadarService.recompute_lineage(int(analysis_id), options))
    )
