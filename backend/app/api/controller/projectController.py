# encoding: UTF-8
import random
import string

from .baseCrudController import BaseCrudController
from ..model.projectModel import Environment, Project, ProjectMember
from ..service.projectService import ProjectService
from ..service.userService import UserService
from ..dao.rbacDao import RbacDao


class ProjectController(BaseCrudController):
    """项目、项目成员、环境配置相关接口控制器。"""

    def project_list(self):
        """分页查询项目列表。"""
        page_num = self._get(self.req_data, 'pageNo', 'page', default=1)
        page_size = self._get(self.req_data, 'pageSize', 'size', default=20)
        keyword = self._get(self.req_data, 'keyword')
        status = self._get(self.req_data, 'status')
        product_id = self._get(self.req_data, 'productId', 'product_id')
        filter_list = []
        # 关键字先按项目名称模糊匹配。
        if keyword:
            filter_list.append(Project.name.like('%{}%'.format(keyword)))
        # 状态字段是枚举数字，查询时显式转 int。
        if status not in (None, ''):
            filter_list.append(Project.status == int(status))
        if product_id not in (None, ''):
            filter_list.append(Project.product_id == int(product_id))
        items, total = ProjectService.list_by_filters(self.session, Project, filter_list, page_num, page_size,
                                                      Project.created_time)
        product_ids = list({item.product_id for item in items if item.product_id})
        product_map = ProjectService.get_product_map(self.session, product_ids)
        result_list = self.serialize_list(items, ['is_delete'])
        for item in result_list:
            item['product_name'] = product_map.get(item.get('product_id'), '')
        return {'list': result_list, 'total': total}

    def project_detail(self):
        """查询项目详情。"""
        project_id = self._get(self.req_data, 'projectId', 'id')
        if not project_id:
            return {}, 'projectId 为必传参数'
        item = ProjectService.get_by_id(self.session, Project, project_id)
        if not item:
            return {}, '未查询到对应项目！'
        return self.serialize(item, ['is_delete']), ''

    def project_create(self):
        """创建项目。"""
        name = self._get(self.req_data, 'name')
        if not name:
            return 0, 'name 为必传参数'
        add_info = {
            'key': ''.join(random.choices(string.ascii_letters + string.digits, k=6)),
            'name': name,
            'product_id': self._get(self.req_data, 'productId', 'product_id'),
            'description': self._get(self.req_data, 'description'),
            'department': self._get(self.req_data, 'department'),
            # 默认状态为启用。
            'status': int(self._get(self.req_data, 'status', default=1)),
            'config': self._get(self.req_data, 'config', default={}),
            'created_by': self._get(self.req_data, 'createdBy'),
            'is_delete': 0
        }
        return ProjectService.create(self.session, Project, add_info)

    def project_update(self):
        """更新项目。"""
        project_id = self._get(self.req_data, 'projectId', 'id')
        if not project_id:
            return 0, 'projectId 为必传参数'
        update_info = {}
        # 仅更新前端实际传入的字段，避免把未传字段覆盖为空。
        for req_key, column_key in [('key', 'key'), ('name', 'name'), ('productId', 'product_id'),
                                    ('product_id', 'product_id'), ('description', 'description'),
                                    ('department', 'department'), ('status', 'status'), ('config', 'config')]:
            value = self._get(self.req_data, req_key)
            if value is not None:
                update_info[column_key] = value
        return ProjectService.update_by_id(self.session, Project, project_id, update_info)

    def project_delete(self):
        """软删除项目。"""
        project_id = self._get(self.req_data, 'projectId', 'id')
        if not project_id:
            return 0, 'projectId 为必传参数'
        return ProjectService.delete_by_id(self.session, Project, project_id)

    def environment_list(self):
        """按项目查询环境配置列表。"""
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        if not project_id:
            return {'list': [], 'total': 0}
        items, total = ProjectService.list_by_filters(self.session, Environment,
                                                      [Environment.project_id == int(project_id)],
                                                      self._get(self.req_data, 'pageNo', default=1),
                                                      self._get(self.req_data, 'pageSize', default=20),
                                                      Environment.created_time)
        return {'list': self.serialize_list(items, ['is_delete']), 'total': total}

    def environment_create(self):
        """新增环境配置。"""
        project_id = self._get(self.req_data, 'project_id')
        name = self._get(self.req_data, 'name')
        variables = self._get(self.req_data, 'variables')
        if not project_id or not name or variables is None:
            return 0, 'projectId、name、variables 为必传参数'
        return ProjectService.create(self.session, Environment, {
            'project_id': project_id,
            'name': name,
            'variables': variables,
            # 兼容是否加密开关。
            'is_encrypted': bool(self._get(self.req_data, 'isEncrypted', default=False)),
            'is_delete': 0
        })

    def environment_update(self):
        """更新环境配置。"""
        env_id = self._get(self.req_data, 'environmentId', 'id')
        if not env_id:
            return 0, 'environmentId 为必传参数'
        update_info = {}
        for req_key, column_key in [('name', 'name'), ('variables', 'variables'), ('isEncrypted', 'is_encrypted')]:
            value = self._get(self.req_data, req_key)
            if value is not None:
                update_info[column_key] = value
        return ProjectService.update_by_id(self.session, Environment, env_id, update_info)

    def environment_delete(self):
        """软删除环境配置。"""
        env_id = self._get(self.req_data, 'environmentId', 'id')
        if not env_id:
            return 0, 'environmentId 为必传参数'
        return ProjectService.delete_by_id(self.session, Environment, env_id)

    def member_list(self):
        """查询项目成员列表（带用户名、角色名称、项目名称）。"""
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        filters = [ProjectMember.project_id == int(project_id)] if project_id else []
        items, total = ProjectService.list_by_filters(self.session, ProjectMember, filters,
                                                      self._get(self.req_data, 'pageNo', default=1),
                                                      self._get(self.req_data, 'pageSize', default=20),
                                                      ProjectMember.joined_time)
        result_list = self.serialize_list(items)
        if not result_list:
            return {'list': result_list, 'total': total}
        user_ids = [item.get('user_id') for item in result_list]
        project_ids = [item.get('project_id') for item in result_list]
        user_map = UserService.get_user_info_map(self.session, user_ids)
        project_map = ProjectService.get_project_name_map(self.session, project_ids)
        user_role_map = UserService.get_user_roles_map(self.session, user_ids)
        
        for item in result_list:
            user_id = item.get('user_id')
            user_info = user_map.get(user_id, {})
            item['real_name'] = user_info.get('real_name', '')
            item['username'] = user_info.get('username', '')
            project_info = project_map.get(item.get('project_id'), {})
            item['project_name'] = project_info.get('name', '')
            
            role_info = user_role_map.get(user_id, {})
            role_names = role_info.get('role_names', [])
            item['role_names'] = role_names
            item['role_name'] = ','.join(role_names) if role_names else ''
        return {'list': result_list, 'total': total}

    def member_create(self):
        """批量新增项目成员（根据用户系统角色自动映射项目成员角色）。"""
        project_id = self._get(self.req_data, 'project_id')
        user_ids = self._get(self.req_data, 'user_ids')
        if not project_id or not user_ids:
            return 0, 'project_id、user_ids 为必传参数'
        if not isinstance(user_ids, list):
            return 0, 'user_ids 必须为数组'
        if not user_ids:
            return 0, 'user_ids 不能为空'
        normalized_user_ids = []
        seen_user_ids = set()
        for user_id in user_ids:
            if user_id in (None, ''):
                return 0, 'user_ids 不能为空'
            normalized_user_id = int(user_id)
            if normalized_user_id in seen_user_ids:
                return 0, f'用户 {normalized_user_id} 重复选择'
            seen_user_ids.add(normalized_user_id)
            normalized_user_ids.append(normalized_user_id)
        existing_members = self.session.query(ProjectMember.user_id).filter(
            ProjectMember.project_id == int(project_id),
            ProjectMember.user_id.in_(normalized_user_ids)
        ).all()
        existing_user_ids = [item[0] for item in existing_members]
        if existing_user_ids:
            existing_user_map = UserService.get_user_info_map(self.session, existing_user_ids)
            existing_user_names = [
                existing_user_map.get(user_id, {}).get('real_name') or
                existing_user_map.get(user_id, {}).get('username') or
                str(user_id)
                for user_id in existing_user_ids
            ]
            return 0, f'用户 {",".join(existing_user_names)} 已是项目成员'
        user_role_map = UserService.get_user_roles_map(self.session, normalized_user_ids)
        role_name_map = RbacDao.get_role_name_map(self.session)
        name_to_project_role = {name: role_id for role_id, name in role_name_map.items()}
        created_ids = []
        for user_id in normalized_user_ids:
            role_info = user_role_map.get(user_id, {})
            role_names = role_info.get('role_names', [])
            project_role = 0
            for role_name in role_names:
                if role_name in name_to_project_role:
                    project_role = name_to_project_role[role_name]
                    break
            if project_role == 0:
                return 0, f'用户 {user_id} 未分配有效角色，无法添加为项目成员'
            create_id, err_msg = ProjectService.create(self.session, ProjectMember, {
                'project_id': project_id,
                'user_id': user_id,
                'role': project_role
            })
            if err_msg:
                return 0, f'用户 {user_id} 添加失败：{err_msg}'
            created_ids.append(create_id)
        return created_ids[0] if len(created_ids) == 1 else created_ids, ''
