# encoding: UTF-8
from sqlalchemy import or_

from logger import logger
from ..model.aiReviewModel import AiTestReviewCaseSuggestion, AiTestReviewFinding


class AiReviewDao(object):
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
    def list_reviews(session, model_cls, req_data):
        filters = []
        for req_key, column in [
            ('productId', model_cls.product_id),
            ('projectId', model_cls.project_id),
        ]:
            value = req_data.get(req_key) or req_data.get(req_key[0].lower() + req_key[1:])
            if value not in (None, ''):
                filters.append(column == int(value))
        for req_key, column in [
            ('reviewType', model_cls.review_type),
            ('sourceType', model_cls.source_type),
            ('status', model_cls.status),
            ('riskLevel', model_cls.risk_level),
        ]:
            value = req_data.get(req_key) or req_data.get(AiReviewDao._camel_to_snake(req_key))
            if value not in (None, ''):
                filters.append(column == value)
        query = session.query(model_cls).filter(*filters)
        if hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        keyword = req_data.get('keyword')
        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(or_(model_cls.review_no.like(like_keyword), model_cls.title.like(like_keyword)))
        total = query.count()
        page = int(req_data.get('pageNo') or req_data.get('page') or 1)
        limit = int(req_data.get('pageSize') or req_data.get('limit') or req_data.get('size') or 20)
        items = query.order_by(model_cls.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def get_findings(session, review_id):
        return session.query(AiTestReviewFinding).filter(
            AiTestReviewFinding.review_id == int(review_id),
            AiTestReviewFinding.is_delete == 0
        ).order_by(AiTestReviewFinding.id.asc()).all()

    @staticmethod
    def get_case_suggestions(session, review_id):
        return session.query(AiTestReviewCaseSuggestion).filter(
            AiTestReviewCaseSuggestion.review_id == int(review_id),
            AiTestReviewCaseSuggestion.is_delete == 0
        ).order_by(AiTestReviewCaseSuggestion.id.asc()).all()

    @staticmethod
    def soft_delete_by_review(session, model_cls, review_id):
        session.query(model_cls).filter(
            model_cls.review_id == int(review_id),
            model_cls.is_delete == 0
        ).update({'is_delete': 1})
        err = session.done(close=False)
        if err:
            return 0, f'删除失败：{err}'
        return int(review_id), ''

    @staticmethod
    def _camel_to_snake(name):
        result = []
        for char in name:
            if char.isupper() and result:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
