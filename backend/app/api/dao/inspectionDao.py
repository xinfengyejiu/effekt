# encoding: UTF-8
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func, Integer
from app.api.model.inspectionModel import (
    InspectionGroup, InspectionTask, InspectionItem,
    InspectionDbConfig, InspectionExecution, InspectionExecutionItem,
    InspectionDailySummary
)


class InspectionDao(object):

    # ── Group ──
    @staticmethod
    def list_groups(session, project_id=None, page_no=1, page_size=20):
        query = session.query(InspectionGroup).filter(InspectionGroup.is_delete == 0)
        if project_id not in (None, ''):
            query = query.filter(InspectionGroup.project_id == int(project_id))
        total = query.count()
        items = query.order_by(InspectionGroup.updated_time.desc(), InspectionGroup.id.desc())\
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_group(session, group_id):
        return session.query(InspectionGroup).filter(
            InspectionGroup.id == int(group_id), InspectionGroup.is_delete == 0).first()

    @staticmethod
    def create_group(session, values):
        obj = InspectionGroup(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_group(session, group_id, values):
        obj = InspectionDao.get_group(session, group_id)
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def delete_group(session, group_id):
        obj = InspectionDao.get_group(session, group_id)
        if obj:
            obj.is_delete = 1
            session.flush()
        return obj

    @staticmethod
    def list_enabled_groups(session):
        """获取所有启用的且有定时配置的巡检组（供调度器加载）。"""
        return session.query(InspectionGroup).filter(
            InspectionGroup.enabled == 1,
            InspectionGroup.is_delete == 0,
            InspectionGroup.schedule_type.in_(['cron', 'interval'])
        ).all()

    @staticmethod
    def list_enabled_tasks_by_group(session, group_id):
        """组内启用任务（按 id 升序，执行时串行）。"""
        return session.query(InspectionTask).filter(
            InspectionTask.group_id == int(group_id),
            InspectionTask.is_delete == 0,
            InspectionTask.enabled == 1,
        ).order_by(InspectionTask.id.asc()).all()

    # ── Task ──
    @staticmethod
    def list_tasks(session, group_id=None, project_id=None, task_type=None, page_no=1, page_size=20):
        query = session.query(InspectionTask).filter(InspectionTask.is_delete == 0)
        if group_id not in (None, ''):
            query = query.filter(InspectionTask.group_id == int(group_id))
        if project_id not in (None, ''):
            query = query.filter(InspectionTask.project_id == int(project_id))
        if task_type not in (None, ''):
            query = query.filter(InspectionTask.task_type == task_type)
        total = query.count()
        items = query.order_by(InspectionTask.updated_time.desc(), InspectionTask.id.desc())\
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_task(session, task_id):
        return session.query(InspectionTask).filter(
            InspectionTask.id == int(task_id), InspectionTask.is_delete == 0).first()

    @staticmethod
    def create_task(session, values):
        obj = InspectionTask(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_task(session, task_id, values):
        obj = InspectionDao.get_task(session, task_id)
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def delete_task(session, task_id):
        obj = InspectionDao.get_task(session, task_id)
        if obj:
            obj.is_delete = 1
            session.flush()
        return obj

    @staticmethod
    def list_enabled_tasks(session):
        """获取所有启用的且有定时配置的任务（供调度器加载）。"""
        return session.query(InspectionTask).filter(
            InspectionTask.enabled == 1,
            InspectionTask.is_delete == 0,
            InspectionTask.schedule_type.in_(['cron', 'interval'])
        ).all()

    # ── Item ──
    @staticmethod
    def list_items(session, task_id=None, item_type=None, page_no=1, page_size=100):
        query = session.query(InspectionItem).filter(InspectionItem.is_delete == 0)
        if task_id not in (None, ''):
            query = query.filter(InspectionItem.task_id == int(task_id))
        if item_type not in (None, ''):
            query = query.filter(InspectionItem.item_type == item_type)
        total = query.count()
        items = query.order_by(InspectionItem.sort_order.asc(), InspectionItem.id.asc())\
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_item(session, item_id):
        return session.query(InspectionItem).filter(
            InspectionItem.id == int(item_id), InspectionItem.is_delete == 0).first()

    @staticmethod
    def list_items_by_task(session, task_id):
        return session.query(InspectionItem).filter(
            InspectionItem.task_id == int(task_id),
            InspectionItem.is_delete == 0,
            InspectionItem.enabled == 1
        ).order_by(InspectionItem.sort_order.asc(), InspectionItem.id.asc()).all()

    @staticmethod
    def create_item(session, values):
        obj = InspectionItem(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_item(session, item_id, values):
        obj = InspectionDao.get_item(session, item_id)
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def delete_item(session, item_id):
        obj = InspectionDao.get_item(session, item_id)
        if obj:
            obj.is_delete = 1
            session.flush()
        return obj

    # ── DbConfig ──
    @staticmethod
    def list_db_configs(session, project_id=None, page_no=1, page_size=100):
        query = session.query(InspectionDbConfig).filter(InspectionDbConfig.is_delete == 0)
        if project_id not in (None, ''):
            query = query.filter(InspectionDbConfig.project_id == int(project_id))
        total = query.count()
        items = query.order_by(InspectionDbConfig.updated_time.desc(), InspectionDbConfig.id.desc())\
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_db_config(session, config_id):
        return session.query(InspectionDbConfig).filter(
            InspectionDbConfig.id == int(config_id), InspectionDbConfig.is_delete == 0).first()

    @staticmethod
    def create_db_config(session, values):
        obj = InspectionDbConfig(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_db_config(session, config_id, values):
        obj = InspectionDao.get_db_config(session, config_id)
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def delete_db_config(session, config_id):
        obj = InspectionDao.get_db_config(session, config_id)
        if obj:
            obj.is_delete = 1
            session.flush()
        return obj

    # ── Execution ──
    @staticmethod
    def create_execution(session, values):
        obj = InspectionExecution(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def get_execution(session, execution_id):
        return session.query(InspectionExecution).filter(
            InspectionExecution.id == int(execution_id)).first()

    @staticmethod
    def update_execution(session, execution_id, values):
        obj = InspectionDao.get_execution(session, execution_id)
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def list_executions(session, task_id=None, group_id=None, project_id=None, status=None, page_no=1, page_size=20):
        query = session.query(InspectionExecution)
        if task_id not in (None, ''):
            query = query.filter(InspectionExecution.task_id == int(task_id))
        if group_id not in (None, ''):
            query = query.filter(InspectionExecution.group_id == int(group_id))
        if project_id not in (None, ''):
            query = query.filter(InspectionExecution.project_id == int(project_id))
        if status not in (None, ''):
            query = query.filter(InspectionExecution.status == int(status))
        total = query.count()
        items = query.order_by(InspectionExecution.created_time.desc())\
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def create_execution_item(session, values):
        obj = InspectionExecutionItem(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_execution_item(session, item_id, values):
        obj = session.query(InspectionExecutionItem).filter(
            InspectionExecutionItem.id == int(item_id)).first()
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def list_execution_items(session, execution_id):
        return session.query(InspectionExecutionItem).filter(
            InspectionExecutionItem.execution_id == int(execution_id)
        ).order_by(InspectionExecutionItem.id.asc()).all()

    # ── Dashboard / Report ──
    @staticmethod
    def get_dashboard_stats(session, project_id=None):
        """获取概览统计数据。"""
        base = session.query(InspectionExecution)
        if project_id not in (None, ''):
            base = base.filter(InspectionExecution.project_id == int(project_id))

        today = date.today()
        total_today = base.filter(func.date(InspectionExecution.created_time) == today).count()
        pass_today = base.filter(
            func.date(InspectionExecution.created_time) == today,
            InspectionExecution.status == 2
        ).count()
        fail_today = base.filter(
            func.date(InspectionExecution.created_time) == today,
            InspectionExecution.status.in_([3, 4])
        ).count()

        active_tasks = session.query(InspectionTask).filter(
            InspectionTask.enabled == 1, InspectionTask.is_delete == 0
        )
        if project_id not in (None, ''):
            active_tasks = active_tasks.filter(InspectionTask.project_id == int(project_id))
        active_task_count = active_tasks.count()

        return {
            'total_executions_today': total_today,
            'pass_count_today': pass_today,
            'fail_count_today': fail_today,
            'active_tasks': active_task_count,
        }

    @staticmethod
    def get_trend_data(session, project_id=None, days=7):
        """获取近 N 天趋势数据。"""
        start_date = date.today() - timedelta(days=days - 1)
        base = session.query(
            func.date(InspectionExecution.created_time).label('exec_date'),
            func.count(InspectionExecution.id).label('total'),
            func.sum(func.cast(InspectionExecution.status == 2, Integer)).label('passed'),
            func.sum(func.cast(InspectionExecution.status.in_([3, 4]), Integer)).label('failed'),
        ).filter(func.date(InspectionExecution.created_time) >= start_date)

        if project_id not in (None, ''):
            base = base.filter(InspectionExecution.project_id == int(project_id))

        base = base.group_by(func.date(InspectionExecution.created_time))\
            .order_by(func.date(InspectionExecution.created_time).asc())

        results = []
        for row in base.all():
            results.append({
                'date': str(row.exec_date),
                'total': row.total or 0,
                'passed': row.passed or 0,
                'failed': row.failed or 0,
            })
        return results
