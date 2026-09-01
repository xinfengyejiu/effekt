# encoding: UTF-8
"""巡检执行调度服务。"""
import logging
import threading
from datetime import datetime

from app.api.dao.inspectionDao import InspectionDao
from app.api.service.inspectionCheckers import get_checker
from app.api.service.inspectionNotifyService import InspectionNotifyService

logger = logging.getLogger(__name__)


class InspectionExecutionService(object):

    @staticmethod
    def trigger_execution(db, task_id, trigger_type='manual', user_id=None):
        """
        触发巡检任务执行（异步，在后台线程中执行）。
        返回 execution_id。
        """
        task = InspectionDao.get_task(db, task_id)
        if not task:
            return None, '任务不存在'

        items = InspectionDao.list_items_by_task(db, task_id)
        if not items:
            return None, '该任务下没有启用的巡检项'

        # 通知优先用组配置，兼容任务级遗留配置
        group = InspectionDao.get_group(db, task.group_id)
        notify_type = ''
        notify_webhook = ''
        notify_config = task.notify_config or {}
        if group:
            notify_type = group.notify_type or ''
            notify_webhook = group.notify_webhook or ''
        if not notify_type:
            notify_type = task.notify_type or ''
        if not notify_webhook:
            notify_webhook = task.notify_webhook or ''

        execution_values = {
            'task_id': task_id,
            'group_id': task.group_id,
            'project_id': task.project_id,
            'trigger_type': trigger_type,
            'status': 0,
            'total_count': len(items),
            'start_time': datetime.now(),
        }
        execution = InspectionDao.create_execution(db, execution_values)
        db.commit()

        execution_id = execution.id
        run_context = {
            'name': task.name,
            'group_id': task.group_id,
            'notify_type': notify_type,
            'notify_webhook': notify_webhook,
            'notify_config': notify_config,
        }

        thread = threading.Thread(
            target=InspectionExecutionService._run_execution,
            args=(execution_id, [i.to_dict() for i in items], run_context),
            daemon=True,
        )
        thread.start()

        return execution.to_dict(), ''

    @staticmethod
    def trigger_group_execution(db, group_id, trigger_type='manual', user_id=None):
        """
        触发巡检组执行：串行跑组内所有启用任务的启用检查项，失败汇总一次 webhook。
        """
        group = InspectionDao.get_group(db, group_id)
        if not group:
            return None, '巡检组不存在'

        tasks = InspectionDao.list_enabled_tasks_by_group(db, group_id)
        if not tasks:
            return None, '该组下没有启用的任务'

        items = []
        for task in tasks:
            task_items = InspectionDao.list_items_by_task(db, task.id)
            for item in task_items:
                d = item.to_dict()
                d['task_name'] = task.name
                d['task_id'] = task.id
                items.append(d)

        if not items:
            return None, '该组下没有启用的巡检项'

        execution_values = {
            'task_id': None,
            'group_id': group.id,
            'project_id': group.project_id,
            'trigger_type': trigger_type,
            'status': 0,
            'total_count': len(items),
            'start_time': datetime.now(),
        }
        execution = InspectionDao.create_execution(db, execution_values)

        InspectionDao.update_group(db, group.id, {'last_run_at': datetime.now()})
        db.commit()

        execution_id = execution.id
        run_context = {
            'name': group.name,
            'group_id': group.id,
            'notify_type': group.notify_type or '',
            'notify_webhook': group.notify_webhook or '',
            'notify_config': {},
        }

        thread = threading.Thread(
            target=InspectionExecutionService._run_execution,
            args=(execution_id, items, run_context),
            daemon=True,
        )
        thread.start()

        return execution.to_dict(), ''

    @staticmethod
    def _run_execution(execution_id, items, run_context):
        """后台线程：执行巡检并收集结果。"""
        from app.core.database import get_session_factory
        db = get_session_factory()()
        try:
            InspectionDao.update_execution(db, execution_id, {'status': 1, 'start_time': datetime.now()})
            db.commit()

            pass_count = 0
            fail_count = 0
            error_count = 0
            fail_items = []
            start_ts = datetime.now()

            for item in items:
                exec_item_values = {
                    'execution_id': execution_id,
                    'item_id': item['id'],
                    'item_type': item['item_type'],
                    'status': 1,
                    'start_time': datetime.now(),
                }
                exec_item = InspectionDao.create_execution_item(db, exec_item_values)
                db.commit()
                exec_item_id = exec_item.id

                display_name = item.get('name', '')
                if item.get('task_name'):
                    display_name = '{} / {}'.format(item.get('task_name'), display_name)

                try:
                    config = dict(item.get('config', {}) or {})

                    if item['item_type'] == 'sql' and config.get('db_config_id'):
                        db_config = InspectionDao.get_db_config(db, config['db_config_id'])
                        if db_config:
                            config['db_connection'] = {
                                'type': db_config.db_type,
                                'host': db_config.host,
                                'port': db_config.port,
                                'database_name': db_config.database_name,
                                'username': db_config.username,
                                'password': db_config.password,
                            }

                    checker = get_checker(item['item_type'])
                    result = checker.execute(config, timeout=item.get('timeout_seconds', 30))

                    # AI 为主：自然语言判定 + 失败自动分析
                    from app.api.service.inspectionCheckers.ai_judge import InspectionAiJudge
                    result = InspectionAiJudge.apply_ai_to_checker_result(
                        result, config, item_type=item.get('item_type', '')
                    )

                    status_map = {'pass': 2, 'fail': 3, 'error': 4, 'pending': 1}
                    exec_status = status_map.get(result['status'], 4)

                    update_values = {
                        'status': exec_status,
                        'result': result.get('result', {}),
                        'error_message': result.get('error_message', ''),
                        'duration_ms': result.get('duration_ms', 0),
                        'end_time': datetime.now(),
                    }
                    InspectionDao.update_execution_item(db, exec_item_id, update_values)
                    db.commit()

                    if result['status'] == 'pass':
                        pass_count += 1
                    elif result['status'] == 'fail':
                        fail_count += 1
                        ai_analysis = (result.get('result') or {}).get('ai_analysis') or {}
                        fail_items.append({
                            'item_type': item['item_type'],
                            'name': display_name,
                            'error_message': result.get('error_message', ''),
                            'ai_reason': ((result.get('result') or {}).get('ai_verdict') or {}).get('reason', ''),
                            'ai_root_cause': ai_analysis.get('root_cause', ''),
                            'ai_category': ai_analysis.get('category', ''),
                            'ai_suggestions': ai_analysis.get('suggestions') or [],
                        })
                    elif result['status'] == 'error':
                        error_count += 1
                        ai_analysis = (result.get('result') or {}).get('ai_analysis') or {}
                        fail_items.append({
                            'item_type': item['item_type'],
                            'name': display_name,
                            'error_message': result.get('error_message', ''),
                            'ai_reason': ((result.get('result') or {}).get('ai_verdict') or {}).get('reason', ''),
                            'ai_root_cause': ai_analysis.get('root_cause', ''),
                            'ai_category': ai_analysis.get('category', ''),
                            'ai_suggestions': ai_analysis.get('suggestions') or [],
                        })

                except Exception as e:
                    logger.error('巡检项执行异常 [item=%s]: %s', item['id'], str(e))
                    error_count += 1
                    InspectionDao.update_execution_item(db, exec_item_id, {
                        'status': 4,
                        'error_message': str(e),
                        'duration_ms': 0,
                        'end_time': datetime.now(),
                    })
                    db.commit()
                    fail_items.append({
                        'item_type': item['item_type'],
                        'name': display_name,
                        'error_message': str(e),
                    })

            total = len(items)
            if pass_count == total:
                final_status = 2
            elif fail_count + error_count == total:
                final_status = 4
            elif pass_count > 0:
                final_status = 3
            else:
                final_status = 5

            end_time = datetime.now()
            duration_ms = int((end_time - start_ts).total_seconds() * 1000)
            InspectionDao.update_execution(db, execution_id, {
                'status': final_status,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'error_count': error_count,
                'end_time': end_time,
                'duration_ms': duration_ms,
            })
            db.commit()

            execution = InspectionDao.get_execution(db, execution_id)
            if execution:
                execution_data = execution.to_dict()
                execution_data['task_name'] = run_context.get('name', '')
                execution_data['fail_items'] = fail_items

                notify_type = run_context.get('notify_type', '')
                notify_webhook = run_context.get('notify_webhook', '')
                notify_config = run_context.get('notify_config', {}) or {}

                # 失败汇总推送：仅在有失败/异常时通知
                should_notify = (
                    notify_type and notify_webhook
                    and (fail_count > 0 or error_count > 0 or final_status in (3, 4, 5))
                )
                if should_notify:
                    try:
                        success, err = InspectionNotifyService.send_notification(
                            notify_type, notify_webhook, execution_data, notify_config
                        )
                        InspectionDao.update_execution(db, execution_id, {
                            'notify_status': 1 if success else 2,
                        })
                        if err:
                            logger.warning('通知发送结果: %s', err)
                    except Exception as e:
                        logger.error('通知发送失败: %s', str(e))
                        InspectionDao.update_execution(db, execution_id, {
                            'notify_status': 2,
                        })

                db.commit()

        except Exception as e:
            logger.error('巡检执行异常 [execution=%s]: %s', execution_id, str(e))
            InspectionDao.update_execution(db, execution_id, {
                'status': 5,
                'end_time': datetime.now(),
            })
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_execution_detail(db, execution_id):
        """获取执行详情。"""
        execution = InspectionDao.get_execution(db, execution_id)
        if not execution:
            return None
        result = execution.to_dict()
        items = InspectionDao.list_execution_items(db, execution_id)
        result['items'] = [i.to_dict() for i in items]

        if execution.task_id:
            task = InspectionDao.get_task(db, execution.task_id)
            if task:
                result['task_name'] = task.name
                result['task_type'] = task.task_type
        else:
            group = InspectionDao.get_group(db, execution.group_id)
            if group:
                result['task_name'] = group.name
                result['group_name'] = group.name

        return result

    @staticmethod
    def list_executions(db, params):
        """执行记录列表。"""
        items, total = InspectionDao.list_executions(
            db,
            task_id=params.get('task_id'),
            group_id=params.get('group_id'),
            project_id=params.get('project_id'),
            status=params.get('status'),
            page_no=params.get('page_no', 1),
            page_size=params.get('page_size', 20),
        )
        result_items = []
        for i in items:
            d = i.to_dict()
            if i.task_id:
                task = InspectionDao.get_task(db, i.task_id)
                d['task_name'] = task.name if task else ''
            else:
                group = InspectionDao.get_group(db, i.group_id)
                d['task_name'] = group.name if group else ''
                d['group_name'] = group.name if group else ''
            result_items.append(d)
        return {'items': result_items, 'total': total}
