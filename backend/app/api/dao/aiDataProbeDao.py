# encoding: UTF-8
from logger import logger
from ..model.aiDataProbeModel import (
    AiDataProbeAudit,
    AiDataProbeConnection,
    AiDataProbeMessage,
    AiDataProbeSession,
)


class AiDataProbeDao(object):

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
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def list_connections(session, req_data):
        query = session.query(AiDataProbeConnection).filter(AiDataProbeConnection.is_delete == 0)
        product_id = AiDataProbeDao._get(req_data, 'productId', 'product_id')
        project_id = AiDataProbeDao._get(req_data, 'projectId', 'project_id')
        enabled = AiDataProbeDao._get(req_data, 'enabled')
        keyword = AiDataProbeDao._get(req_data, 'keyword')
        if product_id not in (None, ''):
            query = query.filter(AiDataProbeConnection.product_id == int(product_id))
        if project_id not in (None, ''):
            query = query.filter(AiDataProbeConnection.project_id == int(project_id))
        if enabled not in (None, ''):
            query = query.filter(AiDataProbeConnection.enabled == int(enabled))
        if keyword:
            like = '%{}%'.format(keyword)
            query = query.filter(
                (AiDataProbeConnection.name.like(like))
                | (AiDataProbeConnection.host.like(like))
                | (AiDataProbeConnection.database_name.like(like))
            )
        total = query.count()
        page, limit = AiDataProbeDao._page(req_data)
        items = query.order_by(AiDataProbeConnection.updated_time.desc(), AiDataProbeConnection.id.desc())\
            .offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_sessions(session, req_data):
        query = session.query(AiDataProbeSession).filter(AiDataProbeSession.is_delete == 0)
        connection_id = AiDataProbeDao._get(req_data, 'connectionId', 'connection_id')
        project_id = AiDataProbeDao._get(req_data, 'projectId', 'project_id')
        if connection_id not in (None, ''):
            query = query.filter(AiDataProbeSession.connection_id == int(connection_id))
        if project_id not in (None, ''):
            query = query.filter(AiDataProbeSession.project_id == int(project_id))
        total = query.count()
        page, limit = AiDataProbeDao._page(req_data)
        items = query.order_by(AiDataProbeSession.updated_time.desc(), AiDataProbeSession.id.desc())\
            .offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_messages(session, session_id, limit=200):
        return session.query(AiDataProbeMessage).filter(
            AiDataProbeMessage.session_id == int(session_id),
            AiDataProbeMessage.is_delete == 0,
        ).order_by(AiDataProbeMessage.id.asc()).limit(int(limit)).all()

    @staticmethod
    def add_audit(session, values):
        return AiDataProbeDao.create(session, AiDataProbeAudit, values)

    @staticmethod
    def _get(data, *keys):
        if not isinstance(data, dict):
            return None
        for key in keys:
            if key in data and data.get(key) not in (None, ''):
                return data.get(key)
        return None

    @staticmethod
    def _page(req_data):
        try:
            page = int(AiDataProbeDao._get(req_data, 'pageNo', 'page_no') or 1)
        except (TypeError, ValueError):
            page = 1
        try:
            limit = int(AiDataProbeDao._get(req_data, 'pageSize', 'page_size') or 20)
        except (TypeError, ValueError):
            limit = 20
        page = max(page, 1)
        limit = min(max(limit, 1), 100)
        return page, limit
