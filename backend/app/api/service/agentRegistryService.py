# encoding: UTF-8
from ..dao.aiAgentDao import AiAgentDao
from ..dao.aiBaseDao import AiBaseDao
from ..model.aiAgentModel import AiAgent, AiAgentExecution
from .aiCommonService import AiCommonService
from .safeCommandRunner import SafeCommandRunner


class AgentRegistryService(object):
    CREATE_FIELDS = ['agent_code', 'product_id', 'product_name', 'project_id', 'project_name', 'name', 'agent_type', 'entrypoint', 'version', 'description', 'capabilities', 'supported_tasks', 'permission_policy', 'workspace_policy', 'timeout_seconds', 'max_concurrency', 'cost_policy', 'status', 'created_by']
    UPDATE_FIELDS = ['product_id', 'product_name', 'project_id', 'project_name', 'name', 'agent_type', 'entrypoint', 'version', 'description', 'capabilities', 'supported_tasks', 'permission_policy', 'workspace_policy', 'timeout_seconds', 'max_concurrency', 'cost_policy', 'status']

    @staticmethod
    def create_agent(session, req_data, user_id=None):
        data = {field: req_data.get(field) for field in AgentRegistryService.CREATE_FIELDS if field in req_data}
        data.update({
            'agent_code': AiCommonService.get(req_data, 'agentCode', 'agent_code'),
            'agent_type': int(AiCommonService.get(req_data, 'agentType', 'agent_type', default=1)),
            'created_by': user_id,
            'is_delete': 0
        })
        AiCommonService.fill_product_project_names(session, data, req_data)
        return AiCommonService.create_record(
            session, AiAgent, data, ['agent_code', 'name', 'entrypoint'],
            lambda: AiAgentDao.get_agent_by_code(session, data.get('agent_code'))
        )

    @staticmethod
    def update_agent(session, req_data):
        AiCommonService.fill_product_project_names(session, req_data, req_data)
        return AiCommonService.update_record(session, AiAgent, req_data, AgentRegistryService.UPDATE_FIELDS, ('agentId', 'id'))

    @staticmethod
    def delete_agent(session, req_data):
        return AiCommonService.delete_record(session, AiAgent, req_data, ('agentId', 'id'))

    @staticmethod
    def agent_detail(session, agent_id):
        return AiCommonService.detail_record(session, AiAgent, agent_id)

    @staticmethod
    def agent_list(session, req_data):
        filters = []
        status = AiCommonService.get(req_data, 'status')
        if status not in (None, ''):
            filters.append(AiAgent.status == int(status))
        agent_type = AiCommonService.get(req_data, 'agentType', 'agent_type')
        if agent_type not in (None, ''):
            filters.append(AiAgent.agent_type == int(agent_type))
        items, total = AiBaseDao.list_by_filters(
            session, AiAgent, filters,
            AiCommonService.get(req_data, 'page', default=1),
            AiCommonService.get(req_data, 'limit', default=20),
            AiCommonService.get(req_data, 'keyword'),
            ['agent_code', 'name', 'entrypoint', 'description']
        )
        return AiCommonService.list_result(items, total, session, True)

    @staticmethod
    def execute_agent(session, req_data, user_id=None):
        agent_id = AiCommonService.get(req_data, 'agentId', 'agent_id')
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        workspace_path = AiCommonService.get(req_data, 'workspacePath', 'workspace_path')
        if not agent_id or not project_id or not workspace_path:
            return {}, 'agentId、projectId、workspacePath 为必传参数'
        agent = AiBaseDao.get_by_id(session, AiAgent, agent_id)
        if not agent:
            return {}, '未查询到Agent'
        if int(agent.status) != 1:
            return {}, 'Agent未启用'
        if AiAgentDao.count_running_execution(session, agent.id) >= int(agent.max_concurrency or 1):
            return {}, 'Agent执行已达到最大并发'
        command_text = req_data.get('command') or agent.entrypoint
        execution_no = AiCommonService.gen_no('AGT')
        execution, err_msg = AiBaseDao.create(session, AiAgentExecution, {
            'execution_no': execution_no,
            'agent_id': agent.id,
            'project_id': int(project_id),
            'workspace_path': workspace_path,
            'task_type': AiCommonService.get(req_data, 'taskType', 'task_type'),
            'input_payload': req_data.get('inputPayload') or req_data.get('input_payload') or {},
            'command_snapshot': command_text,
            'status': 'running',
            'trigger_by': user_id
        })
        if err_msg:
            return {}, err_msg
        result, run_err = SafeCommandRunner.run(
            command_text=command_text,
            workspace_path=workspace_path,
            timeout_seconds=agent.timeout_seconds,
            entrypoint=agent.entrypoint,
            workspace_policy=agent.workspace_policy or {},
            log_prefix=execution_no
        )
        update_info = {
            'status': result.get('status'),
            'stdout_path': result.get('stdoutPath'),
            'stderr_path': result.get('stderrPath'),
            'result_payload': result,
            'error_message': run_err or result.get('errorMessage'),
            'duration_seconds': result.get('durationSeconds')
        }
        AiBaseDao.update_by_id(session, AiAgentExecution, execution.id, update_info)
        return {'executionId': execution.id, 'executionNo': execution_no, 'result': result}, '' if result.get('status') == 'success' else run_err

    @staticmethod
    def execution_list(session, req_data):
        filters = []
        agent_id = AiCommonService.get(req_data, 'agentId', 'agent_id')
        if agent_id:
            filters.append(AiAgentExecution.agent_id == int(agent_id))
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(AiAgentExecution.project_id == int(project_id))
        status = AiCommonService.get(req_data, 'status')
        if status:
            filters.append(AiAgentExecution.status == status)
        items, total = AiBaseDao.list_by_filters(session, AiAgentExecution, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20))
        rows = AiCommonService.fill_product_project_list(session, items)
        agent_ids = [row.get('agentId') or row.get('agent_id') for row in rows if row.get('agentId') or row.get('agent_id')]
        agents = {}
        if agent_ids:
            agent_rows = session.query(AiAgent).filter(AiAgent.id.in_([int(i) for i in agent_ids]), AiAgent.is_delete == 0).all()
            agents = {int(item.id): item for item in agent_rows}
        for row in rows:
            row_agent_id = row.get('agentId') or row.get('agent_id')
            agent = agents.get(int(row_agent_id)) if row_agent_id else None
            if agent:
                row['agentCode'] = agent.agent_code
                row['agent_code'] = agent.agent_code
                row['agentName'] = agent.name
                row['agent_name'] = agent.name
        return {'list': rows, 'total': total}

    @staticmethod
    def execution_detail(session, execution_id):
        return AiCommonService.detail_record(session, AiAgentExecution, execution_id)
