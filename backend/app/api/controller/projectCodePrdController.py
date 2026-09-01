# encoding: UTF-8
from .baseCrudController import BaseCrudController
from ..model.projectCodePrdModel import ProjectCodePrdConfig, ProjectCodePrdRecord
from ..service.projectCodePrdService import ProjectCodePrdService


class ProjectCodePrdController(BaseCrudController):
    def config_detail(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        if not project_id:
            return {}, 'projectId 为必传参数'
        item = ProjectCodePrdService.get_config_by_project(self.session, project_id)
        return self.serialize(item), ''

    def config_save(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        repo_url = self._get(self.req_data, 'repoUrl', 'repo_url')
        default_branch = self._get(self.req_data, 'defaultBranch', 'default_branch')
        model_config = self._get(self.req_data, 'modelConfig', 'model_config', default={})
        if not project_id:
            return 0, 'projectId 为必传参数'
        if not repo_url:
            return 0, 'repoUrl 为必传参数'
        existing = ProjectCodePrdService.get_config_by_project(self.session, project_id)
        save_info = {
            'project_id': int(project_id),
            'repo_url': repo_url,
            'default_branch': default_branch,
            'model_config': model_config or {},
            'is_delete': 0
        }
        if existing:
            return ProjectCodePrdService.update_by_id(self.session, ProjectCodePrdConfig, existing.id, save_info)
        return ProjectCodePrdService.create(self.session, ProjectCodePrdConfig, save_info)

    def branch_list(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        repo_url = self._get(self.req_data, 'repoUrl', 'repo_url')
        if not repo_url and project_id:
            config = ProjectCodePrdService.get_config_by_project(self.session, project_id)
            repo_url = config.repo_url if config else ''
        if not repo_url:
            return [], 'repoUrl 为必传参数'
        return ProjectCodePrdService.list_remote_branches(repo_url)

    def record_list(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        if not project_id:
            return {'list': [], 'total': 0}, 'projectId 为必传参数'
        items, total = ProjectCodePrdService.list_records(
            self.session,
            project_id,
            self._get(self.req_data, 'pageNo', 'page', default=1),
            self._get(self.req_data, 'pageSize', 'size', default=10)
        )
        return {'list': self.serialize_list(items), 'total': total}, ''

    def record_detail(self):
        record_id = self._get(self.req_data, 'recordId', 'id')
        if not record_id:
            return {}, 'recordId 为必传参数'
        item = ProjectCodePrdService.get_by_id(self.session, ProjectCodePrdRecord, record_id)
        if not item:
            return {}, '未查询到对应PRD记录'
        return self.serialize(item), ''

    def generate(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        branch = self._get(self.req_data, 'branch')
        repo_url = self._get(self.req_data, 'repoUrl', 'repo_url')
        prompt_append = self._get(self.req_data, 'promptAppend', 'prompt_append', default='')
        created_by = self._get(self.req_data, 'createdBy', 'created_by')
        if not project_id:
            return 0, 'projectId 为必传参数'
        config = ProjectCodePrdService.get_config_by_project(self.session, project_id)
        if not repo_url:
            repo_url = config.repo_url if config else ''
        if not branch:
            branch = config.default_branch if config else ''
        if not repo_url:
            return 0, '请先配置Git仓库地址'
        if not branch:
            return 0, '请选择Git分支'
        record_id, err_msg = ProjectCodePrdService.create(self.session, ProjectCodePrdRecord, {
            'project_id': int(project_id),
            'config_id': config.id if config else None,
            'repo_url': repo_url,
            'branch': branch,
            'title': f'代码转PRD-{branch}',
            'status': 0,
            'created_by': int(created_by) if created_by not in (None, '') else None,
            'is_delete': 0
        })
        if err_msg:
            return 0, err_msg
        ProjectCodePrdService.start_generate_prd(record_id, prompt_append)
        return record_id, ''

    def export_docx(self):
        record_id = self._get(self.req_data, 'recordId', 'id')
        if not record_id:
            return None, '', 'recordId 为必传参数'
        item = ProjectCodePrdService.get_by_id(self.session, ProjectCodePrdRecord, record_id)
        if not item:
            return None, '', '未查询到对应PRD记录'
        if not item.prd_markdown:
            return None, '', '该记录暂无PRD内容'
        file_obj, err_msg = ProjectCodePrdService.build_docx(item.prd_markdown)
        if err_msg:
            return None, '', err_msg
        filename = f'code-prd-{item.id}.docx'
        return file_obj, filename, ''
