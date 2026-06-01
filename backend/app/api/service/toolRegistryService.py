# encoding: UTF-8
from ..dao.aiBaseDao import AiBaseDao
from ..dao.aiToolDao import AiToolDao
from ..model.aiToolModel import AiTool, AiToolExecution
from .aiCommonService import AiCommonService
from .safeCommandRunner import SafeCommandRunner


class ToolRegistryService(object):
    CREATE_FIELDS = ['tool_code', 'product_id', 'product_name', 'project_id', 'project_name', 'name', 'tool_type', 'command_template', 'input_schema', 'output_schema', 'artifact_schema', 'parser_type', 'parser_config', 'env_schema', 'timeout_seconds', 'status', 'created_by']
    UPDATE_FIELDS = ['product_id', 'product_name', 'project_id', 'project_name', 'name', 'tool_type', 'command_template', 'input_schema', 'output_schema', 'artifact_schema', 'parser_type', 'parser_config', 'env_schema', 'timeout_seconds', 'status']

    @staticmethod
    def create_tool(session, req_data, user_id=None):
        data = {field: req_data.get(field) for field in ToolRegistryService.CREATE_FIELDS if field in req_data}
        data.update({
            'tool_code': AiCommonService.get(req_data, 'toolCode', 'tool_code'),
            'tool_type': AiCommonService.get(req_data, 'toolType', 'tool_type'),
            'command_template': AiCommonService.get(req_data, 'commandTemplate', 'command_template'),
            'created_by': user_id,
            'is_delete': 0
        })
        AiCommonService.fill_product_project_names(session, data, req_data)
        return AiCommonService.create_record(
            session, AiTool, data, ['tool_code', 'name', 'tool_type', 'command_template'],
            lambda: AiToolDao.get_tool_by_code(session, data.get('tool_code'))
        )

    @staticmethod
    def update_tool(session, req_data):
        AiCommonService.fill_product_project_names(session, req_data, req_data)
        return AiCommonService.update_record(session, AiTool, req_data, ToolRegistryService.UPDATE_FIELDS, ('toolId', 'id'))

    @staticmethod
    def delete_tool(session, req_data):
        return AiCommonService.delete_record(session, AiTool, req_data, ('toolId', 'id'))

    @staticmethod
    def tool_detail(session, tool_id):
        return AiCommonService.detail_record(session, AiTool, tool_id)

    @staticmethod
    def tool_list(session, req_data):
        filters = []
        status = AiCommonService.get(req_data, 'status')
        if status not in (None, ''):
            filters.append(AiTool.status == int(status))
        tool_type = AiCommonService.get(req_data, 'toolType', 'tool_type')
        if tool_type:
            filters.append(AiTool.tool_type == tool_type)
        items, total = AiBaseDao.list_by_filters(session, AiTool, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20), AiCommonService.get(req_data, 'keyword'), ['tool_code', 'name', 'tool_type'])
        return AiCommonService.list_result(items, total, session, True)

    @staticmethod
    def execute_tool(session, req_data, user_id=None):
        tool_id = AiCommonService.get(req_data, 'toolId', 'tool_id')
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        workspace_path = AiCommonService.get(req_data, 'workspacePath', 'workspace_path')
        input_payload = req_data.get('inputPayload') or req_data.get('input_payload') or {}
        if not tool_id or not project_id or not workspace_path:
            return {}, 'toolId、projectId、workspacePath 为必传参数'
        tool = AiBaseDao.get_by_id(session, AiTool, tool_id)
        if not tool:
            return {}, '未查询到工具'
        if int(tool.status) != 1:
            return {}, '工具未启用'
        if AiToolDao.count_running_execution(session, tool.id) >= 1:
            return {}, '工具执行已达到最大并发'
        command_text, err_msg = SafeCommandRunner.render_command(tool.command_template, input_payload)
        if err_msg:
            return {}, err_msg
        execution_no = AiCommonService.gen_no('TOL')
        execution, err_msg = AiBaseDao.create(session, AiToolExecution, {
            'execution_no': execution_no,
            'tool_id': tool.id,
            'project_id': int(project_id),
            'ai_task_id': AiCommonService.get(req_data, 'aiTaskId', 'ai_task_id'),
            'workspace_path': workspace_path,
            'input_payload': input_payload,
            'command_snapshot': command_text,
            'status': 'running',
            'trigger_by': user_id
        })
        if err_msg:
            return {}, err_msg
        result, run_err = SafeCommandRunner.run(command_text, workspace_path, tool.timeout_seconds, None, {}, execution_no)
        update_info = {
            'status': result.get('status'),
            'result_summary': result,
            'stdout_path': result.get('stdoutPath'),
            'stderr_path': result.get('stderrPath'),
            'duration_seconds': result.get('durationSeconds'),
            'error_message': run_err or result.get('errorMessage')
        }
        AiBaseDao.update_by_id(session, AiToolExecution, execution.id, update_info)
        return {'executionId': execution.id, 'executionNo': execution_no, 'result': result}, '' if result.get('status') == 'success' else run_err

    @staticmethod
    def execution_list(session, req_data):
        filters = []
        tool_id = AiCommonService.get(req_data, 'toolId', 'tool_id')
        if tool_id:
            filters.append(AiToolExecution.tool_id == int(tool_id))
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(AiToolExecution.project_id == int(project_id))
        status = AiCommonService.get(req_data, 'status')
        if status:
            filters.append(AiToolExecution.status == status)
        items, total = AiBaseDao.list_by_filters(session, AiToolExecution, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20))
        return AiCommonService.list_result(items, total)

    @staticmethod
    def execution_detail(session, execution_id):
        return AiCommonService.detail_record(session, AiToolExecution, execution_id)
