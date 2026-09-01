# encoding: UTF-8
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.controller.inspectionController import InspectionController
from app.core.database import get_db
from app.core.response import api_failure, api_success
from app.core.security import require_permission

router = APIRouter(tags=['inspection'])


def _result(action):
    result = action()
    if isinstance(result, tuple):
        data, err_msg = result
        if err_msg:
            return api_failure(40009, msg=err_msg)
    else:
        data = result
    return api_success(data=data)


# ═══════════════════════════════════════════════
# 巡检组
# ═══════════════════════════════════════════════

@router.get('/inspection/group/list')
async def group_list(request: Request, db: Session = Depends(get_db),
                     user=Depends(require_permission('inspection:group:list'))):
    return api_success(data=InspectionController.list_groups(db, dict(request.query_params)))


@router.get('/inspection/group/detail')
async def group_detail(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:group:list'))):
    group_id = request.query_params.get('id')
    if not group_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.get_group(db, group_id)
    if not data:
        return api_failure(40011, msg='巡检组不存在')
    return api_success(data=data)


@router.post('/inspection/group/create')
async def group_create(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:group:manage'))):
    body = await request.json()
    return _result(lambda: InspectionController.create_group(db, body, user.get('user_id')))


@router.post('/inspection/group/update')
async def group_update(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:group:manage'))):
    body = await request.json()
    group_id = body.get('id')
    if not group_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.update_group(db, group_id, body)
    if not data:
        return api_failure(40011, msg='巡检组不存在')
    return api_success(data=data)


@router.post('/inspection/group/delete')
async def group_delete(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:group:manage'))):
    body = await request.json()
    group_id = body.get('id')
    if not group_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: InspectionController.delete_group(db, group_id))


@router.post('/inspection/group/toggle')
async def group_toggle(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:group:manage'))):
    body = await request.json()
    group_id = body.get('id')
    if not group_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.toggle_group(db, group_id)
    if not data:
        return api_failure(40011, msg='巡检组不存在')
    return api_success(data=data)


@router.post('/inspection/group/run')
async def group_run(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('inspection:task:execute'))):
    body = await request.json()
    group_id = body.get('id') or body.get('group_id')
    if not group_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: InspectionController.execute_group(db, group_id, user.get('user_id')))


# ═══════════════════════════════════════════════
# 巡检任务
# ═══════════════════════════════════════════════

@router.get('/inspection/task/list')
async def task_list(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('inspection:task:list'))):
    return api_success(data=InspectionController.list_tasks(db, dict(request.query_params)))


@router.get('/inspection/task/detail')
async def task_detail(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:list'))):
    task_id = request.query_params.get('id')
    if not task_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.get_task_detail(db, task_id)
    if not data:
        return api_failure(40011, msg='巡检任务不存在')
    return api_success(data=data)


@router.post('/inspection/task/create')
async def task_create(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    return _result(lambda: InspectionController.create_task(db, body, user.get('user_id')))


@router.post('/inspection/task/update')
async def task_update(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    task_id = body.get('id')
    if not task_id:
        return api_failure(40009, msg='缺少 id 参数')
    body['updated_by'] = user.get('user_id')
    data = InspectionController.update_task(db, task_id, body)
    if not data:
        return api_failure(40011, msg='巡检任务不存在')
    return api_success(data=data)


@router.post('/inspection/task/delete')
async def task_delete(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    task_id = body.get('id')
    if not task_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: InspectionController.delete_task(db, task_id))


@router.post('/inspection/task/toggle')
async def task_toggle(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    task_id = body.get('id')
    if not task_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.toggle_task(db, task_id)
    if not data:
        return api_failure(40011, msg='巡检任务不存在')
    return api_success(data=data)


@router.post('/inspection/task/execute')
async def task_execute(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:task:execute'))):
    body = await request.json()
    task_id = body.get('id')
    if not task_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: InspectionController.execute_task(db, task_id, user.get('user_id')))


# ═══════════════════════════════════════════════
# 巡检项
# ═══════════════════════════════════════════════

@router.get('/inspection/item/list')
async def item_list(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('inspection:task:list'))):
    return api_success(data=InspectionController.list_items(db, dict(request.query_params)))


@router.post('/inspection/item/create')
async def item_create(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    return _result(lambda: InspectionController.create_item(db, body))


@router.post('/inspection/item/update')
async def item_update(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    item_id = body.get('id')
    if not item_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.update_item(db, item_id, body)
    if not data:
        return api_failure(40011, msg='巡检项不存在')
    return api_success(data=data)


@router.post('/inspection/item/delete')
async def item_delete(request: Request, db: Session = Depends(get_db),
                      user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    item_id = body.get('id')
    if not item_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: InspectionController.delete_item(db, item_id))


@router.post('/inspection/item/batch-create')
async def item_batch_create(request: Request, db: Session = Depends(get_db),
                            user=Depends(require_permission('inspection:task:manage'))):
    body = await request.json()
    task_id = body.get('task_id')
    items = body.get('items', [])
    if not task_id:
        return api_failure(40009, msg='缺少 task_id 参数')
    if not items:
        return api_failure(40009, msg='巡检项列表为空')
    return api_success(data=InspectionController.batch_create_items(db, task_id, items))


@router.post('/inspection/item/test')
async def item_test(request: Request, db: Session = Depends(get_db),
                    user=Depends(require_permission('inspection:task:manage'))):
    """单项测试执行。"""
    body = await request.json()
    return api_success(data=InspectionController.test_item(db, body))


# ═══════════════════════════════════════════════
# 数据库连接配置
# ═══════════════════════════════════════════════

@router.get('/inspection/db-config/list')
async def db_config_list(request: Request, db: Session = Depends(get_db),
                         user=Depends(require_permission('inspection:dbconfig:list'))):
    return api_success(data=InspectionController.list_db_configs(db, dict(request.query_params)))


@router.post('/inspection/db-config/create')
async def db_config_create(request: Request, db: Session = Depends(get_db),
                           user=Depends(require_permission('inspection:dbconfig:manage'))):
    body = await request.json()
    return _result(lambda: InspectionController.create_db_config(db, body, user.get('user_id')))


@router.post('/inspection/db-config/update')
async def db_config_update(request: Request, db: Session = Depends(get_db),
                           user=Depends(require_permission('inspection:dbconfig:manage'))):
    body = await request.json()
    config_id = body.get('id')
    if not config_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.update_db_config(db, config_id, body)
    if not data:
        return api_failure(40011, msg='数据库连接不存在')
    return api_success(data=data)


@router.post('/inspection/db-config/delete')
async def db_config_delete(request: Request, db: Session = Depends(get_db),
                           user=Depends(require_permission('inspection:dbconfig:manage'))):
    body = await request.json()
    config_id = body.get('id')
    if not config_id:
        return api_failure(40009, msg='缺少 id 参数')
    return _result(lambda: InspectionController.delete_db_config(db, config_id))


@router.post('/inspection/db-config/test')
async def db_config_test(request: Request, db: Session = Depends(get_db),
                         user=Depends(require_permission('inspection:dbconfig:manage'))):
    """测试数据库连接。"""
    body = await request.json()
    return _result(lambda: InspectionController.test_db_connection(db, body))


# ═══════════════════════════════════════════════
# 执行记录
# ═══════════════════════════════════════════════

@router.get('/inspection/execution/list')
async def execution_list(request: Request, db: Session = Depends(get_db),
                         user=Depends(require_permission('inspection:execution:list'))):
    return api_success(data=InspectionController.list_executions(db, dict(request.query_params)))


@router.get('/inspection/execution/detail')
async def execution_detail(request: Request, db: Session = Depends(get_db),
                           user=Depends(require_permission('inspection:execution:list'))):
    execution_id = request.query_params.get('id')
    if not execution_id:
        return api_failure(40009, msg='缺少 id 参数')
    data = InspectionController.get_execution_detail(db, execution_id)
    if not data:
        return api_failure(40011, msg='执行记录不存在')
    return api_success(data=data)


# ═══════════════════════════════════════════════
# 统计报表
# ═══════════════════════════════════════════════

@router.get('/inspection/report/dashboard')
async def report_dashboard(request: Request, db: Session = Depends(get_db),
                           user=Depends(require_permission('inspection:report'))):
    project_id = request.query_params.get('project_id')
    return api_success(data=InspectionController.get_dashboard(db, project_id))


@router.get('/inspection/report/trend')
async def report_trend(request: Request, db: Session = Depends(get_db),
                       user=Depends(require_permission('inspection:report'))):
    project_id = request.query_params.get('project_id')
    days = int(request.query_params.get('days', 7))
    return api_success(data=InspectionController.get_trend(db, project_id, days))
