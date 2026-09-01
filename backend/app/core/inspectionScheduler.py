# encoding: UTF-8
"""巡检系统定时调度器（基于 APScheduler，组级调度）。"""
import logging
import threading

logger = logging.getLogger(__name__)

_scheduler = None
_lock = threading.Lock()


def get_scheduler():
    """获取调度器单例。"""
    return _scheduler


class InspectionScheduler(object):
    """巡检定时调度管理器（按巡检组注册 job）。"""

    def __init__(self):
        self._scheduler = None

    def start(self):
        """启动调度器并加载所有启用的定时组。"""
        global _scheduler
        with _lock:
            if self._scheduler is not None:
                logger.warning('巡检调度器已启动，跳过重复启动')
                return

            try:
                from apscheduler.schedulers.background import BackgroundScheduler

                self._scheduler = BackgroundScheduler(
                    timezone='Asia/Shanghai',
                    job_defaults={'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 60},
                )
                self._scheduler.start()
                _scheduler = self._scheduler
                logger.info('巡检调度器已启动')
                self.load_groups()

            except ImportError:
                logger.warning('APScheduler 未安装，巡检定时调度功能不可用。请执行: pip install apscheduler')
            except Exception as e:
                logger.error('巡检调度器启动失败: %s', str(e))

    def stop(self):
        """停止调度器。"""
        global _scheduler
        with _lock:
            if self._scheduler:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None
                _scheduler = None
                logger.info('巡检调度器已停止')

    def load_groups(self):
        """从数据库加载所有启用的定时巡检组。"""
        if not self._scheduler:
            return

        try:
            from app.core.database import get_session_factory
            from app.api.dao.inspectionDao import InspectionDao

            db = get_session_factory()()
            try:
                # 清理旧的任务级 job（兼容升级前残留）
                for job in list(self._scheduler.get_jobs()):
                    if job.id.startswith('inspection_task_') or job.id.startswith('inspection_group_'):
                        job.remove()

                groups = InspectionDao.list_enabled_groups(db)
                count = 0
                for group in groups:
                    self._add_job(group)
                    count += 1
                logger.info('巡检调度器已加载 %d 个定时组', count)
            finally:
                db.close()
        except Exception as e:
            logger.error('加载巡检定时组失败: %s', str(e))

    # 兼容旧调用名
    def load_tasks(self):
        self.load_groups()

    def _add_job(self, group):
        """为单个巡检组注册调度 job。"""
        if not self._scheduler:
            return

        job_id = 'inspection_group_{}'.format(group.id)
        existing = self._scheduler.get_job(job_id)
        if existing:
            existing.remove()

        from apscheduler.triggers.interval import IntervalTrigger

        try:
            if group.schedule_type == 'cron' and group.cron_expression:
                trigger = self._parse_cron(group.cron_expression)
                if trigger:
                    self._scheduler.add_job(
                        self._execute_group,
                        trigger=trigger,
                        id=job_id,
                        args=[group.id],
                        name='巡检组: {}'.format(group.name),
                        replace_existing=True,
                    )
                    logger.info('注册定时组: %s (cron=%s)', group.name, group.cron_expression)

            elif group.schedule_type == 'interval' and group.interval_seconds:
                trigger = IntervalTrigger(seconds=group.interval_seconds)
                self._scheduler.add_job(
                    self._execute_group,
                    trigger=trigger,
                    id=job_id,
                    args=[group.id],
                    name='巡检组: {}'.format(group.name),
                    replace_existing=True,
                )
                logger.info('注册间隔组: %s (interval=%ds)', group.name, group.interval_seconds)

        except Exception as e:
            logger.error('注册巡检组失败 [group=%s]: %s', group.id, str(e))

    def _parse_cron(self, cron_expr):
        """
        解析 cron 表达式为 APScheduler CronTrigger。
        支持标准 5 段格式: minute hour day_of_month month day_of_week
        """
        from apscheduler.triggers.cron import CronTrigger

        try:
            parts = cron_expr.strip().split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
            elif len(parts) == 6:
                return CronTrigger(
                    second=parts[0],
                    minute=parts[1],
                    hour=parts[2],
                    day=parts[3],
                    month=parts[4],
                    day_of_week=parts[5],
                )
            else:
                logger.warning('无效的 cron 表达式: %s', cron_expr)
                return None
        except Exception as e:
            logger.warning('解析 cron 表达式失败 [%s]: %s', cron_expr, str(e))
            return None

    @staticmethod
    def _execute_group(group_id):
        """调度器回调：执行巡检组。"""
        from app.core.database import get_session_factory
        from app.api.service.inspectionExecutionService import InspectionExecutionService

        db = get_session_factory()()
        try:
            logger.info('定时触发巡检组 [group_id=%s]', group_id)
            result, err = InspectionExecutionService.trigger_group_execution(
                db, group_id, trigger_type='scheduled'
            )
            if err:
                logger.error('定时触发巡检组失败 [group=%s]: %s', group_id, err)
            else:
                logger.info(
                    '定时触发巡检组成功 [group=%s, execution=%s]',
                    group_id, result.get('id') if result else '',
                )
        except Exception as e:
            logger.error('定时触发巡检组异常 [group=%s]: %s', group_id, str(e))
        finally:
            db.close()

    def reload_group(self, group):
        """重新加载单个组（组更新后调用）。"""
        self._add_job(group)

    def remove_group(self, group_id):
        """移除单个组的调度。"""
        if not self._scheduler:
            return
        job_id = 'inspection_group_{}'.format(group_id)
        existing = self._scheduler.get_job(job_id)
        if existing:
            existing.remove()
            logger.info('已移除巡检组调度 [group=%s]', group_id)

    # 兼容旧任务级 API（不再注册任务级 job）
    def reload_task(self, task):
        logger.debug('reload_task 已弃用，请使用组级调度')

    def remove_task(self, task_id):
        if not self._scheduler:
            return
        job_id = 'inspection_task_{}'.format(task_id)
        existing = self._scheduler.get_job(job_id)
        if existing:
            existing.remove()

    def get_jobs(self):
        """获取所有调度中的任务（供管理接口使用）。"""
        if not self._scheduler:
            return []
        jobs = self._scheduler.get_jobs()
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger),
            }
            for job in jobs
        ]


# 全局单例
inspection_scheduler = InspectionScheduler()
