# encoding: UTF-8
from .baseCrudController import BaseCrudController
from ..model.userModel import User
from ..service.userService import UserService
from ..utils.authMiddleware import TOKEN_REFRESH_THRESHOLD_SECONDS, create_token, create_refresh_token


class UserController(BaseCrudController):
    def user_list(self):
        filters = []
        keyword = self._get(self.req_data, 'keyword')
        status = self._get(self.req_data, 'status')
        if keyword:
            filters.append(User.username.like('%{}%'.format(keyword)))
        if status not in (None, ''):
            filters.append(User.status == int(status))
        items, total = UserService.list_by_filters(self.session, User, filters,
                                                   self._get(self.req_data, 'pageNo', 'page', default=1),
                                                   self._get(self.req_data, 'pageSize', 'size', default=20),
                                                   User.created_time)
        result_list = self.serialize_list(items, ['is_delete', 'password_hash'])
        role_map = UserService.get_user_roles_map(self.session, [item.id for item in items])
        for item in result_list:
            role_info = role_map.get(item.get('id'), {'role_ids': [], 'role_names': []})
            item['role_ids'] = role_info['role_ids']
            item['role_names'] = role_info['role_names']
        return {'list': result_list, 'total': total}

    def user_detail(self):
        user_id = self._get(self.req_data, 'userId', 'id')
        if not user_id:
            return {}, 'userId 为必传参数'
        item = UserService.get_by_id(self.session, User, user_id)
        if not item:
            return {}, '未查询到对应用户！'
        ret = self.serialize(item, ['is_delete', 'password_hash'])
        ret['role_ids'] = UserService.get_user_role_ids(self.session, user_id)
        return ret, ''

    def user_create(self):
        username = self._get(self.req_data, 'username')
        password = self._get(self.req_data, 'password')
        if not username or not password:
            return 0, 'username、password 为必传参数'
        exist_user = UserService.get_by_username(self.session, username)
        if exist_user:
            return 0, '用户名已存在！'
        return UserService.create(self.session, User, {
            'username': username,
            'real_name': self._get(self.req_data, 'realName', 'real_name'),
            'password_hash': password,
            'mobile': self._get(self.req_data, 'mobile'),
            'email': self._get(self.req_data, 'email'),
            'avatar': self._get(self.req_data, 'avatar'),
            'status': int(self._get(self.req_data, 'status', default=1)),
            'created_by': self._get(self.req_data, 'createdBy'),
            'is_delete': 0
        })

    def user_update(self):
        user_id = self._get(self.req_data, 'userId', 'id')
        if not user_id:
            return 0, 'userId 为必传参数'
        update_info = {}
        for req_key, column_key in [('username', 'username'), ('realName', 'real_name'), ('real_name', 'real_name'),
                                    ('password', 'password_hash'), ('mobile', 'mobile'), ('email', 'email'),
                                    ('avatar', 'avatar'), ('status', 'status')]:
            value = self._get(self.req_data, req_key)
            if value is not None:
                update_info[column_key] = value
        return UserService.update_by_id(self.session, User, user_id, update_info)

    def user_delete(self):
        user_id = self._get(self.req_data, 'userId', 'id')
        if not user_id:
            return 0, 'userId 为必传参数'
        return UserService.delete_by_id(self.session, User, user_id)

    def user_role_list(self):
        user_id = self._get(self.req_data, 'userId')
        if not user_id:
            return {'roleIds': []}
        return {'roleIds': UserService.get_user_role_ids(self.session, user_id)}

    def user_role_assign(self):
        user_id = self._get(self.req_data, 'userId')
        role_ids = self._get(self.req_data, 'roleIds', default=[])
        if not user_id:
            return 0, 'userId 为必传参数'
        return UserService.assign_roles(self.session, user_id, role_ids)

    def register(self):
        username = self._get(self.req_data, 'username')
        password = self._get(self.req_data, 'password')
        if not username or not password:
            return 0, 'username、password 为必传参数'
        exist_user = UserService.get_by_username(self.session, username)
        if exist_user:
            return 0, '用户名已存在！'
        return UserService.create(self.session, User, {
            'username': username,
            'real_name': self._get(self.req_data, 'realName', 'real_name'),
            'password_hash': password,
            'mobile': self._get(self.req_data, 'mobile'),
            'email': self._get(self.req_data, 'email'),
            'avatar': self._get(self.req_data, 'avatar'),
            'status': 1,
            'created_by': self._get(self.req_data, 'createdBy'),
            'is_delete': 0
        })

    def login(self):
        username = self._get(self.req_data, 'username')
        password = self._get(self.req_data, 'password')
        if not username or not password:
            return {}, 'username、password 为必传参数'
        user = UserService.get_by_username(self.session, username)
        if not user or user.password_hash != password:
            return {}, '用户名或密码错误！'
        if int(user.status) != 1:
            return {}, '用户已禁用！'
        UserService.update_last_login_time(self.session, user.id)
        token, expire_seconds = create_token(user.id)
        refresh_token, refresh_expire_seconds = create_refresh_token(user.id)
        ret = self.serialize(user, ['is_delete', 'password_hash'])
        ret['role_ids'] = UserService.get_user_role_ids(self.session, user.id)
        ret['token'] = token
        ret['token_type'] = 'Bearer'
        ret['expires_in'] = expire_seconds
        ret['refresh_token'] = refresh_token
        ret['refresh_expires_in'] = refresh_expire_seconds
        ret['refresh_threshold_seconds'] = TOKEN_REFRESH_THRESHOLD_SECONDS
        ret['refresh_mechanism'] = '请求任意已登录接口时，若token剩余有效期小于阈值则自动续期到完整有效期'
        return ret, ''
