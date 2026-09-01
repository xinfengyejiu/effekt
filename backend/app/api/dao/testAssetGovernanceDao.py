# encoding: UTF-8
from sqlalchemy import or_

from logger import logger
from ..model.testAssetGovernanceModel import TestAssetAction, TestAssetIssue


class TestAssetGovernanceDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__} create failed: {err}')
            return None, f'新增失败：{err}'
        return obj, ''

    @staticmethod
    def batch_create(session, model_cls, rows):
        objs = [model_cls(**row) for row in rows]
        if objs:
            session.add_all(objs)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__} batch create failed: {err}')
            return [], f'批量新增失败：{err}'
        return objs, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        update_res = session.query(model_cls).filter(*filters).update(update_info)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__} update failed: {err}')
            return 0, f'更新失败：{err}'
        if not update_res:
            return 0, '未查询到对应记录'
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def list_scans(session, model_cls, req_data):
        query = session.query(model_cls).filter(model_cls.is_delete == 0)
        for req_key, column in [
            ('productId', model_cls.product_id),
            ('projectId', model_cls.project_id),
        ]:
            value = TestAssetGovernanceDao._get(req_data, req_key, TestAssetGovernanceDao._camel_to_snake(req_key))
            if value not in (None, ''):
                query = query.filter(column == int(value))
        for req_key, column in [
            ('status', model_cls.status),
            ('scanType', model_cls.scan_type),
        ]:
            value = TestAssetGovernanceDao._get(req_data, req_key, TestAssetGovernanceDao._camel_to_snake(req_key))
            if value not in (None, ''):
                query = query.filter(column == value)
        keyword = req_data.get('keyword')
        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(or_(model_cls.scan_no.like(like_keyword), model_cls.title.like(like_keyword)))
        total = query.count()
        page, limit = TestAssetGovernanceDao._page(req_data)
        items = query.order_by(model_cls.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_issues(session, req_data):
        query = session.query(TestAssetIssue).filter(TestAssetIssue.is_delete == 0)
        for req_key, column in [
            ('scanId', TestAssetIssue.scan_id),
            ('productId', TestAssetIssue.product_id),
            ('projectId', TestAssetIssue.project_id),
            ('moduleId', TestAssetIssue.module_id),
        ]:
            value = TestAssetGovernanceDao._get(req_data, req_key, TestAssetGovernanceDao._camel_to_snake(req_key))
            if value not in (None, ''):
                query = query.filter(column == int(value))
        for req_key, column in [
            ('issueType', TestAssetIssue.issue_type),
            ('severity', TestAssetIssue.severity),
            ('actionStatus', TestAssetIssue.action_status),
        ]:
            value = TestAssetGovernanceDao._get(req_data, req_key, TestAssetGovernanceDao._camel_to_snake(req_key))
            if value not in (None, ''):
                query = query.filter(column == value)
        keyword = req_data.get('keyword')
        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(or_(TestAssetIssue.title.like(like_keyword), TestAssetIssue.description.like(like_keyword)))
        total = query.count()
        page, limit = TestAssetGovernanceDao._page(req_data)
        items = query.order_by(TestAssetIssue.severity.desc(), TestAssetIssue.id.asc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def get_issues(session, scan_id):
        return session.query(TestAssetIssue).filter(
            TestAssetIssue.scan_id == int(scan_id),
            TestAssetIssue.is_delete == 0
        ).order_by(TestAssetIssue.id.asc()).all()

    @staticmethod
    def get_actions_by_issue_ids(session, issue_ids):
        if not issue_ids:
            return []
        return session.query(TestAssetAction).filter(
            TestAssetAction.issue_id.in_([int(item) for item in issue_ids])
        ).order_by(TestAssetAction.created_time.desc(), TestAssetAction.id.desc()).all()

    @staticmethod
    def soft_delete_by_scan(session, scan_id):
        issue_ids = [
            item[0] for item in session.query(TestAssetIssue.id).filter(
                TestAssetIssue.scan_id == int(scan_id),
                TestAssetIssue.is_delete == 0
            ).all()
        ]
        if issue_ids:
            session.query(TestAssetAction).filter(TestAssetAction.issue_id.in_(issue_ids)).update(
                {'status': 'deleted'},
                synchronize_session=False
            )
        session.query(TestAssetIssue).filter(
            TestAssetIssue.scan_id == int(scan_id),
            TestAssetIssue.is_delete == 0
        ).update({'is_delete': 1}, synchronize_session=False)
        err = session.done(close=False)
        if err:
            return 0, f'清理旧问题失败：{err}'
        return int(scan_id), ''

    @staticmethod
    def _page(req_data):
        page = int(req_data.get('pageNo') or req_data.get('page') or 1)
        limit = int(req_data.get('pageSize') or req_data.get('limit') or req_data.get('size') or 20)
        return page, limit

    @staticmethod
    def _get(req_data, *keys):
        for key in keys:
            value = req_data.get(key)
            if value not in (None, ''):
                return value
        return None

    @staticmethod
    def _camel_to_snake(name):
        result = []
        for char in name:
            if char.isupper() and result:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
