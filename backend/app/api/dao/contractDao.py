# encoding: UTF-8
"""契约测试 DAO。"""
from app.api.model.contractModel import (
    ContractSuite, ContractSuiteItem, ContractRun, ContractRunItem, ContractFinding,
)


class ContractDao(object):

    # ── Suite ──
    @staticmethod
    def list_suites(session, project_id=None, product_id=None, page_no=1, page_size=20):
        query = session.query(ContractSuite).filter(ContractSuite.is_delete == 0)
        if project_id not in (None, ''):
            query = query.filter(ContractSuite.project_id == int(project_id))
        if product_id not in (None, ''):
            query = query.filter(ContractSuite.product_id == int(product_id))
        total = query.count()
        items = query.order_by(ContractSuite.updated_time.desc(), ContractSuite.id.desc()) \
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_suite(session, suite_id):
        return session.query(ContractSuite).filter(
            ContractSuite.id == int(suite_id), ContractSuite.is_delete == 0
        ).first()

    @staticmethod
    def create_suite(session, values):
        obj = ContractSuite(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_suite(session, suite_id, values):
        obj = ContractDao.get_suite(session, suite_id)
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def delete_suite(session, suite_id):
        obj = ContractDao.get_suite(session, suite_id)
        if obj:
            obj.is_delete = 1
            session.flush()
        return obj

    @staticmethod
    def list_enabled_scheduled_suites(session):
        return session.query(ContractSuite).filter(
            ContractSuite.enabled == 1,
            ContractSuite.is_delete == 0,
            ContractSuite.schedule_type.in_(['cron', 'interval']),
        ).all()

    # ── Item ──
    @staticmethod
    def list_items(session, suite_id, enabled_only=False):
        query = session.query(ContractSuiteItem).filter(
            ContractSuiteItem.suite_id == int(suite_id),
            ContractSuiteItem.is_delete == 0,
        )
        if enabled_only:
            query = query.filter(ContractSuiteItem.enabled == 1)
        return query.order_by(ContractSuiteItem.sort_order.asc(), ContractSuiteItem.id.asc()).all()

    @staticmethod
    def soft_delete_items_by_suite(session, suite_id):
        items = session.query(ContractSuiteItem).filter(
            ContractSuiteItem.suite_id == int(suite_id),
            ContractSuiteItem.is_delete == 0,
        ).all()
        for item in items:
            item.is_delete = 1
        session.flush()

    @staticmethod
    def create_item(session, values):
        obj = ContractSuiteItem(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def replace_items(session, suite_id, item_dicts):
        ContractDao.soft_delete_items_by_suite(session, suite_id)
        created = []
        for idx, raw in enumerate(item_dicts or []):
            values = {
                'suite_id': int(suite_id),
                'mock_interface_id': raw.get('mock_interface_id'),
                'name': raw.get('name') or raw.get('path') or 'unnamed',
                'method': (raw.get('method') or 'GET').upper(),
                'path': raw.get('path') or '/',
                'path_params': raw.get('path_params') or {},
                'query_params': raw.get('query_params') or {},
                'body_template': raw.get('body_template'),
                'response_schema': raw.get('response_schema') or {},
                'timeout_seconds': int(raw.get('timeout_seconds') or 30),
                'enabled': int(raw.get('enabled', 1)),
                'sort_order': int(raw.get('sort_order', idx)),
            }
            created.append(ContractDao.create_item(session, values))
        return created

    # ── Run ──
    @staticmethod
    def create_run(session, values):
        obj = ContractRun(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def update_run(session, run_id, values):
        obj = session.query(ContractRun).filter(ContractRun.id == int(run_id)).first()
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def get_run(session, run_id):
        return session.query(ContractRun).filter(ContractRun.id == int(run_id)).first()

    @staticmethod
    def list_runs(session, project_id=None, suite_id=None, page_no=1, page_size=20):
        query = session.query(ContractRun)
        if project_id not in (None, ''):
            query = query.filter(ContractRun.project_id == int(project_id))
        if suite_id not in (None, ''):
            query = query.filter(ContractRun.suite_id == int(suite_id))
        total = query.count()
        items = query.order_by(ContractRun.id.desc()) \
            .offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def create_run_item(session, values):
        obj = ContractRunItem(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def list_run_items(session, run_id):
        return session.query(ContractRunItem).filter(
            ContractRunItem.run_id == int(run_id)
        ).order_by(ContractRunItem.id.asc()).all()

    @staticmethod
    def create_finding(session, values):
        obj = ContractFinding(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def list_findings(session, run_id, run_item_id=None):
        query = session.query(ContractFinding).filter(ContractFinding.run_id == int(run_id))
        if run_item_id not in (None, ''):
            query = query.filter(ContractFinding.run_item_id == int(run_item_id))
        return query.order_by(ContractFinding.id.asc()).all()
