# encoding: UTF-8
from sqlalchemy import or_

from logger import logger


class AiBaseDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__}新增失败！{err}')
            return None, f'新增失败！{err}'
        return obj, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info):
        filters = [model_cls.id == int(obj_id)]
        if hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        update_res = session.query(model_cls).filter(*filters).update(update_info)
        err = session.done(close=False)
        if err:
            logger.error(f'{model_cls.__name__}更新失败！id: {obj_id}, err: {err}')
            return 0, f'更新失败！{err}'
        if not update_res:
            return 0, '未查询到对应记录！'
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id):
        filters = [model_cls.id == int(obj_id)]
        if hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def get_by_code(session, model_cls, code_field, code):
        filters = [getattr(model_cls, code_field) == code]
        if hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def soft_delete(session, model_cls, obj_id):
        if not hasattr(model_cls, 'is_delete'):
            return AiBaseDao.update_by_id(session, model_cls, obj_id, {})
        return AiBaseDao.update_by_id(session, model_cls, obj_id, {'is_delete': 1})

    @staticmethod
    def list_by_filters(session, model_cls, filters, page=1, limit=20, keyword=None, keyword_fields=None):
        query = session.query(model_cls).filter(*filters)
        if hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        if keyword and keyword_fields:
            like_keyword = f'%{keyword}%'
            query = query.filter(or_(*[getattr(model_cls, field).like(like_keyword) for field in keyword_fields]))
        total = query.count()
        order_field = getattr(model_cls, 'created_time', model_cls.id)
        items = query.order_by(order_field.desc()).offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        return items, total
