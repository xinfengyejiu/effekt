# encoding: UTF-8
from logger import logger


class PerformanceDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__}新增失败！{err}')
            return 0, f'新增失败！{err}'
        return obj.id, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
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
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def get_first(session, model_cls, filter_list, soft_delete=True):
        query = session.query(model_cls).filter(*filter_list)
        if soft_delete and hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        return query.first()

    @staticmethod
    def list_by_filters(session, model_cls, filter_list, page=1, limit=20, order_column=None, soft_delete=True):
        query = session.query(model_cls).filter(*filter_list)
        if soft_delete and hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        total = query.count()
        if order_column is not None:
            query = query.order_by(order_column.desc())
        rets = query.offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        return rets, total

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        if hasattr(model_cls, 'is_delete'):
            return PerformanceDao.update_by_id(session, model_cls, obj_id, {'is_delete': 1})
        return PerformanceDao.update_by_id(session, model_cls, obj_id, {'status': 0}, soft_delete=False)
