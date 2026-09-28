# encoding: UTF-8
from logger import logger
from ..model.weakNetworkModel import WeakNetworkProfile, WeakNetworkSession


class WeakNetworkDao(object):

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
    def list_profiles(session, req_data):
        query = session.query(WeakNetworkProfile).filter(WeakNetworkProfile.is_delete == 0)
        product_id = WeakNetworkDao._get(req_data, 'productId', 'product_id')
        project_id = WeakNetworkDao._get(req_data, 'projectId', 'project_id')
        enabled = WeakNetworkDao._get(req_data, 'enabled')
        keyword = WeakNetworkDao._get(req_data, 'keyword')
        # System presets (null scope) + scoped profiles
        if product_id not in (None, '') or project_id not in (None, ''):
            from sqlalchemy import or_
            clauses = [WeakNetworkProfile.is_system == 1]
            if product_id not in (None, '') and project_id not in (None, ''):
                clauses.append(
                    (WeakNetworkProfile.product_id == int(product_id)) &
                    (WeakNetworkProfile.project_id == int(project_id))
                )
            elif product_id not in (None, ''):
                clauses.append(WeakNetworkProfile.product_id == int(product_id))
            elif project_id not in (None, ''):
                clauses.append(WeakNetworkProfile.project_id == int(project_id))
            query = query.filter(or_(*clauses))
        if enabled not in (None, ''):
            query = query.filter(WeakNetworkProfile.enabled == int(enabled))
        if keyword:
            like = '%{}%'.format(keyword)
            query = query.filter(
                (WeakNetworkProfile.name.like(like)) | (WeakNetworkProfile.preset_code.like(like))
            )
        total = query.count()
        page, limit = WeakNetworkDao._page(req_data)
        items = query.order_by(
            WeakNetworkProfile.is_system.desc(),
            WeakNetworkProfile.id.asc(),
        ).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_sessions(session, req_data):
        query = session.query(WeakNetworkSession).filter(WeakNetworkSession.is_delete == 0)
        profile_id = WeakNetworkDao._get(req_data, 'profileId', 'profile_id')
        project_id = WeakNetworkDao._get(req_data, 'projectId', 'project_id')
        if profile_id not in (None, ''):
            query = query.filter(WeakNetworkSession.profile_id == int(profile_id))
        if project_id not in (None, ''):
            query = query.filter(WeakNetworkSession.project_id == int(project_id))
        total = query.count()
        page, limit = WeakNetworkDao._page(req_data)
        items = query.order_by(WeakNetworkSession.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def _page(req_data):
        try:
            page = int(WeakNetworkDao._get(req_data, 'pageNo', 'page') or 1)
        except Exception:
            page = 1
        try:
            limit = int(WeakNetworkDao._get(req_data, 'pageSize', 'limit') or 20)
        except Exception:
            limit = 20
        page = max(page, 1)
        limit = min(max(limit, 1), 200)
        return page, limit

    @staticmethod
    def _get(data, *keys):
        if not data:
            return None
        for k in keys:
            if k in data and data.get(k) is not None:
                return data.get(k)
        return None
