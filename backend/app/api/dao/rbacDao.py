# encoding: UTF-8
from ..model.rbacModel import Role, Permission, RolePermission, Menu, RoleMenu
from logger import logger


class RbacDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        # 同步表对应序列：防止历史直插/迁移导致序列滞后于 MAX(id) 引发主键冲突
        try:
            table_name = getattr(model_cls, '__tablename__', None)
            if table_name:
                session.execute(
                    "SELECT setval("
                    "pg_get_serial_sequence(:tbl_seq, 'id'), "
                    "GREATEST(COALESCE((SELECT MAX(id) FROM %s), 0), 1), "
                    "true)" % table_name,
                    {'tbl_seq': 'public.%s' % table_name}
                )
        except Exception as _seq_err:
            logger.warning(f'同步 {getattr(model_cls, "__tablename__", "?")} 序列失败：{_seq_err}')
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
        return RbacDao.update_by_id(session, model_cls, obj_id, {'is_delete': 1})

    @staticmethod
    def get_role_permission_ids(session, role_id):
        items = session.query(RolePermission).filter(RolePermission.role_id == int(role_id), RolePermission.is_delete == 0).all()
        return [item.permission_id for item in items]

    @staticmethod
    def replace_role_permissions(session, role_id, permission_ids):
        role_id = int(role_id)
        normalized_permission_ids = []
        for permission_id in permission_ids:
            permission_id = int(permission_id)
            if permission_id not in normalized_permission_ids:
                normalized_permission_ids.append(permission_id)
        session.query(RolePermission).filter(RolePermission.role_id == role_id, RolePermission.is_delete == 0).update({'is_delete': 1})
        session.flush()
        if normalized_permission_ids:
            existing_items = session.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(normalized_permission_ids)
            ).all()
            existing_map = {item.permission_id: item for item in existing_items}
            for permission_id in normalized_permission_ids:
                existing_item = existing_map.get(permission_id)
                if existing_item:
                    existing_item.is_delete = 0
                else:
                    session.add(RolePermission(role_id=role_id, permission_id=permission_id, is_delete=0))
        err = session.done(close=False)
        if err:
            return 0, f'分配权限失败！{err}'
        return role_id, ''

    @staticmethod
    def assign_permissions_to_roles(session, role_ids, permission_id):
        permission_id = int(permission_id)
        normalized_role_ids = []
        for role_id in role_ids:
            role_id = int(role_id)
            if role_id not in normalized_role_ids:
                normalized_role_ids.append(role_id)
        existing_items = session.query(RolePermission).filter(
            RolePermission.role_id.in_(normalized_role_ids),
            RolePermission.permission_id == permission_id
        ).all()
        existing_role_ids = {item.role_id for item in existing_items}
        for role_id in normalized_role_ids:
            if role_id not in existing_role_ids:
                session.add(RolePermission(role_id=role_id, permission_id=permission_id, is_delete=0))
            else:
                existing_item = next(item for item in existing_items if item.role_id == role_id)
                if existing_item.is_delete == 1:
                    existing_item.is_delete = 0
        err = session.done(close=False)
        if err:
            return 0, f'分配权限失败！{err}'
        return len(normalized_role_ids), ''

    @staticmethod
    def get_role_menu_ids(session, role_id):
        items = session.query(RoleMenu).filter(RoleMenu.role_id == int(role_id), RoleMenu.is_delete == 0).all()
        return [item.menu_id for item in items]

    @staticmethod
    def replace_role_menus(session, role_id, menu_ids):
        role_id = int(role_id)
        normalized_menu_ids = []
        for menu_id in menu_ids:
            menu_id = int(menu_id)
            if menu_id not in normalized_menu_ids:
                normalized_menu_ids.append(menu_id)
        session.query(RoleMenu).filter(RoleMenu.role_id == role_id, RoleMenu.is_delete == 0).update({'is_delete': 1})
        if normalized_menu_ids:
            existing_items = session.query(RoleMenu).filter(
                RoleMenu.role_id == role_id,
                RoleMenu.menu_id.in_(normalized_menu_ids)
            ).all()
            existing_map = {item.menu_id: item for item in existing_items}
            for menu_id in normalized_menu_ids:
                existing_item = existing_map.get(menu_id)
                if existing_item:
                    existing_item.is_delete = 0
                else:
                    session.add(RoleMenu(role_id=role_id, menu_id=menu_id, is_delete=0))
        err = session.done(close=False)
        if err:
            return 0, f'分配菜单失败！{err}'
        return role_id, ''

    @staticmethod
    def get_role_names_map(session, role_ids):
        if not role_ids:
            return {}
        items = session.query(Role).filter(Role.id.in_(role_ids), Role.is_delete == 0).all()
        return {item.id: item.name for item in items}

    @staticmethod
    def get_role_permission_codes(session, role_ids):
        if not role_ids:
            return []
        permission_items = session.query(Permission.code).join(
            RolePermission, RolePermission.permission_id == Permission.id
        ).filter(
            RolePermission.role_id.in_(role_ids), RolePermission.is_delete == 0,
            Permission.is_delete == 0, Permission.status == 1
        ).all()
        menu_items = session.query(Menu.permission_code).join(
            RoleMenu, RoleMenu.menu_id == Menu.id
        ).filter(
            RoleMenu.role_id.in_(role_ids), RoleMenu.is_delete == 0,
            Menu.is_delete == 0, Menu.status == 1
        ).all()
        return sorted(list({item[0] for item in permission_items if item[0]} | {item[0] for item in menu_items if item[0]}))

    @staticmethod
    def get_menu_tree_items(session, filter_list):
        return session.query(Menu).filter(*filter_list, Menu.is_delete == 0).order_by(Menu.sort.asc(), Menu.id.asc()).all()

    @staticmethod
    def role_model():
        return Role

    @staticmethod
    def permission_model():
        return Permission

    @staticmethod
    def menu_model():
        return Menu

    @staticmethod
    def get_role_name_map(session):
        items = session.query(Role).filter(Role.is_delete == 0, Role.status == 1).all()
        return {item.id: item.name for item in items}

    @staticmethod
    def get_menu_permission_codes(session, menu_ids):
        if not menu_ids:
            return []
        items = session.query(Menu.permission_code).filter(
            Menu.id.in_(menu_ids),
            Menu.is_delete == 0
        ).all()
        return [item[0] for item in items if item[0]]

    @staticmethod
    def get_permission_ids_by_codes(session, permission_codes):
        if not permission_codes:
            return []
        items = session.query(Permission.id).filter(
            Permission.code.in_(permission_codes),
            Permission.is_delete == 0
        ).all()
        return [item[0] for item in items]
