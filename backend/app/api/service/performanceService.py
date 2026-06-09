# encoding: UTF-8
from ..dao.performanceDao import PerformanceDao


class PerformanceService(object):
    @staticmethod
    def create(session, model_cls, add_info):
        return PerformanceDao.create(session, model_cls, add_info)

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        return PerformanceDao.update_by_id(session, model_cls, obj_id, update_info, soft_delete)

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        return PerformanceDao.get_by_id(session, model_cls, obj_id, soft_delete)

    @staticmethod
    def get_first(session, model_cls, filter_list, soft_delete=True):
        return PerformanceDao.get_first(session, model_cls, filter_list, soft_delete)

    @staticmethod
    def list_by_filters(session, model_cls, filter_list, page_num=1, page_size=20, order_column=None, soft_delete=True):
        return PerformanceDao.list_by_filters(session, model_cls, filter_list, int(page_num), int(page_size), order_column, soft_delete)

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        return PerformanceDao.delete_by_id(session, model_cls, obj_id)
