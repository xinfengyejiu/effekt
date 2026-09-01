# encoding: UTF-8
from datetime import datetime

from ..model.userModel import User, UserRole
from logger import logger


class UserDao(object):
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
    def list_by_filters(session, model_cls, filter_list, page=1, limit=20, order_column=None):
        query = session.query(model_cls).filter(*filter_list)
        if hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        total = query.count()
        if order_column is not None:
            query = query.order_by(order_column.desc())
        rets = query.offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        return rets, total

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        return UserDao.update_by_id(session, model_cls, obj_id, {'is_delete': 1})

    @staticmethod
    def get_user_role_ids(session, user_id):
        items = session.query(UserRole).filter(UserRole.user_id == int(user_id), UserRole.is_delete == 0).all()
        return [item.role_id for item in items]

    @staticmethod
    def replace_user_roles(session, user_id, role_ids):
        user_id = int(user_id)
        role_ids = [int(role_id) for role_id in role_ids]
        # 同步 sys_user_role 序列：防止历史 SQL 直插导致序列滞后于 MAX(id)
        try:
            session.execute(
                "SELECT setval("
                "pg_get_serial_sequence('public.sys_user_role', 'id'), "
                "GREATEST(COALESCE((SELECT MAX(id) FROM public.sys_user_role), 0), 1), "
                "true)"
            )
        except Exception as _seq_err:
            logger.warning(f'同步 sys_user_role 序列失败：{_seq_err}')
        session.query(UserRole).filter(UserRole.user_id == user_id, UserRole.is_delete == 0).update({'is_delete': 1})
        existing_items = session.query(UserRole).filter(UserRole.user_id == user_id).all()
        existing_map = {item.role_id: item for item in existing_items}
        for role_id in role_ids:
            existing_item = existing_map.get(role_id)
            if existing_item:
                existing_item.is_delete = 0
            else:
                session.add(UserRole(user_id=user_id, role_id=role_id, is_delete=0))
        err = session.done(close=False)
        if err:
            return 0, f'分配角色失败！{err}'
        return user_id, ''

    @staticmethod
    def get_user_roles(session, user_ids):
        if not user_ids:
            return {}
        items = session.query(UserRole).filter(UserRole.user_id.in_(user_ids), UserRole.is_delete == 0).all()
        ret = {}
        for item in items:
            ret.setdefault(item.user_id, []).append(item.role_id)
        return ret

    @staticmethod
    def get_by_username(session, username):
        return session.query(User).filter(User.username == username, User.is_delete == 0).first()

    @staticmethod
    def update_last_login_time(session, user_id):
        session.query(User).filter(User.id == int(user_id), User.is_delete == 0).update({'last_login_time': datetime.now()})
        err = session.done(close=False)
        if err:
            return 0, f'更新登录时间失败！{err}'
        return int(user_id), ''

    @staticmethod
    def user_model():
        return User

    @staticmethod
    def get_user_info_map(session, user_ids):
        if not user_ids:
            return {}
        items = session.query(User).filter(User.id.in_(user_ids), User.is_delete == 0).all()
        return {item.id: {'username': item.username, 'real_name': item.real_name} for item in items}
