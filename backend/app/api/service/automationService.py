# encoding: UTF-8
import secrets
from datetime import datetime

from ..dao.automationDao import AutomationDao
from ..model.automationModel import AutoExecution, AutoExecutionCase
from ..model.planModel import PlanCase
from ..service.planService import PlanService
from common.jenkinsRequest import JenkinsRequest
from const import JENKINS_DEFAULT_JOB, PLATFORM_BASE_URL
from logger import logger

class AutomationService(object):
    STATUS_PENDING = 0
    STATUS_TRIGGERING = 1
    STATUS_QUEUED = 2
    STATUS_RUNNING = 3
    STATUS_SUCCESS = 4
    STATUS_FAILED = 5
    STATUS_CANCELED = 6
    STATUS_TRIGGER_FAILED = 7
    STATUS_CALLBACK_ERROR = 8

    CASE_STATUS_PENDING = 0
    CASE_STATUS_RUNNING = 1
    CASE_STATUS_PASSED = 2
    CASE_STATUS_FAILED = 3
    CASE_STATUS_BLOCKED = 4
    CASE_STATUS_SKIPPED = 5
    CASE_STATUS_NOT_FOUND = 6
    CASE_STATUS_CANCELED = 7

    PLAN_CASE_STATUS_MAP = {
        CASE_STATUS_PASSED: 1,
        CASE_STATUS_FAILED: 2,
        CASE_STATUS_BLOCKED: 3,
    }

    @staticmethod
    def generate_execution_no():
        return 'AE' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]

    @staticmethod
    def generate_callback_token():
        return secrets.token_hex(16)

    @staticmethod
    def create_case_execution(session, req_data, user_id):
        case_id = req_data.get('caseId') or req_data.get('case_id')
        env_code = req_data.get('envCode') or req_data.get('env_code')
        if not case_id or not env_code:
            return {}, 'caseId、envCode 为必传参数'
        case_item = AutomationDao.query_case_auto_item(session, case_id)
        if not case_item:
            return {}, '该用例不存在或未接入自动化'
        running_exists = AutomationService.get_running_execution_by_case(session, case_id, env_code)
        if running_exists:
            return {}, '该用例在当前环境已有执行中任务'
        callback_token = AutomationService.generate_callback_token()
        execution_obj, err_msg = AutomationDao.create_execution(session, {
            'execution_no': AutomationService.generate_execution_no(),
            'trigger_type': 1,
            'project_id': case_item.project_id,
            'source_case_id': case_item.id,
            'env_code': env_code,
            'run_mode': int(req_data.get('runMode') or req_data.get('run_mode') or 1),
            'status': AutomationService.STATUS_PENDING,
            'total_count': 1,
            'pending_count': 1,
            'running_count': 0,
            'passed_count': 0,
            'failed_count': 0,
            'blocked_count': 0,
            'skipped_count': 0,
            'not_found_count': 0,
            'trigger_by': user_id,
            'trigger_message': req_data.get('remark'),
            'callback_token': callback_token,
            'ext': {}
        })
        if err_msg:
            return {}, err_msg
        _, err_msg = AutomationDao.batch_create_execution_cases(session, [{
            'execution_id': execution_obj.id,
            'case_id': case_item.id,
            'case_key': case_item.case_key,
            'case_title': case_item.title,
            'run_order': 1,
            'status': AutomationService.CASE_STATUS_PENDING
        }])
        if err_msg:
            return {}, err_msg
        trigger_ok, trigger_msg = AutomationService.trigger_jenkins(session, execution_obj.id, req_data.get('jenkinsJobName'))
        if not trigger_ok:
            return {}, trigger_msg
        execution = AutomationDao.get_execution_by_id(session, execution_obj.id)
        return execution.to_dict() if execution else {'id': execution_obj.id}, ''

    @staticmethod
    def create_plan_execution(session, req_data, user_id):
        from logger import logger
        
        plan_id = req_data.get('planId') or req_data.get('plan_id')
        env_code = req_data.get('envCode') or req_data.get('env_code')
        round_no = req_data.get('roundNo') or req_data.get('round_no')
        case_ids = req_data.get('caseIds') or req_data.get('case_ids') or []
        
        logger.info(f'====== 计划自动化执行开始 ======')
        logger.info(f'请求参数: plan_id={plan_id}, env_code={env_code}, round_no={round_no}, case_ids={case_ids}, user_id={user_id}')
        
        if not plan_id or not env_code:
            logger.error('参数校验失败: planId、envCode 为必传参数')
            return {}, 'planId、envCode 为必传参数'
        
        running_exists = AutomationService.get_running_execution_by_plan(session, plan_id, env_code)
        if running_exists:
            logger.error(f'计划执行冲突: 计划 {plan_id} 在环境 {env_code} 已有执行中任务')
            return {}, '该计划在当前环境已有执行中任务'
        
        logger.info(f'查询计划自动化用例: plan_id={plan_id}, round_no={round_no}')
        items = AutomationDao.query_plan_auto_cases(session, plan_id, round_no, case_ids)
        if not items:
            logger.error('计划下无可执行自动化用例')
            return {}, '计划下无可执行自动化用例'
        
        logger.info(f'查询到 {len(items)} 条自动化用例')
        for idx, (plan_case, case_item) in enumerate(items, start=1):
            logger.info(f'  {idx}. case_key={case_item.case_key}, case_title={case_item.title}')
        
        project_id = items[0][1].project_id
        callback_token = AutomationService.generate_callback_token()
        execution_no = AutomationService.generate_execution_no()
        
        logger.info(f'创建执行记录: execution_no={execution_no}, project_id={project_id}, plan_id={plan_id}')
        execution_obj, err_msg = AutomationDao.create_execution(session, {
            'execution_no': execution_no,
            'trigger_type': 2,
            'project_id': project_id,
            'plan_id': int(plan_id),
            'plan_round_no': int(round_no) if round_no not in (None, '') else None,
            'env_code': env_code,
            'run_mode': int(req_data.get('runMode') or req_data.get('run_mode') or 1),
            'status': AutomationService.STATUS_PENDING,
            'total_count': len(items),
            'pending_count': len(items),
            'running_count': 0,
            'passed_count': 0,
            'failed_count': 0,
            'blocked_count': 0,
            'skipped_count': 0,
            'not_found_count': 0,
            'trigger_by': user_id,
            'trigger_message': req_data.get('remark'),
            'callback_token': callback_token,
            'ext': {}
        })
        if err_msg:
            logger.error(f'创建执行记录失败: {err_msg}')
            return {}, err_msg
        
        logger.info(f'执行记录创建成功: execution_id={execution_obj.id}')
        
        batch_list = []
        for idx, (plan_case, case_item) in enumerate(items, start=1):
            batch_list.append({
                'execution_id': execution_obj.id,
                'plan_case_id': plan_case.id,
                'case_id': case_item.id,
                'case_key': case_item.case_key,
                'case_title': case_item.title,
                'run_order': idx,
                'status': AutomationService.CASE_STATUS_PENDING
            })
        
        logger.info(f'批量创建执行明细: {len(batch_list)} 条')
        _, err_msg = AutomationDao.batch_create_execution_cases(session, batch_list)
        if err_msg:
            logger.error(f'批量创建执行明细失败: {err_msg}')
            return {}, err_msg
        
        logger.info(f'触发Jenkins构建: execution_id={execution_obj.id}')
        trigger_ok, trigger_msg = AutomationService.trigger_jenkins(session, execution_obj.id, req_data.get('jenkinsJobName'))
        if not trigger_ok:
            logger.error(f'Jenkins触发失败: {trigger_msg}')
            return {}, trigger_msg
        
        logger.info('计划自动化执行成功')
        execution = AutomationDao.get_execution_by_id(session, execution_obj.id)
        logger.info(f'====== 计划自动化执行结束 ======')
        return execution.to_dict() if execution else {'id': execution_obj.id}, ''

    @staticmethod
    def trigger_jenkins(session, execution_id, job_name=None):
        
        
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return False, '未查询到对应执行记录'
        AutomationDao.update_execution_by_id(session, execution_id, {'status': AutomationService.STATUS_TRIGGERING})
        
        cases, _ = AutomationDao.list_execution_case_by_filters(session, [AutoExecutionCase.execution_id == int(execution_id)], 1, 100000)
        case_keys = [case.case_key for case in cases if case.case_key]
        test_target = ','.join(case_keys)
        
        test_type = 'story' if case_keys else 'all'
        
        params = {
            'EXECUTION_ID': execution.id,
            'CALLBACK_TOKEN': execution.callback_token,
            'PLATFORM_BASE_URL': PLATFORM_BASE_URL,
            'ENV_CODE': execution.env_code,
            'RUN_MODE': execution.run_mode,
            'TRIGGER_TYPE': execution.trigger_type,
            'TEST_TYPE': test_type,
            'TEST_TARGET': test_target
        }
        
        jenkins_url = None
        jenkins_job_name = None
        if execution.plan_id:
            plan = AutomationDao.get_plan_by_id(session, execution.plan_id)
            if plan and plan.jenkins_url:
                jenkins_url = plan.jenkins_url
                if '/job/' in jenkins_url:
                    import re
                    match = re.match(r'^(https?://[^/]+)/(job/[^/]+)/?.*$', jenkins_url)
                    if match:
                        jenkins_url = match.group(1)
                        jenkins_job_name = match.group(2).replace('job/', '')
                        logger.info(f'从计划配置中解析 Jenkins: base_url={jenkins_url}, job_name={jenkins_job_name}')
        
        jenkins_request = JenkinsRequest(jenkins_url=jenkins_url)
        target_job_name = jenkins_job_name or job_name or execution.jenkins_job_name or JENKINS_DEFAULT_JOB
        success, err_msg, payload = jenkins_request.build_with_parameters(params, target_job_name)
        if not success:
            AutomationDao.update_execution_by_id(session, execution_id, {
                'status': AutomationService.STATUS_TRIGGER_FAILED,
                'trigger_message': err_msg
            })
            return False, err_msg
        update_info = {
            'status': AutomationService.STATUS_QUEUED,
            'jenkins_job_name': payload.get('job_name') or job_name or JENKINS_DEFAULT_JOB,
            'jenkins_queue_id': payload.get('queue_id')
        }
        if payload.get('location'):
            update_info['trigger_message'] = payload.get('location')
        AutomationDao.update_execution_by_id(session, execution_id, update_info)
        return True, ''

    @staticmethod
    def get_running_execution_by_case(session, case_id, env_code):
        items, _ = AutomationDao.list_execution_by_filters(session, [
            AutoExecution.source_case_id == int(case_id),
            AutoExecution.env_code == env_code,
            AutoExecution.status.in_([0, 1, 2, 3])
        ], 1, 1)
        return items[0] if items else None

    @staticmethod
    def get_running_execution_by_plan(session, plan_id, env_code):
        items, _ = AutomationDao.list_execution_by_filters(session, [
            AutoExecution.plan_id == int(plan_id),
            AutoExecution.env_code == env_code,
            AutoExecution.status.in_([0, 1, 2, 3])
        ], 1, 1)
        return items[0] if items else None

    @staticmethod
    def list_executions(session, req_data):
        filters = []
        project_id = req_data.get('projectId') or req_data.get('project_id')
        plan_id = req_data.get('planId') or req_data.get('plan_id')
        status = req_data.get('status')
        trigger_type = req_data.get('triggerType') or req_data.get('trigger_type')
        if project_id:
            filters.append(AutoExecution.project_id == int(project_id))
        if plan_id:
            filters.append(AutoExecution.plan_id == int(plan_id))
        if status not in (None, ''):
            filters.append(AutoExecution.status == int(status))
        if trigger_type not in (None, ''):
            filters.append(AutoExecution.trigger_type == int(trigger_type))
        items, total = AutomationDao.list_execution_by_filters(session, filters, req_data.get('pageNo') or req_data.get('page') or 1, req_data.get('pageSize') or req_data.get('size') or 20)
        return {'list': [item.to_dict() for item in items], 'total': total}

    @staticmethod
    def get_execution_detail(session, execution_id):
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return {}, '未查询到对应执行记录'
        ret = execution.to_dict()
        summary = AutomationDao.count_execution_case_summary(session, execution_id)
        ret.update({
            'summary': {
                'total': summary.get('total', 0),
                'pending': summary.get(0, 0),
                'running': summary.get(1, 0),
                'passed': summary.get(2, 0),
                'failed': summary.get(3, 0),
                'blocked': summary.get(4, 0),
                'skipped': summary.get(5, 0),
                'notFound': summary.get(6, 0),
                'canceled': summary.get(7, 0)
            }
        })
        return ret, ''

    @staticmethod
    def list_execution_cases(session, req_data):
        execution_id = req_data.get('executionId') or req_data.get('execution_id')
        if not execution_id:
            return {}, 'executionId 为必传参数'
        filters = [AutoExecutionCase.execution_id == int(execution_id)]
        status = req_data.get('status')
        if status not in (None, ''):
            filters.append(AutoExecutionCase.status == int(status))
        items, total = AutomationDao.list_execution_case_by_filters(session, filters, req_data.get('pageNo') or req_data.get('page') or 1, req_data.get('pageSize') or req_data.get('size') or 20)
        return {'list': [item.to_dict() for item in items], 'total': total}, ''

    @staticmethod
    def pull_execution_cases(session, execution_id, callback_token):
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return {}, '未查询到对应执行记录'
        if execution.callback_token != callback_token:
            return {}, '回调鉴权失败'
        case_items, _ = AutomationDao.list_execution_case_by_filters(session, [AutoExecutionCase.execution_id == int(execution_id)], 1, 100000)
        return {
            'executionId': execution.id,
            'executionNo': execution.execution_no,
            'triggerType': execution.trigger_type,
            'projectId': execution.project_id,
            'planId': execution.plan_id,
            'envCode': execution.env_code,
            'runMode': execution.run_mode,
            'items': [{
                'executionCaseId': item.id,
                'planCaseId': item.plan_case_id,
                'caseId': item.case_id,
                'caseKey': item.case_key,
                'caseTitle': item.case_title,
                'runOrder': item.run_order
            } for item in case_items]
        }, ''

    @staticmethod
    def mark_execution_queued(session, req_data):
        execution_id = req_data.get('executionId') or req_data.get('execution_id')
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return 0, '未查询到对应执行记录'
        return AutomationDao.update_execution_by_id(session, execution_id, {
            'status': AutomationService.STATUS_QUEUED,
            'jenkins_queue_id': req_data.get('queueId') or req_data.get('queue_id'),
            'jenkins_job_name': req_data.get('jobName') or req_data.get('job_name') or execution.jenkins_job_name,
            'jenkins_build_number': req_data.get('buildNumber') or req_data.get('build_number'),
            'jenkins_build_url': req_data.get('buildUrl') or req_data.get('build_url')
        })

    @staticmethod
    def mark_execution_started(session, req_data):
        execution_id = req_data.get('executionId') or req_data.get('execution_id')
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return 0, '未查询到对应执行记录'
        start_time = req_data.get('startTime') or req_data.get('start_time') or datetime.now()
        return AutomationDao.update_execution_by_id(session, execution_id, {
            'status': AutomationService.STATUS_RUNNING,
            'jenkins_job_name': req_data.get('jobName') or req_data.get('job_name') or execution.jenkins_job_name,
            'jenkins_build_number': req_data.get('buildNumber') or req_data.get('build_number'),
            'jenkins_build_url': req_data.get('buildUrl') or req_data.get('build_url'),
            'console_url': req_data.get('consoleUrl') or req_data.get('console_url'),
            'start_time': start_time
        })

    @staticmethod
    def save_case_result(session, req_data):
        execution_id = req_data.get('executionId') or req_data.get('execution_id')
        execution_case_id = req_data.get('executionCaseId') or req_data.get('execution_case_id')
        case_id = req_data.get('caseId') or req_data.get('case_id')
        if not execution_id or (not execution_case_id and not case_id):
            return 0, 'executionId、executionCaseId/caseId 为必传参数'
        execution_case = AutomationDao.get_execution_case_by_id(session, execution_case_id) if execution_case_id else None
        if not execution_case and case_id:
            execution_case = AutomationDao.get_execution_case_by_unique(session, execution_id, case_id, req_data.get('planCaseId') or req_data.get('plan_case_id'))
        if not execution_case:
            return 0, '未查询到对应执行明细'
        update_info = {
            'status': int(req_data.get('status')) if req_data.get('status') is not None else execution_case.status,
            'pytest_nodeid': req_data.get('pytestNodeid') or req_data.get('pytest_nodeid'),
            'result_message': req_data.get('resultMessage') or req_data.get('result_message'),
            'error_message': req_data.get('errorMessage') or req_data.get('error_message'),
            'stack_trace': req_data.get('stackTrace') or req_data.get('stack_trace'),
            'report_url': req_data.get('reportUrl') or req_data.get('report_url'),
            'duration_seconds': req_data.get('durationSeconds') or req_data.get('duration_seconds'),
            'started_time': req_data.get('startedTime') or req_data.get('started_time') or execution_case.started_time,
            'finished_time': req_data.get('finishedTime') or req_data.get('finished_time') or datetime.now(),
            'ext': req_data.get('ext') if req_data.get('ext') is not None else execution_case.ext
        }
        update_id, err_msg = AutomationDao.update_execution_case_by_id(session, execution_case.id, update_info)
        if err_msg:
            return update_id, err_msg
        execution_case = AutomationDao.get_execution_case_by_id(session, execution_case.id)
        try:
            from app.api.service.failureAttributionService import FailureAttributionService
            FailureAttributionService.classify_and_store_auto_case(session, execution_case)
        except Exception:
            pass
        if execution_case and execution_case.plan_case_id:
            AutomationService.sync_plan_case_result(session, execution_case)
        AutomationService.refresh_execution_summary(session, execution_id)
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if execution and execution.plan_id:
            AutomationService.refresh_plan_status(session, execution.plan_id)
        return execution_case.id, ''

    @staticmethod
    def finish_execution(session, req_data):
        execution_id = req_data.get('executionId') or req_data.get('execution_id')
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return 0, '未查询到对应执行记录'
        end_time = req_data.get('endTime') or req_data.get('end_time') or datetime.now()
        start_time = req_data.get('startTime') or req_data.get('start_time') or execution.start_time
        update_info = {
            'jenkins_build_number': req_data.get('buildNumber') or req_data.get('build_number') or execution.jenkins_build_number,
            'jenkins_build_url': req_data.get('buildUrl') or req_data.get('build_url') or execution.jenkins_build_url,
            'console_url': req_data.get('consoleUrl') or req_data.get('console_url') or execution.console_url,
            'report_url': req_data.get('reportUrl') or req_data.get('report_url') or execution.report_url,
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': req_data.get('durationSeconds') or req_data.get('duration_seconds') or AutomationService.calc_duration_seconds(start_time, end_time)
        }
        update_id, err_msg = AutomationDao.update_execution_by_id(session, execution_id, update_info)
        if err_msg:
            return update_id, err_msg
        AutomationService.refresh_execution_summary(session, execution_id, force_finish=True)
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if execution and execution.plan_id:
            AutomationService.refresh_plan_status(session, execution.plan_id)
        return int(execution_id), ''

    @staticmethod
    def abort_execution(session, req_data):
        execution_id = req_data.get('executionId') or req_data.get('execution_id')
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return 0, '未查询到对应执行记录'
        case_items, _ = AutomationDao.list_execution_case_by_filters(session, [AutoExecutionCase.execution_id == int(execution_id), AutoExecutionCase.status.in_([0, 1])], 1, 100000)
        for item in case_items:
            AutomationDao.update_execution_case_by_id(session, item.id, {'status': AutomationService.CASE_STATUS_CANCELED, 'finished_time': datetime.now()})
        update_id, err_msg = AutomationDao.update_execution_by_id(session, execution_id, {
            'status': int(req_data.get('status') or AutomationService.STATUS_CANCELED),
            'trigger_message': req_data.get('message') or req_data.get('trigger_message'),
            'jenkins_build_number': req_data.get('buildNumber') or req_data.get('build_number') or execution.jenkins_build_number,
            'console_url': req_data.get('consoleUrl') or req_data.get('console_url') or execution.console_url,
            'end_time': datetime.now()
        })
        if err_msg:
            return update_id, err_msg
        AutomationService.refresh_execution_summary(session, execution_id, keep_terminal_status=True)
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if execution and execution.plan_id:
            AutomationService.refresh_plan_status(session, execution.plan_id)
        return int(execution_id), ''

    @staticmethod
    def sync_plan_case_result(session, execution_case):
        status = AutomationService.PLAN_CASE_STATUS_MAP.get(execution_case.status)
        update_info = {
            'actual_result': execution_case.error_message or execution_case.result_message,
            'executed_time': execution_case.finished_time or datetime.now(),
            'execution_duration': execution_case.duration_seconds
        }
        if status is not None:
            update_info['status'] = status
        AutomationDao.update_plan_case_result(session, execution_case.plan_case_id, update_info)

    @staticmethod
    def refresh_execution_summary(session, execution_id, force_finish=False, keep_terminal_status=False):
        summary = AutomationDao.count_execution_case_summary(session, execution_id)
        execution = AutomationDao.get_execution_by_id(session, execution_id)
        if not execution:
            return
        update_info = {
            'total_count': summary.get('total', 0),
            'pending_count': summary.get(0, 0),
            'running_count': summary.get(1, 0),
            'passed_count': summary.get(2, 0),
            'failed_count': summary.get(3, 0),
            'blocked_count': summary.get(4, 0),
            'skipped_count': summary.get(5, 0),
            'not_found_count': summary.get(6, 0)
        }
        total = summary.get('total', 0)
        running_count = summary.get(1, 0)
        finished_count = summary.get(2, 0) + summary.get(3, 0) + summary.get(4, 0) + summary.get(5, 0) + summary.get(6, 0) + summary.get(7, 0)
        if not keep_terminal_status:
            if running_count > 0:
                update_info['status'] = AutomationService.STATUS_RUNNING
            elif total > 0 and finished_count == total:
                if summary.get(3, 0) + summary.get(4, 0) + summary.get(6, 0) > 0:
                    update_info['status'] = AutomationService.STATUS_FAILED
                else:
                    update_info['status'] = AutomationService.STATUS_SUCCESS
        if force_finish or (total > 0 and finished_count == total):
            end_time = execution.end_time or datetime.now()
            update_info['end_time'] = end_time
            if execution.start_time:
                update_info['duration_seconds'] = AutomationService.calc_duration_seconds(execution.start_time, end_time)
        AutomationDao.update_execution_by_id(session, execution_id, update_info)

    @staticmethod
    def refresh_plan_status(session, plan_id):
        PlanService.refresh_plan_status(session, plan_id)

    @staticmethod
    def calc_duration_seconds(start_time, end_time):
        if not start_time or not end_time:
            return None
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        return int((end_time - start_time).total_seconds())
