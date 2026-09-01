# encoding: UTF-8
from sqlalchemy import or_

from logger import logger
from ..model.aiWorkloadEstimateModel import (
    AiWorkloadEstimate,
    AiWorkloadEstimateFunction,
    AiWorkloadEstimateModule,
)


class AiWorkloadEstimateDao(object):
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
    def get_by_id(session, obj_id):
        return session.query(AiWorkloadEstimate).filter(
            AiWorkloadEstimate.id == int(obj_id),
            AiWorkloadEstimate.is_delete == 0
        ).first()

    @staticmethod
    def get_by_no(session, estimate_no):
        return session.query(AiWorkloadEstimate).filter(
            AiWorkloadEstimate.estimate_no == estimate_no,
            AiWorkloadEstimate.is_delete == 0
        ).first()

    @staticmethod
    def list_estimates(session, req_data):
        query = session.query(AiWorkloadEstimate).filter(AiWorkloadEstimate.is_delete == 0)
        for req_key, column in [
            ('productId', AiWorkloadEstimate.product_id),
            ('projectId', AiWorkloadEstimate.project_id),
            ('ownerId', AiWorkloadEstimate.owner_id),
        ]:
            value = AiWorkloadEstimateDao._get(req_data, req_key, AiWorkloadEstimateDao._camel_to_snake(req_key))
            if value not in (None, ''):
                query = query.filter(column == int(value))
        for req_key, column in [
            ('status', AiWorkloadEstimate.status),
            ('complexityLevel', AiWorkloadEstimate.complexity_level),
            ('confidence', AiWorkloadEstimate.confidence),
        ]:
            value = AiWorkloadEstimateDao._get(req_data, req_key, AiWorkloadEstimateDao._camel_to_snake(req_key))
            if value not in (None, ''):
                query = query.filter(column == value)
        product_name = AiWorkloadEstimateDao._get(req_data, 'productName', 'product_name')
        if product_name:
            query = query.filter(AiWorkloadEstimate.product_name.like(f'%{product_name}%'))
        project_name = AiWorkloadEstimateDao._get(req_data, 'projectName', 'project_name')
        if project_name:
            query = query.filter(AiWorkloadEstimate.project_name.like(f'%{project_name}%'))
        owner_name = AiWorkloadEstimateDao._get(req_data, 'ownerName', 'owner_name')
        if owner_name:
            query = query.filter(AiWorkloadEstimate.owner_name.like(f'%{owner_name}%'))
        keyword = AiWorkloadEstimateDao._get(req_data, 'keyword')
        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(or_(
                AiWorkloadEstimate.estimate_no.like(like_keyword),
                AiWorkloadEstimate.title.like(like_keyword),
                AiWorkloadEstimate.owner_name.like(like_keyword)
            ))
        start_time = AiWorkloadEstimateDao._get(req_data, 'startTime', 'start_time')
        if start_time:
            query = query.filter(AiWorkloadEstimate.created_time >= start_time)
        end_time = AiWorkloadEstimateDao._get(req_data, 'endTime', 'end_time')
        if end_time:
            query = query.filter(AiWorkloadEstimate.created_time <= end_time)
        total = query.count()
        page, limit = AiWorkloadEstimateDao._page(req_data)
        items = query.order_by(AiWorkloadEstimate.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def get_modules(session, estimate_id):
        return session.query(AiWorkloadEstimateModule).filter(
            AiWorkloadEstimateModule.estimate_id == int(estimate_id)
        ).order_by(AiWorkloadEstimateModule.sort_order.asc(), AiWorkloadEstimateModule.id.asc()).all()

    @staticmethod
    def get_functions(session, estimate_id):
        return session.query(AiWorkloadEstimateFunction).filter(
            AiWorkloadEstimateFunction.estimate_id == int(estimate_id)
        ).order_by(AiWorkloadEstimateFunction.sort_order.asc(), AiWorkloadEstimateFunction.id.asc()).all()

    @staticmethod
    def get_detail(session, estimate_id):
        estimate = AiWorkloadEstimateDao.get_by_id(session, estimate_id)
        if not estimate:
            return None
        return {
            'estimate': estimate,
            'modules': AiWorkloadEstimateDao.get_modules(session, estimate_id),
            'functions': AiWorkloadEstimateDao.get_functions(session, estimate_id)
        }

    @staticmethod
    def replace_details(session, estimate_id, module_rows, function_rows):
        session.query(AiWorkloadEstimateFunction).filter(
            AiWorkloadEstimateFunction.estimate_id == int(estimate_id)
        ).delete(synchronize_session=False)
        session.query(AiWorkloadEstimateModule).filter(
            AiWorkloadEstimateModule.estimate_id == int(estimate_id)
        ).delete(synchronize_session=False)
        module_objs = [AiWorkloadEstimateModule(**row) for row in module_rows]
        function_objs = [AiWorkloadEstimateFunction(**row) for row in function_rows]
        if module_objs:
            session.add_all(module_objs)
            session.flush()
        module_id_by_name = {item.module_name: item.id for item in module_objs}
        for function_obj in function_objs:
            if not function_obj.module_id and function_obj.module_name in module_id_by_name:
                function_obj.module_id = module_id_by_name[function_obj.module_name]
        if function_objs:
            session.add_all(function_objs)
        err = session.done(close=False)
        if err:
            logger.warning(f'AiWorkloadEstimate detail replace failed: {err}')
            return [], [], f'保存预估明细失败：{err}'
        return module_objs, function_objs, ''

    @staticmethod
    def assign_owner(session, estimate_id, owner_id, owner_name, assigned_by, assigned_time):
        return AiWorkloadEstimateDao.update_by_id(session, AiWorkloadEstimate, estimate_id, {
            'owner_id': owner_id,
            'owner_name': owner_name,
            'assigned_by': assigned_by,
            'assigned_time': assigned_time
        })

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
