# encoding: UTF-8
from .baseCrudController import BaseCrudController
from ..model.dataBuilderModel import DataBuilder, DataTask
from ..service.dataBuilderService import DataBuilderService


class DataBuilderController(BaseCrudController):
    """造数器与造数任务相关接口控制器。"""

    def builder_list(self):
        """分页查询造数器列表，可按项目过滤。"""
        filters = []
        project_id = self._get(self.req_data, 'projectId')
        if project_id:
            filters.append(DataBuilder.project_id == int(project_id))
        tag = self._get(self.req_data, 'tag')
        source = self._get(self.req_data, 'source')
        if source:
            filters.append(DataBuilder.source == source)
        items, total = DataBuilderService.list_by_filters(
            self.session, DataBuilder, filters,
            self._get(self.req_data, 'pageNo', default=1),
            self._get(self.req_data, 'pageSize', default=20),
            DataBuilder.created_time,
        )
        rows = self.serialize_list(items, ['is_delete'])
        if tag:
            tag_text = str(tag).strip()
            rows = [row for row in rows if tag_text in (row.get('tags') or [])]
            total = len(rows)
        return {'list': rows, 'total': total}

    def builder_detail(self):
        """查询造数器详情。"""
        builder_id = self._get(self.req_data, 'builderId', 'id')
        if not builder_id:
            return {}, 'builderId 为必传参数'
        item = DataBuilderService.get_by_id(self.session, DataBuilder, builder_id)
        if not item:
            return {}, '未查询到对应造数器！'
        return self.serialize(item, ['is_delete']), ''

    def builder_create(self):
        """创建造数器，definition 保存流程编排或模板定义。"""
        project_id = self._get(self.req_data, 'projectId')
        name = self._get(self.req_data, 'name')
        definition = self._get(self.req_data, 'definition')
        if not project_id or not name or definition is None:
            return 0, 'projectId、name、definition 为必传参数'
        tags = self._get(self.req_data, 'tags', default=[]) or []
        add_info = {
            'project_id': project_id,
            'name': name,
            'description': self._get(self.req_data, 'description'),
            'builder_type': int(self._get(self.req_data, 'builderType', default=1)),
            'definition': definition,
            'input_schema': self._get(self.req_data, 'inputSchema'),
            'output_example': self._get(self.req_data, 'outputExample'),
            'tags': tags,
            'source': self._get(self.req_data, 'source', default='manual') or 'manual',
            'scene_key': self._get(self.req_data, 'sceneKey'),
            'created_by': self._get(self.req_data, 'createdBy'),
            'is_delete': 0,
        }
        return DataBuilderService.create(self.session, DataBuilder, add_info)

    def builder_update(self):
        builder_id = self._get(self.req_data, 'builderId', 'id')
        if not builder_id:
            return 0, 'builderId 为必传参数'
        update_info = {}
        for req_key, column_key in [
            ('name', 'name'),
            ('description', 'description'),
            ('builderType', 'builder_type'),
            ('definition', 'definition'),
            ('inputSchema', 'input_schema'),
            ('outputExample', 'output_example'),
            ('tags', 'tags'),
            ('source', 'source'),
            ('sceneKey', 'scene_key'),
        ]:
            value = self._get(self.req_data, req_key)
            if value is not None:
                update_info[column_key] = value
        return DataBuilderService.update_by_id(self.session, DataBuilder, builder_id, update_info)

    def builder_delete(self):
        builder_id = self._get(self.req_data, 'builderId', 'id')
        if not builder_id:
            return 0, 'builderId 为必传参数'
        return DataBuilderService.delete_by_id(self.session, DataBuilder, builder_id)

    def builder_execute(self):
        builder_id = self._get(self.req_data, 'builderId')
        if not builder_id:
            return {}, 'builderId 为必传参数'
        return DataBuilderService.execute_builder(
            self.session,
            builder_id,
            self._get(self.req_data, 'params', default={}),
            self._get(self.req_data, 'createdBy'),
        )

    def task_status(self):
        task_id = self._get(self.req_data, 'taskId')
        if not task_id:
            return {}, 'taskId 为必传参数'
        item = DataBuilderService.get_by_id(self.session, DataTask, task_id, soft_delete=False)
        if not item:
            return {}, '未查询到对应任务！'
        return self.serialize(item), ''

    def task_list(self):
        items, total = DataBuilderService.list_tasks(
            self.session,
            project_id=self._get(self.req_data, 'projectId'),
            builder_id=self._get(self.req_data, 'builderId'),
            page_no=self._get(self.req_data, 'pageNo', default=1),
            page_size=self._get(self.req_data, 'pageSize', default=20),
        )
        return {'list': self.serialize_list(items), 'total': total}

    def ai_generate(self):
        prompt = self._get(self.req_data, 'prompt')
        return DataBuilderService.ai_generate(
            prompt,
            project_id=self._get(self.req_data, 'projectId'),
            db_project=self._get(self.req_data, 'dbProject', 'db_project'),
            env=self._get(self.req_data, 'env'),
            hint=self._get(self.req_data, 'hint'),
            product_name=self._get(self.req_data, 'productName', 'product_name'),
            project_name=self._get(self.req_data, 'projectName', 'project_name'),
        )

    def ai_refine(self):
        return DataBuilderService.ai_refine(
            self._get(self.req_data, 'draft', default={}),
            self._get(self.req_data, 'instruction'),
            env=self._get(self.req_data, 'env'),
            db_project=self._get(self.req_data, 'dbProject', 'db_project'),
            project_id=self._get(self.req_data, 'projectId'),
            product_name=self._get(self.req_data, 'productName', 'product_name'),
            project_name=self._get(self.req_data, 'projectName', 'project_name'),
        )

    def draft_from_sql(self):
        return DataBuilderService.draft_from_sql(
            self._get(self.req_data, 'sql'),
            project_id=self._get(self.req_data, 'projectId'),
            db_project=self._get(self.req_data, 'dbProject', 'db_project'),
            env=self._get(self.req_data, 'env'),
            name=self._get(self.req_data, 'name'),
            product_name=self._get(self.req_data, 'productName', 'product_name'),
            project_name=self._get(self.req_data, 'projectName', 'project_name'),
        )

    def ocr_generate(self, image_bytes, mime_type=None):
        return DataBuilderService.ocr_generate(
            image_bytes,
            mime_type=mime_type,
            project_id=self._get(self.req_data, 'projectId'),
            db_project=self._get(self.req_data, 'dbProject', 'db_project'),
            env=self._get(self.req_data, 'env'),
            prompt=self._get(self.req_data, 'prompt'),
            product_name=self._get(self.req_data, 'productName', 'product_name'),
            project_name=self._get(self.req_data, 'projectName', 'project_name'),
        )

    def save_as_scene(self):
        return DataBuilderService.save_as_scene(
            self.session,
            self.req_data,
            created_by=self._get(self.req_data, 'createdBy'),
        )
