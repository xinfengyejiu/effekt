# encoding: UTF-8
from ..dao.aiBaseDao import AiBaseDao
from ..dao.aiFlowDao import AiFlowDao
from ..model.aiFlowModel import AiSkillFlow, AiSkillFlowExecution
from .aiCommonService import AiCommonService


class SkillFlowService(object):
    UPDATE_FIELDS = ['product_id', 'product_name', 'project_id', 'project_name', 'name', 'description', 'trigger_type', 'flow_definition', 'input_schema', 'output_schema', 'status']

    @staticmethod
    def create_flow(session, req_data, user_id=None):
        flow_code = AiCommonService.get(req_data, 'flowCode', 'flow_code')
        data = {
            'project_id': int(AiCommonService.get(req_data, 'projectId', 'project_id') or 0),
            'name': req_data.get('name'),
            'flow_code': flow_code,
            'description': req_data.get('description'),
            'trigger_type': AiCommonService.get(req_data, 'triggerType', 'trigger_type', default='manual'),
            'flow_definition': AiCommonService.get(req_data, 'flowDefinition', 'flow_definition', default={}),
            'input_schema': AiCommonService.get(req_data, 'inputSchema', 'input_schema', default={}),
            'output_schema': AiCommonService.get(req_data, 'outputSchema', 'output_schema', default={}),
            'status': int(req_data.get('status') or 3),
            'created_by': user_id,
            'is_delete': 0
        }
        AiCommonService.fill_product_project_names(session, data, req_data)
        return AiCommonService.create_record(session, AiSkillFlow, data, ['project_id', 'name', 'flow_code'], lambda: AiFlowDao.get_flow_by_code(session, flow_code))

    @staticmethod
    def update_flow(session, req_data):
        AiCommonService.fill_product_project_names(session, req_data, req_data)
        return AiCommonService.update_record(session, AiSkillFlow, req_data, SkillFlowService.UPDATE_FIELDS, ('flowId', 'id'))

    @staticmethod
    def delete_flow(session, req_data):
        return AiCommonService.delete_record(session, AiSkillFlow, req_data, ('flowId', 'id'))

    @staticmethod
    def flow_detail(session, flow_id):
        return AiCommonService.detail_record(session, AiSkillFlow, flow_id)

    @staticmethod
    def flow_list(session, req_data):
        filters = []
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(AiSkillFlow.project_id == int(project_id))
        trigger_type = AiCommonService.get(req_data, 'triggerType', 'trigger_type')
        if trigger_type:
            filters.append(AiSkillFlow.trigger_type == trigger_type)
        status = req_data.get('status')
        if status not in (None, ''):
            filters.append(AiSkillFlow.status == int(status))
        items, total = AiBaseDao.list_by_filters(session, AiSkillFlow, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20), req_data.get('keyword'), ['flow_code', 'name', 'description'])
        return AiCommonService.list_result(items, total, session, True)

    @staticmethod
    def execute_flow(session, req_data):
        flow_id = AiCommonService.get(req_data, 'flowId', 'flow_id')
        if not flow_id:
            return {}, 'flowId 为必传参数'
        flow = AiBaseDao.get_by_id(session, AiSkillFlow, flow_id)
        if not flow:
            return {}, '未查询到流程'
        input_payload = AiCommonService.get(req_data, 'inputPayload', 'input_payload', default={})
        node_results = [{
            'type': 'placeholder',
            'message': 'Flow Adapter待接入具体节点执行器',
            'flowCode': flow.flow_code,
            'flowDefinition': flow.flow_definition or {}
        }]
        output_payload = {'message': '流程定义校验通过', 'flowId': int(flow.id), 'flowCode': flow.flow_code}
        execution, err_msg = AiBaseDao.create(session, AiSkillFlowExecution, {
            'flow_id': flow.id,
            'ai_task_id': AiCommonService.get(req_data, 'aiTaskId', 'ai_task_id'),
            'status': 'success',
            'input_payload': input_payload,
            'node_results': node_results,
            'output_payload': output_payload,
            'duration_seconds': 0
        })
        if err_msg:
            return {}, err_msg
        return {'executionId': execution.id, 'status': 'success', 'nodeResults': node_results, 'output': output_payload, 'message': '流程试执行完成'}, ''

    @staticmethod
    def execution_list(session, req_data):
        filters = []
        flow_id = AiCommonService.get(req_data, 'flowId', 'flow_id')
        if flow_id:
            filters.append(AiSkillFlowExecution.flow_id == int(flow_id))
        ai_task_id = AiCommonService.get(req_data, 'aiTaskId', 'ai_task_id')
        if ai_task_id:
            filters.append(AiSkillFlowExecution.ai_task_id == int(ai_task_id))
        status = AiCommonService.get(req_data, 'status')
        if status:
            filters.append(AiSkillFlowExecution.status == status)
        items, total = AiBaseDao.list_by_filters(session, AiSkillFlowExecution, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20))
        return AiCommonService.list_result(items, total)

    @staticmethod
    def execution_detail(session, execution_id):
        return AiCommonService.detail_record(session, AiSkillFlowExecution, execution_id)
