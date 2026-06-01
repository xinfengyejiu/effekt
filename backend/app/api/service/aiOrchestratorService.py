# encoding: UTF-8
from ..dao.aiBaseDao import AiBaseDao
from ..model.aiTaskModel import AiTestTask, AiTestTaskStep
from .aiCommonService import AiCommonService
from .riskAnalysisService import RiskAnalysisService
from .testRecommendationService import TestRecommendationService


class AiOrchestratorService(object):
    @staticmethod
    def create_task(session, req_data, user_id=None):
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        task_type = AiCommonService.get(req_data, 'taskType', 'task_type')
        if not project_id or not task_type:
            return 0, 'projectId、taskType 为必传参数'
        task_no = AiCommonService.get(req_data, 'taskNo', 'task_no') or AiCommonService.gen_no('AIT')
        data = {
            'task_no': task_no,
            'project_id': int(project_id),
            'task_type': task_type,
            'source_type': AiCommonService.get(req_data, 'sourceType', 'source_type', default='manual'),
            'source_id': AiCommonService.get(req_data, 'sourceId', 'source_id'),
            'source_payload': AiCommonService.get(req_data, 'sourcePayload', 'source_payload', default={}),
            'status': 'pending',
            'selected_agents': AiCommonService.get(req_data, 'selectedAgents', 'selected_agents', default=[]),
            'selected_tools': AiCommonService.get(req_data, 'selectedTools', 'selected_tools', default=[]),
            'selected_skills': AiCommonService.get(req_data, 'selectedSkills', 'selected_skills', default=[]),
            'created_by': user_id,
            'is_delete': 0
        }
        AiCommonService.fill_product_project_names(session, data, req_data)
        obj, err_msg = AiBaseDao.create(session, AiTestTask, data)
        if err_msg:
            return 0, err_msg
        return obj.id, ''

    @staticmethod
    def task_list(session, req_data):
        filters = []
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(AiTestTask.project_id == int(project_id))
        task_type = AiCommonService.get(req_data, 'taskType', 'task_type')
        if task_type:
            filters.append(AiTestTask.task_type == task_type)
        status = req_data.get('status')
        if status:
            filters.append(AiTestTask.status == status)
        items, total = AiBaseDao.list_by_filters(session, AiTestTask, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20), req_data.get('keyword'), ['task_no', 'task_type', 'source_type'])
        return AiCommonService.list_result(items, total, session, True)

    @staticmethod
    def task_detail(session, task_id):
        task = AiBaseDao.get_by_id(session, AiTestTask, task_id)
        if not task:
            return {}, '未查询到AI任务'
        steps = session.query(AiTestTaskStep).filter(AiTestTaskStep.task_id == int(task_id)).order_by(AiTestTaskStep.step_order.asc()).all()
        data = AiCommonService.list_result([task], 1)['list'][0]
        data['steps'] = AiCommonService.list_result(steps, len(steps))['list']
        return data, ''

    @staticmethod
    def cancel_task(session, req_data):
        task_id = AiCommonService.get(req_data, 'taskId', 'task_id')
        if not task_id:
            return 0, 'taskId 为必传参数'
        task = AiBaseDao.get_by_id(session, AiTestTask, task_id)
        if not task:
            return 0, '未查询到AI任务'
        if task.status in {'success', 'failed', 'canceled'}:
            return 0, '当前任务状态不可取消'
        return AiBaseDao.update_by_id(session, AiTestTask, task.id, {'status': 'canceled'})

    @staticmethod
    def execute_task(session, req_data):
        task_id = AiCommonService.get(req_data, 'taskId', 'task_id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        task = AiBaseDao.get_by_id(session, AiTestTask, task_id)
        if not task:
            return {}, '未查询到AI任务'
        if task.task_type not in {'pr_risk', 'requirement_case', 'regression_select', 'release_gate'}:
            return {}, '当前任务类型暂不支持自动执行'
        AiBaseDao.update_by_id(session, AiTestTask, task.id, {'status': 'running'})
        step, _ = AiBaseDao.create(session, AiTestTaskStep, {
            'task_id': task.id,
            'step_order': 1,
            'step_type': 'risk_analysis',
            'status': 'running',
            'input_payload': task.source_payload or {}
        })
        analysis_result, err_msg = RiskAnalysisService.analyze_requirement({'sourcePayload': task.source_payload or {}})
        if err_msg:
            if step:
                AiBaseDao.update_by_id(session, AiTestTaskStep, step.id, {'status': 'failed', 'error_message': err_msg})
            AiBaseDao.update_by_id(session, AiTestTask, task.id, {'status': 'failed', 'result_summary': {'error': err_msg}})
            return {}, err_msg
        recommended_tests = TestRecommendationService.normalize_recommendations(analysis_result)
        if step:
            AiBaseDao.update_by_id(session, AiTestTaskStep, step.id, {'status': 'success', 'output_payload': analysis_result})
        AiBaseDao.update_by_id(session, AiTestTask, task.id, {
            'status': 'success',
            'risk_level': analysis_result.get('risk_level'),
            'recommended_tests': recommended_tests,
            'result_summary': analysis_result
        })
        return {'taskId': task.id, 'analysis': analysis_result}, ''
