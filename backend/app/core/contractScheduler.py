# encoding: UTF-8
"""契约套件定时调度器（基于 APScheduler）。"""
import logging
import threading

logger = logging.getLogger(__name__)

_scheduler = None
_lock = threading.Lock()


class ContractScheduler(object):

    def __init__(self):
        self._scheduler = None

    def start(self):
        global _scheduler
        with _lock:
            if self._scheduler is not None:
                logger.warning('契约调度器已启动，跳过重复启动')
                return
            try:
                from apscheduler.schedulers.background import BackgroundScheduler

                self._scheduler = BackgroundScheduler(
                    timezone='Asia/Shanghai',
                    job_defaults={'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 60},
                )
                self._scheduler.start()
                _scheduler = self._scheduler
                logger.info('契约调度器已启动')
                self.load_suites()
            except ImportError:
                logger.warning('APScheduler 未安装，契约定时调度不可用')
            except Exception as e:
                logger.error('契约调度器启动失败: %s', str(e))

    def stop(self):
        global _scheduler
        with _lock:
            if self._scheduler:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None
                _scheduler = None
                logger.info('契约调度器已停止')

    def load_suites(self):
        if not self._scheduler:
            return
        try:
            from app.core.database import get_session_factory
            from app.api.dao.contractDao import ContractDao

            db = get_session_factory()()
            try:
                for job in list(self._scheduler.get_jobs()):
                    if job.id.startswith('contract_suite_'):
                        job.remove()
                suites = ContractDao.list_enabled_scheduled_suites(db)
                for suite in suites:
                    self._add_job(suite)
                logger.info('契约调度器已加载 %d 个定时套件', len(suites))
            finally:
                db.close()
        except Exception as e:
            logger.error('加载契约定时套件失败: %s', str(e))

    def _add_job(self, suite):
        if not self._scheduler:
            return
        job_id = 'contract_suite_{}'.format(suite.id)
        existing = self._scheduler.get_job(job_id)
        if existing:
            existing.remove()

        from apscheduler.triggers.interval import IntervalTrigger

        try:
            if suite.schedule_type == 'cron' and suite.cron_expression:
                trigger = self._parse_cron(suite.cron_expression)
                if not trigger:
                    return
                self._scheduler.add_job(
                    self._execute_suite,
                    trigger=trigger,
                    id=job_id,
                    args=[suite.id],
                    name='契约套件: {}'.format(suite.name),
                    replace_existing=True,
                )
            elif suite.schedule_type == 'interval' and suite.interval_seconds:
                self._scheduler.add_job(
                    self._execute_suite,
                    trigger=IntervalTrigger(seconds=int(suite.interval_seconds)),
                    id=job_id,
                    args=[suite.id],
                    name='契约套件: {}'.format(suite.name),
                    replace_existing=True,
                )
        except Exception as e:
            logger.error('注册契约套件失败 [suite=%s]: %s', suite.id, str(e))

    def _parse_cron(self, cron_expr):
        from apscheduler.triggers.cron import CronTrigger
        try:
            parts = cron_expr.strip().split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0], hour=parts[1], day=parts[2],
                    month=parts[3], day_of_week=parts[4],
                )
            if len(parts) == 6:
                return CronTrigger(
                    second=parts[0], minute=parts[1], hour=parts[2],
                    day=parts[3], month=parts[4], day_of_week=parts[5],
                )
            logger.warning('无效的 cron 表达式: %s', cron_expr)
            return None
        except Exception as e:
            logger.warning('解析 cron 失败 [%s]: %s', cron_expr, str(e))
            return None

    @staticmethod
    def _execute_suite(suite_id):
        from app.core.database import get_session_factory
        from app.api.service.contractExecutionService import ContractExecutionService

        db = get_session_factory()()
        try:
            logger.info('定时触发契约套件 [suite_id=%s]', suite_id)
            result, err = ContractExecutionService.trigger_suite_run(
                db, suite_id, trigger_type='scheduled'
            )
            if err:
                logger.error('定时契约执行失败 [suite=%s]: %s', suite_id, err)
            else:
                logger.info('定时契约执行成功 [suite=%s, run=%s]',
                            suite_id, result.get('id') if result else '')
        except Exception as e:
            logger.error('定时契约执行异常 [suite=%s]: %s', suite_id, str(e))
        finally:
            db.close()

    def reload_suite(self, suite):
        self._add_job(suite)

    def remove_suite(self, suite_id):
        if not self._scheduler:
            return
        job_id = 'contract_suite_{}'.format(suite_id)
        existing = self._scheduler.get_job(job_id)
        if existing:
            existing.remove()
            logger.info('已移除契约套件调度 [suite=%s]', suite_id)


contract_scheduler = ContractScheduler()
