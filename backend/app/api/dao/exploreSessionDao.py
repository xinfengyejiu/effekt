# encoding: UTF-8
from logger import logger
from ..model.exploreSessionModel import ExploreSession, ExploreSessionEntry


class ExploreSessionDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning('%s create failed: %s', model_cls.__name__, err)
            return None, '新增失败：{}'.format(err)
        return obj, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        update_res = session.query(model_cls).filter(*filters).update(update_info, synchronize_session=False)
        err = session.done(close=False)
        if err:
            logger.warning('%s update failed: %s', model_cls.__name__, err)
            return 0, '更新失败：{}'.format(err)
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
    def list_sessions(session, req_data):
        query = session.query(ExploreSession).filter(ExploreSession.is_delete == 0)
        product_id = ExploreSessionDao._get(req_data, 'productId', 'product_id')
        project_id = ExploreSessionDao._get(req_data, 'projectId', 'project_id')
        status = ExploreSessionDao._get(req_data, 'status')
        keyword = ExploreSessionDao._get(req_data, 'keyword')
        if product_id not in (None, ''):
            query = query.filter(ExploreSession.product_id == int(product_id))
        if project_id not in (None, ''):
            query = query.filter(ExploreSession.project_id == int(project_id))
        if status not in (None, ''):
            query = query.filter(ExploreSession.status == status)
        else:
            query = query.filter(ExploreSession.status != 'archived')
        if keyword:
            like = '%{}%'.format(keyword)
            query = query.filter(
                (ExploreSession.title.like(like)) | (ExploreSession.session_no.like(like))
            )
        total = query.count()
        page, limit = ExploreSessionDao._page(req_data)
        items = query.order_by(ExploreSession.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_entries(session, session_id):
        return session.query(ExploreSessionEntry).filter(
            ExploreSessionEntry.session_id == int(session_id),
            ExploreSessionEntry.is_delete == 0,
        ).order_by(ExploreSessionEntry.sort_no.asc(), ExploreSessionEntry.id.asc()).all()

    @staticmethod
    def next_sort_no(session, session_id):
        row = session.query(ExploreSessionEntry).filter(
            ExploreSessionEntry.session_id == int(session_id),
            ExploreSessionEntry.is_delete == 0,
        ).order_by(ExploreSessionEntry.sort_no.desc()).first()
        if not row:
            return 1
        return int(row.sort_no or 0) + 1

    @staticmethod
    def get_entries_by_ids(session, session_id, entry_ids):
        if not entry_ids:
            return []
        ids = [int(x) for x in entry_ids]
        return session.query(ExploreSessionEntry).filter(
            ExploreSessionEntry.session_id == int(session_id),
            ExploreSessionEntry.id.in_(ids),
            ExploreSessionEntry.is_delete == 0,
        ).order_by(ExploreSessionEntry.sort_no.asc(), ExploreSessionEntry.id.asc()).all()

    @staticmethod
    def link_entries(session, entry_ids, bug_id=None, case_id=None):
        if not entry_ids:
            return '', ''
        update_info = {}
        if bug_id is not None:
            update_info['linked_bug_id'] = int(bug_id)
        if case_id is not None:
            update_info['linked_case_id'] = int(case_id)
        if not update_info:
            return '', ''
        session.query(ExploreSessionEntry).filter(
            ExploreSessionEntry.id.in_([int(x) for x in entry_ids]),
            ExploreSessionEntry.is_delete == 0,
        ).update(update_info, synchronize_session=False)
        err = session.done(close=False)
        if err:
            return '', '回写关联失败：{}'.format(err)
        return '', ''

    @staticmethod
    def _page(req_data):
        try:
            page = int(req_data.get('pageNo') or req_data.get('page') or 1)
        except Exception:
            page = 1
        try:
            limit = int(req_data.get('pageSize') or req_data.get('limit') or 20)
        except Exception:
            limit = 20
        page = max(page, 1)
        limit = min(max(limit, 1), 200)
        return page, limit

    @staticmethod
    def _get(req_data, *keys):
        for key in keys:
            if key in req_data and req_data.get(key) not in (None,):
                return req_data.get(key)
        return None
