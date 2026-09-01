# encoding: UTF-8
from datetime import datetime
import json

from .baseCrudController import BaseCrudController
from ..model.planModel import PlanCase, TestPlan, TestRound
from ..model.caseModel import Module, TestCase
from ..service.planService import PlanService
from ..service.userService import UserService


class PlanController(BaseCrudController):
    def plan_list(self):
        filters = []
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        status = self._get(self.req_data, 'status')
        keyword = self._get(self.req_data, 'keyword')
        owner_id = self._get(self.req_data, 'ownerId', 'owner_id', 'owner')
        if project_id:
            filters.append(TestPlan.project_id == int(project_id))
        if status not in (None, ''):
            filters.append(TestPlan.status == int(status))
        if keyword:
            filters.append(TestPlan.name.like('%{}%'.format(keyword)))
        if owner_id:
            filters.append(TestPlan.owner_id == int(owner_id))
        
        items, total = PlanService.list_by_filters(self.session, TestPlan, filters, self._get(self.req_data, 'pageNo', 'page', default=1), self._get(self.req_data, 'pageSize', 'size', default=20), TestPlan.created_time)
        
        owner_ids = [item.owner_id for item in items if item.owner_id]
        user_info_map = UserService.get_user_info_map(self.session, owner_ids) if owner_ids else {}
        
        result_list = []
        for item in items:
            plan_dict = item.to_dict()
            if item.owner_id and item.owner_id in user_info_map:
                plan_dict['owner_name'] = user_info_map[item.owner_id].get('real_name', '')
            else:
                plan_dict['owner_name'] = ''
            result_list.append(plan_dict)
        
        return {'list': result_list, 'total': total}

    def plan_detail(self):
        plan_id = self._get(self.req_data, 'planId', 'id')
        if not plan_id:
            return {}, 'planId 为必传参数'
        item = PlanService.get_by_id(self.session, TestPlan, plan_id)
        if not item:
            return {}, '未查询到对应计划！'
        ret = self.serialize(item, ['is_delete'])
        ret.update(PlanService.plan_stats(self.session, plan_id))
        return ret, ''

    def plan_create(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        name = self._get(self.req_data, 'name')
        if not project_id or not name:
            return 0, 'projectId、name 为必传参数'
        add_info = {'project_id': project_id, 'name': name, 'version': self._get(self.req_data, 'version'), 'description': self._get(self.req_data, 'description'), 'start_date': self._get(self.req_data, 'startDate', 'start_time'), 'end_date': self._get(self.req_data, 'endDate', 'end_time'), 'owner_id': self._get(self.req_data, 'ownerId', 'owner_id'), 'status': int(self._get(self.req_data, 'status', default=0)), 'environment_id': self._get(self.req_data, 'environmentId', 'environment_id'), 'jenkins_url': self._get(self.req_data, 'jenkinsUrl', 'jenkins_url'), 'is_auto': int(self._get(self.req_data, 'isAuto', 'is_auto', default=0)), 'is_delete': 0}
        return PlanService.create(self.session, TestPlan, add_info)

    def plan_update(self):
        """更新测试计划，只更新请求中传入的字段。"""
        plan_id = self._get(self.req_data, 'planId', 'id')
        if not plan_id:
            return 0, 'planId 为必传参数'
        update_info = {}
        for req_keys, column_key in [(('name', 'name'), 'name'), (('version', 'version'), 'version'), (('description', 'description'), 'description'), (('startDate', 'start_time', 'start_date'), 'start_date'), (('endDate', 'end_time', 'end_date'), 'end_date'), (('ownerId', 'owner_id'), 'owner_id'), (('status', 'status'), 'status'), (('environmentId', 'environment_id'), 'environment_id'), (('jenkinsUrl', 'jenkins_url'), 'jenkins_url'), (('isAuto', 'is_auto'), 'is_auto')]:
            value = self._get(self.req_data, *req_keys)
            if value is not None:
                update_info[column_key] = value
        return PlanService.update_by_id(self.session, TestPlan, plan_id, update_info)

    def plan_delete(self):
        plan_id = self._get(self.req_data, 'planId', 'id')
        if not plan_id:
            return 0, 'planId 为必传参数'
        return PlanService.delete_by_id(self.session, TestPlan, plan_id)

    def round_create(self):
        plan_id = self._get(self.req_data, 'planId')
        round_no = self._get(self.req_data, 'roundNo')
        if not plan_id or not round_no:
            return 0, 'planId、roundNo 为必传参数'
        return PlanService.create(self.session, TestRound, {'plan_id': plan_id, 'round_no': round_no, 'name': self._get(self.req_data, 'name'), 'start_date': self._get(self.req_data, 'startDate'), 'end_date': self._get(self.req_data, 'endDate')})

    def round_list(self):
        plan_id = self._get(self.req_data, 'planId')
        filters = [TestRound.plan_id == int(plan_id)] if plan_id else []
        items, total = PlanService.list_by_filters(self.session, TestRound, filters, self._get(self.req_data, 'pageNo', default=1), self._get(self.req_data, 'pageSize', default=50), TestRound.id)
        return {'list': self.serialize_list(items), 'total': total}

    def plan_case_add(self):
        plan_id = self._get(self.req_data, 'planId')
        case_ids = self._get(self.req_data, 'caseIds', default=[])
        if not plan_id or not case_ids:
            return 0, 'planId、caseIds 为必传参数'
        batch_info_list = [{'plan_id': plan_id, 'case_id': case_id, 'assignee_id': self._get(self.req_data, 'assigneeId'), 'round_no': int(self._get(self.req_data, 'roundNo', default=1)), 'status': 0} for case_id in case_ids]
        return PlanService.batch_create(self.session, PlanCase, batch_info_list)

    def plan_case_list(self):
        plan_id = self._get(self.req_data, 'planId', 'plan_id')
        filters = [PlanCase.plan_id == int(plan_id)] if plan_id else []
        round_no = self._get(self.req_data, 'roundNo')
        if round_no not in (None, ''):
            filters.append(PlanCase.round_no == int(round_no))
        items, total = PlanService.list_by_filters(self.session, PlanCase, filters, self._get(self.req_data, 'pageNo', default=1), self._get(self.req_data, 'pageSize', default=20), PlanCase.id, asc=True)
        
        case_ids = [item.case_id for item in items if item.case_id]
        case_info_map = {}
        module_info_map = {}
        if case_ids:
            cases = self.session.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_delete == 0).all()
            case_info_map = {case.id: {'case_key': case.case_key, 'title': case.title, 'module_id': case.module_id} for case in cases}
            
            module_ids = [case.module_id for case in cases if case.module_id]
            if module_ids:
                modules = self.session.query(Module).filter(Module.id.in_(module_ids), Module.is_delete == 0).all()
                module_info_map = {module.id: {'name': module.name, 'path': module.path} for module in modules}
        
        result_list = []
        for item in items:
            case_dict = item.to_dict()
            if item.case_id and item.case_id in case_info_map:
                case_dict['case_key'] = case_info_map[item.case_id]['case_key']
                case_dict['case_title'] = case_info_map[item.case_id]['title']
                module_id = case_info_map[item.case_id].get('module_id')
                if module_id and module_id in module_info_map:
                    case_dict['module_name'] = module_info_map[module_id]['name']
                    case_dict['module_path'] = module_info_map[module_id].get('path', '')
                else:
                    case_dict['module_name'] = ''
                    case_dict['module_path'] = ''
            else:
                case_dict['case_key'] = ''
                case_dict['case_title'] = ''
                case_dict['module_name'] = ''
                case_dict['module_path'] = ''
            result_list.append(case_dict)
        
        return {'list': result_list, 'total': total}

    def plan_case_execute(self):
        plan_case_id = self._get(self.req_data, 'planCaseId', 'id')
        if not plan_case_id:
            return 0, 'planCaseId 为必传参数'
        
        plan_case = PlanService.get_by_id(self.session, PlanCase, plan_case_id, soft_delete=False)
        if not plan_case:
            return 0, '未查询到对应计划用例！'
        
        plan_id = plan_case.plan_id
        
        update_info = {'status': int(self._get(self.req_data, 'status', default=0)), 'actual_result': self._get(self.req_data, 'actualResult'), 'defect_links': self._get(self.req_data, 'defectLinks', default=[]), 'attachments': self._get(self.req_data, 'attachments', default=[]), 'executed_time': datetime.now(), 'execution_duration': self._get(self.req_data, 'executionDuration')}
        result = PlanService.update_by_id(self.session, PlanCase, plan_case_id, update_info, soft_delete=False)
        
        PlanService.refresh_plan_status(self.session, plan_id)
        
        return result

    def plan_case_ai_execute(self):
        from ..service.aiService import AIService

        plan_id = self._get(self.req_data, 'planId', 'plan_id')
        plan_case_id = self._get(self.req_data, 'planCaseId', 'id')
        if not plan_id:
            return {}, 'planId 为必传参数'

        plan = PlanService.get_by_id(self.session, TestPlan, plan_id)
        if not plan:
            return {}, '未查询到对应计划！'
        test_url = (plan.description or '').strip()
        if not test_url:
            return {}, '计划描述为空，请在计划描述中填写本次测试地址 URL'

        filters = [PlanCase.plan_id == int(plan_id)]
        if plan_case_id:
            filters.append(PlanCase.id == int(plan_case_id))
        else:
            filters.append(PlanCase.status.in_([0, 2, 3]))
        plan_cases = self.session.query(PlanCase).filter(*filters).order_by(PlanCase.id.asc()).all()
        if not plan_cases:
            return {'total': 0, 'passed': 0, 'failed': 0, 'blocked': 0, 'results': []}, ''

        case_ids = [item.case_id for item in plan_cases if item.case_id]
        case_map = {}
        module_map = {}
        if case_ids:
            cases = self.session.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_delete == 0).all()
            case_map = {case.id: case for case in cases}
            module_ids = [case.module_id for case in cases if case.module_id]
            if module_ids:
                modules = self.session.query(Module).filter(Module.id.in_(module_ids), Module.is_delete == 0).all()
                module_map = {module.id: module for module in modules}

        results = []
        for plan_case in plan_cases:
            case = case_map.get(plan_case.case_id)
            if not case:
                actual_result = 'AI执行阻塞：未找到关联用例，无法获取用例步骤和预期结果'
                PlanService.update_by_id(self.session, PlanCase, plan_case.id, {
                    'status': 3,
                    'actual_result': actual_result,
                    'defect_links': [],
                    'attachments': [],
                    'executed_time': datetime.now(),
                    'execution_duration': None
                }, soft_delete=False)
                results.append({
                    'planCaseId': plan_case.id,
                    'caseId': plan_case.case_id,
                    'caseKey': '',
                    'caseTitle': '',
                    'status': 3,
                    'statusLabel': '阻塞',
                    'actualResult': actual_result,
                    'reason': '未找到关联用例'
                })
                continue
            module = module_map.get(case.module_id)
            steps = self._normalize_case_text(case.steps)
            expected_results = self._normalize_case_text(case.expected_results)
            ai_result, err_msg = AIService.execute_test_case_by_ai({
                'testUrl': test_url,
                'planName': plan.name,
                'planVersion': plan.version,
                'caseKey': case.case_key,
                'caseTitle': case.title,
                'modulePath': module.path if module else '',
                'moduleName': module.name if module else '',
                'preconditions': self._normalize_case_text(case.preconditions),
                'steps': steps,
                'expectedResults': expected_results
            })
            if err_msg:
                status = 3
                actual_result = f'AI执行失败：{err_msg}'
                reason = err_msg
            else:
                status = self._normalize_ai_execute_status(ai_result)
                actual_result = self._format_ai_execute_result(ai_result)
                reason = ai_result.get('reason', '')
            PlanService.update_by_id(self.session, PlanCase, plan_case.id, {
                'status': status,
                'actual_result': actual_result,
                'defect_links': [],
                'attachments': [],
                'executed_time': datetime.now(),
                'execution_duration': None
            }, soft_delete=False)
            results.append({
                'planCaseId': plan_case.id,
                'caseId': plan_case.case_id,
                'caseKey': case.case_key,
                'caseTitle': case.title,
                'status': status,
                'statusLabel': self._execute_status_label(status),
                'actualResult': actual_result,
                'reason': reason
            })

        PlanService.refresh_plan_status(self.session, plan_id)
        return {
            'total': len(results),
            'passed': len([item for item in results if item.get('status') == 1]),
            'failed': len([item for item in results if item.get('status') == 2]),
            'blocked': len([item for item in results if item.get('status') == 3]),
            'results': results
        }, ''

    @staticmethod
    def _normalize_case_text(value):
        if value is None:
            return ''
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        text = str(value)
        try:
            parsed = json.loads(text)
            if isinstance(parsed, (dict, list)):
                return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass
        return text

    @staticmethod
    def _normalize_ai_execute_status(ai_result):
        status = str((ai_result or {}).get('status') or '').lower()
        if status in ('pass', 'passed', 'success', '1', '通过'):
            return 1
        if status in ('fail', 'failed', 'failure', '2', '失败'):
            return 2
        return 3

    @staticmethod
    def _execute_status_label(status):
        return {1: '通过', 2: '失败', 3: '阻塞'}.get(status, '待执行')

    @staticmethod
    def _format_ai_execute_result(ai_result):
        ai_result = ai_result or {}
        lines = [f"AI执行结论：{PlanController._execute_status_label(PlanController._normalize_ai_execute_status(ai_result))}"]
        for label, key in [('实际结果', 'actualResult'), ('失败原因', 'reason'), ('执行过程', 'evidence'), ('建议', 'suggestion')]:
            value = ai_result.get(key)
            if value:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                lines.append(f'{label}：{value}')
        return '\n'.join(lines)

    def progress(self):
        """查询计划进度统计。"""
        plan_id = self._get(self.req_data, 'planId', 'plan_id')
        if not plan_id:
            return {}, 'planId 为必传参数'
        return PlanService.plan_stats(self.session, plan_id), ''
