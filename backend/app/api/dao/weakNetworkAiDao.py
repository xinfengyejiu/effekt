# encoding: UTF-8
from logger import logger
from ..model.weakNetworkAiModel import (
    WeakNetworkAiCheckpoint,
    WeakNetworkAiEvidence,
    WeakNetworkAiFinding,
    WeakNetworkAiTask,
)


class WeakNetworkAiDao(object):

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
            return 0, '更新失败：{}'.format(err)
        if not update_res:
            return 0, '未查询到对应记录'
        try:
            inner = getattr(session, 'session', None) or getattr(session, '_session', None)
            if inner is not None:
                inner.expire_all()
        except Exception:
            pass
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def list_tasks(session, req_data):
        query = session.query(WeakNetworkAiTask).filter(WeakNetworkAiTask.is_delete == 0)
        product_id = WeakNetworkAiDao._get(req_data, 'productId', 'product_id')
        project_id = WeakNetworkAiDao._get(req_data, 'projectId', 'project_id')
        status = WeakNetworkAiDao._get(req_data, 'status')
        keyword = WeakNetworkAiDao._get(req_data, 'keyword')
        if product_id not in (None, ''):
            query = query.filter(WeakNetworkAiTask.product_id == int(product_id))
        if project_id not in (None, ''):
            query = query.filter(WeakNetworkAiTask.project_id == int(project_id))
        if status not in (None, ''):
            query = query.filter(WeakNetworkAiTask.status == status)
        if keyword:
            like = '%{}%'.format(keyword)
            query = query.filter(
                (WeakNetworkAiTask.title.like(like)) | (WeakNetworkAiTask.task_no.like(like))
            )
        total = query.count()
        page, limit = WeakNetworkAiDao._page(req_data)
        items = query.order_by(WeakNetworkAiTask.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_checkpoints(session, task_id):
        return session.query(WeakNetworkAiCheckpoint).filter(
            WeakNetworkAiCheckpoint.task_id == int(task_id),
            WeakNetworkAiCheckpoint.is_delete == 0,
        ).order_by(WeakNetworkAiCheckpoint.sort_no.asc(), WeakNetworkAiCheckpoint.id.asc()).all()

    @staticmethod
    def list_evidence(session, task_id):
        return session.query(WeakNetworkAiEvidence).filter(
            WeakNetworkAiEvidence.task_id == int(task_id),
            WeakNetworkAiEvidence.is_delete == 0,
        ).order_by(WeakNetworkAiEvidence.id.asc()).all()

    @staticmethod
    def list_findings(session, task_id, status=None):
        query = session.query(WeakNetworkAiFinding).filter(
            WeakNetworkAiFinding.task_id == int(task_id),
            WeakNetworkAiFinding.is_delete == 0,
        )
        if status:
            query = query.filter(WeakNetworkAiFinding.status == status)
        return query.order_by(WeakNetworkAiFinding.id.asc()).all()

    @staticmethod
    def soft_delete_checkpoints(session, task_id):
        session.query(WeakNetworkAiCheckpoint).filter(
            WeakNetworkAiCheckpoint.task_id == int(task_id),
            WeakNetworkAiCheckpoint.is_delete == 0,
        ).update({'is_delete': 1}, synchronize_session=False)
        return session.done(close=False)

    @staticmethod
    def _page(req_data):
        try:
            page = int(WeakNetworkAiDao._get(req_data, 'pageNo', 'page') or 1)
        except Exception:
            page = 1
        try:
            limit = int(WeakNetworkAiDao._get(req_data, 'pageSize', 'limit') or 20)
        except Exception:
            limit = 20
        return max(page, 1), min(max(limit, 1), 200)

    @staticmethod
    def _get(data, *keys):
        if not data:
            return None
        for k in keys:
            if k in data and data.get(k) is not None:
                return data.get(k)
        return None
