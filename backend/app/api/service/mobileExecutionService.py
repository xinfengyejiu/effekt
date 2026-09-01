# encoding: UTF-8
import json
import logging
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from app.core.config import (
    MOBILE_AUTOMATION_APPIUM_URL,
    MOBILE_AUTOMATION_PYTHON,
    MOBILE_AUTOMATION_ROOT,
    MOBILE_AUTOMATION_TIMEOUT_SECONDS,
)
from app.core.database import get_db_context
from app.api.dao.mobileAutomationDao import MobileAutomationDao
from app.api.model.automationModel import AutoExecutionCase
from app.api.model.caseModel import TestCase
from app.api.model.mobileAutomationModel import MobileExecutionStep
from app.api.model.projectModel import Project
from app.api.service.mobileArtifactService import MobileArtifactService
from app.api.service.mobileAIVerifyService import MobileAIVerifyService
from app.api.service.mobilePageParserService import MobilePageParserService

logger = logging.getLogger(__name__)


class MobileExecutionService(object):
    STATUS_PENDING = 0
    STATUS_RUNNING = 3
    STATUS_SUCCESS = 4
    STATUS_FAILED = 5
    STATUS_CANCELED = 6
    STATUS_TRIGGER_FAILED = 7
    _processes = {}
    _lock = threading.Lock()
    _selector_pattern = re.compile(r'^[\w\u4e00-\u9fa5./:-]+$')

    @staticmethod
    def _execution_no():
        return 'MA' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]

    @staticmethod
    def _safe_selector(selector):
        value = str(selector or '').strip()
        logger.info('_safe_selector called with: %r', value)
        if not value or not MobileExecutionService._selector_pattern.fullmatch(value):
            logger.error('_safe_selector failed: value=%r, pattern=%s', value, MobileExecutionService._selector_pattern.pattern)
            raise ValueError('script_selector 格式非法')
        if '..' in value or value.startswith('/') or value.startswith('\\'):
            raise ValueError('script_selector 必须位于脚本仓库内')
        # 拒绝绝对路径（如 D:\xxx 或 C:/xxx）
        if len(value) >= 2 and value[1] == ':' and value[0].isalpha():
            raise ValueError('script_selector 必须为相对路径，不能是绝对路径')
        root = Path(MOBILE_AUTOMATION_ROOT).resolve()
        target_path = (root / value.split('::', 1)[0]).resolve()
        if root not in target_path.parents and target_path != root:
            raise ValueError('script_selector 超出脚本仓库范围')
        return value

    @staticmethod
    def _split_selectors(raw):
        if isinstance(raw, (list, tuple)):
            parts = [str(item or '').strip() for item in raw]
        else:
            parts = [item.strip() for item in re.split(r'[;\n]+', str(raw or ''))]
        return [item for item in parts if item]

    @staticmethod
    def _guess_selector_for_case(case_item, fallback):
        text = '{0} {1}'.format(getattr(case_item, 'case_key', '') or '', getattr(case_item, 'title', '') or '')
        lower = text.lower()
        if any(token in text for token in ('日语', '日本語', '语言')) or 'japanese' in lower or 'language' in lower:
            return 'tests/test_joyhub_login.py::test_change_language_to_japanese'
        if any(token in text for token in ('登录', '登陆', 'Login', 'login')):
            return 'tests/test_joyhub_login.py::test_login_success'
        return fallback

    @staticmethod
    def _resolve_case_selectors(script_selector, case_items, script_selectors=None):
        """按用例顺序解析脚本：优先 script_selectors；否则拆分 script_selector；不足时按用例标题猜测。"""
        explicit = MobileExecutionService._split_selectors(script_selectors if script_selectors is not None else [])
        joined = MobileExecutionService._split_selectors(script_selector)
        base = explicit or joined
        if not base:
            raise ValueError('script_selector 为必传参数')
        fallback = MobileExecutionService._safe_selector(base[0])
        resolved = []
        for index, case_item in enumerate(case_items):
            if index < len(base):
                resolved.append(MobileExecutionService._safe_selector(base[index]))
            elif len(base) == 1:
                # 多用例共用一个选择器时，尽量按标题映射到不同脚本，避免第二条假通过
                guessed = MobileExecutionService._guess_selector_for_case(case_item, fallback)
                resolved.append(MobileExecutionService._safe_selector(guessed))
            else:
                resolved.append(fallback)
        return resolved

    @staticmethod
    def list_configs(session, req_data):
        items, total = MobileAutomationDao.list_configs(session, req_data.get('project_id'), req_data.get('page_no', 1), req_data.get('page_size', 20))
        result = []
        for item in items:
            data = item.to_dict()
            data['case_ids'] = [case.case_id for case in MobileAutomationDao.list_config_cases(session, item.id)]
            result.append(data)
        return {'list': result, 'total': total}

    @staticmethod
    def get_config(session, config_id):
        item = MobileAutomationDao.get_config(session, config_id)
        if not item:
            return {}, '移动执行配置不存在'
        data = item.to_dict()
        data['case_ids'] = [case.case_id for case in MobileAutomationDao.list_config_cases(session, item.id)]
        data['script_selectors'] = MobileExecutionService._split_selectors(data.get('script_selector'))
        return data, ''

    @staticmethod
    def save_config(session, req_data, user_id):
        required = ('name', 'project_id', 'mobile_app_id', 'device_serial', 'env_code', 'case_ids', 'script_selector')
        missing = [key for key in required if req_data.get(key) in (None, '', [])]
        if missing:
            return {}, '{0} 为必传参数'.format('、'.join(missing))
        app = MobileAutomationDao.get_app(session, req_data['mobile_app_id'])
        if not app or app.enabled != 1 or int(app.project_id) != int(req_data['project_id']):
            return {}, '应用配置不存在、已禁用或与项目不匹配'
        case_ids = [int(item) for item in req_data['case_ids']]
        cases = session.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_delete == 0).all()
        if len(cases) != len(set(case_ids)):
            return {}, '存在无效或已删除的测试用例'
        case_map = {int(item.id): item for item in cases}
        ordered_cases = [case_map[case_id] for case_id in case_ids]
        try:
            selectors = MobileExecutionService._resolve_case_selectors(
                req_data.get('script_selector'), ordered_cases, req_data.get('script_selectors')
            )
        except ValueError as exc:
            return {}, str(exc)
        config = MobileAutomationDao.get_config(session, req_data.get('id')) if req_data.get('id') else None
        if config is None:
            from app.api.model.mobileAutomationModel import MobileExecutionConfig
            config = MobileExecutionConfig(created_by=user_id)
            session.add(config)
        for key in ('name', 'project_id', 'mobile_app_id', 'device_serial', 'env_code', 'remark'):
            setattr(config, key, req_data.get(key))
        config.script_selector = ';'.join(selectors)
        config.project_id = int(req_data['project_id'])
        config.mobile_app_id = int(req_data['mobile_app_id'])
        config.enabled = 1
        # 必须先写完必填字段再 flush，否则 name 等 NOT NULL 列会直接落库失败
        session.flush()
        from app.api.model.mobileAutomationModel import MobileExecutionConfigCase
        session.query(MobileExecutionConfigCase).filter_by(config_id=config.id).delete(synchronize_session=False)
        for order, case_id in enumerate(case_ids, start=1):
            session.add(MobileExecutionConfigCase(config_id=config.id, case_id=case_id, run_order=order))
        session.commit()
        data, _ = MobileExecutionService.get_config(session, config.id)
        return data, ''

    @staticmethod
    def delete_config(session, config_id):
        config = MobileAutomationDao.get_config(session, config_id)
        if not config:
            return 0, '移动执行配置不存在'
        config.enabled = 0
        session.commit()
        return config.id, ''

    @staticmethod
    def run_config(session, config_id, user_id):
        config, error = MobileExecutionService.get_config(session, config_id)
        if error:
            return {}, error
        config['remark'] = config.get('remark') or config.get('name')
        return MobileExecutionService.create_execution(session, config, user_id)

    @staticmethod
    def create_execution(session, req_data, user_id):
        required = ('project_id', 'mobile_app_id', 'device_serial', 'case_ids', 'script_selector', 'env_code')
        missing = [key for key in required if req_data.get(key) in (None, '', [])]
        if missing:
            return {}, '{0} 为必传参数'.format('、'.join(missing))
        if int(req_data.get('run_mode', 1)) != 1:
            return {}, '首期仅支持串行执行'
        root = Path(MOBILE_AUTOMATION_ROOT)
        if not root.is_dir():
            return {}, '移动脚本仓库不存在，请先完成环境配置'
        if not Path(MOBILE_AUTOMATION_PYTHON).is_file():
            return {}, '移动自动化 Python 解释器不存在'
        app = MobileAutomationDao.get_app(session, req_data['mobile_app_id'])
        if not app or app.enabled != 1:
            return {}, '应用配置不存在或已禁用'
        if int(app.project_id) != int(req_data['project_id']):
            return {}, '应用配置与项目不匹配'
        case_ids = [int(item) for item in req_data['case_ids']]
        case_items = session.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_delete == 0).all()
        if len(case_items) != len(set(case_ids)):
            return {}, '存在无效或已删除的测试用例'
        case_map = {int(item.id): item for item in case_items}
        ordered_cases = [case_map[case_id] for case_id in case_ids]
        try:
            selectors = MobileExecutionService._resolve_case_selectors(
                req_data.get('script_selector'), ordered_cases, req_data.get('script_selectors')
            )
        except ValueError as exc:
            return {}, str(exc)
        device, err_msg = MobileAutomationDao.lock_device(session, req_data['device_serial'])
        if err_msg:
            session.rollback()
            return {}, err_msg
        execution_no = MobileExecutionService._execution_no()
        # 查询项目名，用于按项目归类产物目录
        project = session.query(Project).filter(
            Project.id == int(req_data['project_id']), Project.is_delete == 0
        ).first()
        project_name = project.name if project else None
        artifact_root = MobileArtifactService.execution_root(execution_no, project_name)
        ext = {
            'execution_engine': 'mobile_local',
            'device_serial': device.serial_no,
            'mobile_app_id': app.id,
            'app_package': app.package_name,
            'launch_activity': app.launch_activity,
            'script_selector': selectors[0],
            'script_selectors': selectors,
            'appium_url': MOBILE_AUTOMATION_APPIUM_URL,
            'artifact_root': MobileArtifactService.safe_relative_path(artifact_root),
            'project_name': project_name,
        }
        try:
            execution = MobileAutomationDao.create_execution(session, {
                'execution_no': execution_no,
                'trigger_type': 1,
                'project_id': int(req_data['project_id']),
                'source_case_id': ordered_cases[0].id if len(ordered_cases) == 1 else None,
                'env_code': req_data['env_code'],
                'run_mode': 1,
                'status': MobileExecutionService.STATUS_PENDING,
                'total_count': len(ordered_cases),
                'pending_count': len(ordered_cases),
                'trigger_by': user_id,
                'trigger_source': 'mobile_platform',
                'trigger_message': req_data.get('remark'),
                'ext': ext,
            }, ordered_cases)
            session.commit()
        except Exception:
            session.rollback()
            raise
        thread = threading.Thread(target=MobileExecutionService._run_execution, args=(execution.id,), daemon=True)
        thread.start()
        return execution.to_dict(), ''

    @staticmethod
    def retry_execution(session, execution_id, user_id):
        execution = MobileAutomationDao.get_execution(session, execution_id)
        if not execution or execution.trigger_source != 'mobile_platform':
            return {}, '移动执行记录不存在'
        if execution.status not in (MobileExecutionService.STATUS_SUCCESS, MobileExecutionService.STATUS_FAILED,
                                    MobileExecutionService.STATUS_CANCELED, MobileExecutionService.STATUS_TRIGGER_FAILED):
            return {}, '仅已结束的移动执行支持重新执行'
        ext = execution.ext or {}
        case_items = MobileAutomationDao.list_execution_cases(session, execution.id)
        if not case_items:
            return {}, '原执行未关联测试用例，无法重新执行'
        request_data = {
            'project_id': execution.project_id,
            'mobile_app_id': ext.get('mobile_app_id'),
            'device_serial': ext.get('device_serial'),
            'case_ids': [item.case_id for item in case_items],
            'script_selector': ';'.join(MobileExecutionService._split_selectors(
                ext.get('script_selectors') or ext.get('script_selector')
            )),
            'script_selectors': MobileExecutionService._split_selectors(
                ext.get('script_selectors') or ext.get('script_selector')
            ),
            'env_code': execution.env_code,
            'run_mode': execution.run_mode,
            'remark': execution.trigger_message,
        }
        return MobileExecutionService.create_execution(session, request_data, user_id)

    @staticmethod
    def execution_progress(session, execution_id):
        execution = MobileAutomationDao.get_execution(session, execution_id)
        if not execution or execution.trigger_source != 'mobile_platform':
            return {}, '移动执行记录不存在'
        cases = MobileAutomationDao.list_execution_cases(session, execution.id)
        steps = MobileAutomationDao.list_steps(session, execution.id)
        artifacts = MobileAutomationDao.list_artifacts(session, execution.id)
        ext = execution.ext or {}
        log_path = MobileArtifactService.execution_root(
            execution.execution_no, ext.get('project_name')
        ) / 'console.log'
        console_tail = ''
        if log_path.is_file():
            console_tail = MobileArtifactService.read_text_auto(log_path, max_chars=20000)
        latest_screenshot = next((item for item in reversed(artifacts) if item.artifact_type == 'screenshot'), None)
        report_artifact = next((item for item in reversed(artifacts) if item.artifact_type == 'html_report'), None)
        completed = sum(1 for item in cases if item.status in (2, 3, 4, 5, 6, 7))
        return {
            'execution': execution.to_dict(),
            'cases': [item.to_dict() for item in cases],
            'steps': [item.to_dict() for item in steps],
            'metrics': {'total': len(cases), 'completed': completed, 'passed': execution.passed_count or 0, 'failed': execution.failed_count or 0},
            'latest_screenshot_artifact_id': latest_screenshot.id if latest_screenshot else None,
            'html_report_artifact_id': report_artifact.id if report_artifact else None,
            'console_tail': console_tail,
        }, ''

    @staticmethod
    def _capture_step_snapshot(session, execution, serial_no, execution_case_id, step, is_after=False, capture_label=None):
        try:
            captured = MobilePageParserService.capture(
                session, execution.id, execution.execution_no, serial_no, execution_case_id,
                capture_label or ('after' if is_after else 'before')
            )
            step.page_snapshot = captured.get('snapshot') or {}
            if is_after:
                step.after_screenshot_artifact_id = captured.get('screenshot_artifact_id')
            else:
                step.before_screenshot_artifact_id = captured.get('screenshot_artifact_id')
            step.ui_xml_artifact_id = captured.get('xml_artifact_id')
        except Exception as exc:
            step.error_message = '{0}\n页面采集失败：{1}'.format(step.error_message or '', str(exc)[:300]).strip()

    @staticmethod
    def _max_step_no(session, execution_id):
        steps = MobileAutomationDao.list_steps(session, execution_id)
        return max((int(item.step_no or 0) for item in steps), default=0)

    @staticmethod
    def _ai_verify_case(session, execution_case, page_snapshot=None, exit_code=None, error_message=None):
        """对单个用例执行结果进行 AI 验证，结果写入用例 ext 字段。"""
        try:
            from app.api.model.mobileAutomationModel import MobileExecutionConfig
            from app.api.model.caseModel import TestCase

            # 查找关联的测试用例以获取步骤信息
            case_item = session.query(TestCase).filter(
                TestCase.id == execution_case.case_id, TestCase.is_delete == 0
            ).first()
            case_title = execution_case.case_title or (case_item.title if case_item else '')
            case_steps = []
            if case_item and case_item.steps:
                steps_data = case_item.steps
                if isinstance(steps_data, str):
                    try:
                        steps_data = json.loads(steps_data)
                    except Exception:
                        steps_data = [{'content': steps_data}]
                if isinstance(steps_data, list):
                    case_steps = steps_data

            verify_result = MobileAIVerifyService.verify(
                case_title=case_title,
                case_steps=case_steps,
                page_snapshot=page_snapshot or {},
                exit_code=exit_code or 0,
                error_message=error_message,
            )

            # 写入用例 ext 字段
            ext = execution_case.ext or {}
            ext['ai_verify'] = verify_result
            execution_case.ext = ext
            logger.info(
                'AI验证用例[%s]结果: verdict=%s, confidence=%d, reason=%s',
                execution_case.case_title, verify_result.get('verdict'),
                verify_result.get('confidence', 0), verify_result.get('reason', '')[:100]
            )
        except Exception as exc:
            logger.exception('AI验证用例异常: %s', exc)

    @staticmethod
    def _run_execution(execution_id):
        with get_db_context() as session:
            execution = MobileAutomationDao.get_execution(session, execution_id)
            if not execution:
                return
            ext = execution.ext or {}
            serial_no = ext.get('device_serial')
            execution_root = MobileArtifactService.execution_root(
                execution.execution_no, ext.get('project_name')
            )
            log_path = execution_root / 'console.log'
            allure_dir = execution_root / 'allure-results'
            allure_dir.mkdir(parents=True, exist_ok=True)
            execution_cases = MobileAutomationDao.list_execution_cases(session, execution.id)
            selectors = MobileExecutionService._split_selectors(ext.get('script_selectors') or ext.get('script_selector'))
            if not selectors:
                MobileExecutionService._finish_exception(execution.id, '缺少 script_selector')
                return
            if len(selectors) < len(execution_cases):
                selectors = selectors + [selectors[-1]] * (len(execution_cases) - len(selectors))
            MobileAutomationDao.set_execution_status(
                session, execution.id, MobileExecutionService.STATUS_RUNNING, start_time=datetime.now()
            )
            session.commit()

            any_failed = False
            try:
                with log_path.open('ab') as log_file:
                    for index, execution_case in enumerate(execution_cases):
                        selector = selectors[index]
                        case_label = execution_case.case_title or execution_case.case_key or str(execution_case.case_id)
                        steps_rel = 'runtime_steps_case_{0}.jsonl'.format(execution_case.id)
                        steps_file = execution_root / steps_rel
                        if steps_file.exists():
                            steps_file.unlink()
                        with get_db_context() as case_session:
                            live_case = case_session.query(AutoExecutionCase).filter(
                                AutoExecutionCase.id == execution_case.id
                            ).first()
                            if live_case:
                                live_case.status = 1
                                live_case.result_message = '执行中：{0}'.format(selector)
                            step_base = MobileExecutionService._max_step_no(case_session, execution.id)
                            runtime_step = MobileAutomationDao.create_step(case_session, {
                                'execution_id': execution.id,
                                'execution_case_id': execution_case.id,
                                'step_no': step_base + 1,
                                'instruction': '[{0}] 启动并执行 pytest：{1}'.format(case_label, selector),
                                'action_type': 'pytest',
                                'action_payload': {
                                    'script_selector': selector,
                                    'case_id': execution_case.case_id,
                                    'execution_case_id': execution_case.id,
                                },
                                'status': 'running',
                            })
                            live_execution = MobileAutomationDao.get_execution(case_session, execution.id)
                            MobileExecutionService._capture_step_snapshot(
                                case_session, live_execution, serial_no, execution_case.id, runtime_step
                            )
                            case_session.commit()
                            runtime_step_id = runtime_step.id
                            step_offset = step_base

                        command = [
                            MOBILE_AUTOMATION_PYTHON, '-m', 'pytest', selector,
                            '--alluredir', str(allure_dir),
                        ]
                        env = os.environ.copy()
                        env.update({
                            'MOBILE_DEVICE_SERIAL': serial_no,
                            'MOBILE_APP_PACKAGE': ext.get('app_package', ''),
                            'MOBILE_EXECUTION_ID': str(execution.id),
                            'MOBILE_EXECUTION_CASE_ID': str(execution_case.id),
                            'MOBILE_ARTIFACT_DIR': str(execution_root),
                            'MOBILE_RUNTIME_STEPS_FILE': steps_rel,
                            'MOBILE_APPIUM_URL': ext.get('appium_url', MOBILE_AUTOMATION_APPIUM_URL),
                            # Windows 默认控制台是 GBK，强制 UTF-8 避免中文日志乱码
                            'PYTHONIOENCODING': 'utf-8',
                            'PYTHONUTF8': '1',
                        })
                        log_file.write(('\n===== CASE {0}/{1}: {2} =====\n'.format(
                            index + 1, len(execution_cases), case_label
                        )).encode('utf-8'))
                        log_file.flush()
                        process = subprocess.Popen(
                            command, cwd=MOBILE_AUTOMATION_ROOT,
                            stdout=log_file, stderr=subprocess.STDOUT, env=env
                        )
                        with MobileExecutionService._lock:
                            MobileExecutionService._processes[execution.id] = process
                        deadline = time.monotonic() + MOBILE_AUTOMATION_TIMEOUT_SECONDS
                        last_capture = 0
                        synced_runtime_steps = 0
                        while process.poll() is None:
                            now = time.monotonic()
                            if now >= deadline:
                                MobileExecutionService._terminate_process(execution.id)
                                MobileExecutionService._finish_exception(execution.id, '执行超时')
                                return
                            with get_db_context() as live_session:
                                synced_runtime_steps = MobileExecutionService._sync_runtime_steps(
                                    live_session, execution.id, execution_case.id, execution_root,
                                    synced_runtime_steps, step_offset=step_offset, steps_file_name=steps_rel
                                )
                                live_session.commit()
                            if now - last_capture >= 3:
                                with get_db_context() as live_session:
                                    live_execution = MobileAutomationDao.get_execution(live_session, execution.id)
                                    live_step = live_session.query(MobileExecutionStep).filter(
                                        MobileExecutionStep.id == runtime_step_id
                                    ).first()
                                    if live_execution and live_step:
                                        live_step.duration_ms = int(
                                            (datetime.now() - live_execution.start_time).total_seconds() * 1000
                                        ) if live_execution.start_time else None
                                        MobileExecutionService._capture_step_snapshot(
                                            live_session, live_execution, serial_no, live_step.execution_case_id,
                                            live_step, capture_label='live_{0}'.format(int(time.time() * 1000))
                                        )
                                        live_session.commit()
                                last_capture = now
                            time.sleep(0.5)
                        exit_code = process.returncode
                        with get_db_context() as result_session:
                            result = MobileAutomationDao.get_execution(result_session, execution.id)
                            live_case = result_session.query(AutoExecutionCase).filter(
                                AutoExecutionCase.id == execution_case.id
                            ).first()
                            synced_runtime_steps = MobileExecutionService._sync_runtime_steps(
                                result_session, execution.id, execution_case.id, execution_root,
                                synced_runtime_steps, step_offset=step_offset, steps_file_name=steps_rel
                            )
                            runtime_step_result = result_session.query(MobileExecutionStep).filter(
                                MobileExecutionStep.id == runtime_step_id
                            ).first()
                            failed_step_msg = ''
                            if exit_code != 0:
                                any_failed = True
                                failed_steps = [
                                    item for item in MobileAutomationDao.list_steps(
                                        result_session, execution.id, execution_case.id
                                    )
                                    if item.status == 'failed' and item.error_message
                                ]
                                if failed_steps:
                                    failed_step_msg = '步骤{0}失败：{1}'.format(
                                        failed_steps[-1].step_no, failed_steps[-1].error_message
                                    )
                            if runtime_step_result:
                                runtime_step_result.status = 'success' if exit_code == 0 else 'failed'
                                runtime_step_result.duration_ms = int(
                                    (datetime.now() - result.start_time).total_seconds() * 1000
                                ) if result and result.start_time else None
                                runtime_step_result.error_message = (
                                    '' if exit_code == 0 else (failed_step_msg or 'pytest exit_code={0}'.format(exit_code))
                                )
                                MobileExecutionService._capture_step_snapshot(
                                    result_session, result, serial_no, execution_case.id, runtime_step_result, True
                                )
                                # AI 验证：在执行后快照采集完成后，调用 AI 验证
                                MobileExecutionService._ai_verify_case(
                                    result_session, execution_case, page_snapshot=runtime_step_result.page_snapshot,
                                    exit_code=exit_code, error_message=runtime_step_result.error_message or None
                                )
                            if live_case:
                                # 优先使用 AI 验证结果，AI 不可用时回退到 pytest 退出码
                                ai_result = (live_case.ext or {}).get('ai_verify')
                                if ai_result and isinstance(ai_result, dict):
                                    live_case.status = MobileAIVerifyService.decide_case_status(
                                        ai_result.get('verdict', ''), exit_code
                                    )
                                    ai_reason = ai_result.get('reason', '')
                                    ai_verdict = ai_result.get('verdict', '')
                                    if exit_code == 0 and ai_verdict == 'fail':
                                        live_case.result_message = 'AI验证判定失败：{0}'.format(ai_reason[:200])
                                    elif exit_code != 0 and ai_verdict == 'pass':
                                        live_case.result_message = 'pytest异常但AI验证判定通过：{0}'.format(ai_reason[:200])
                                    else:
                                        live_case.result_message = (
                                            'pytest exit_code=0' if exit_code == 0
                                            else (failed_step_msg or 'pytest exit_code={0}'.format(exit_code))
                                        )
                                else:
                                    live_case.status = 2 if exit_code == 0 else 3
                                    live_case.result_message = (
                                        'pytest exit_code=0' if exit_code == 0
                                        else (failed_step_msg or 'pytest exit_code={0}'.format(exit_code))
                                    )
                                if exit_code != 0 and not ai_result:
                                    live_case.error_message = failed_step_msg or 'pytest exit_code={0}'.format(exit_code)
                                live_case.finished_time = datetime.now()
                            result_session.commit()
                        if exit_code != 0:
                            # 串行：一条失败后继续跑后续用例，最终汇总
                            continue

                with get_db_context() as result_session:
                    result = MobileAutomationDao.get_execution(result_session, execution.id)
                    if not result:
                        return
                    result_cases = MobileAutomationDao.list_execution_cases(result_session, execution.id)
                    passed = sum(1 for item in result_cases if item.status == 2)
                    failed = sum(1 for item in result_cases if item.status == 3)
                    result.status = (
                        MobileExecutionService.STATUS_SUCCESS if failed == 0 and passed == len(result_cases)
                        else MobileExecutionService.STATUS_FAILED
                    )
                    result.pending_count = 0
                    result.running_count = 0
                    result.passed_count = passed
                    result.failed_count = failed
                    result.end_time = datetime.now()
                    result.duration_seconds = int(
                        (result.end_time - result.start_time).total_seconds()
                    ) if result.start_time else None
                    if any_failed:
                        first_failed = next((item for item in result_cases if item.status == 3), None)
                        if first_failed and first_failed.error_message:
                            result.trigger_message = first_failed.error_message
                    MobileArtifactService.register_file(result_session, result.id, log_path, 'console_log')
                    for item in execution_root.glob('runtime_steps*.jsonl'):
                        MobileArtifactService.register_file(result_session, result.id, item, 'runtime_steps')
                    try:
                        report_path = MobileArtifactService.generate_html_report(result, result_cases, log_path)
                        MobileArtifactService.register_file(result_session, result.id, report_path, 'html_report')
                    except Exception:
                        pass
                    if allure_dir.exists():
                        for item in allure_dir.rglob('*'):
                            if item.is_file():
                                MobileArtifactService.register_file(result_session, result.id, item, 'allure_result')
                    MobileAutomationDao.release_device(result_session, serial_no)
                    result_session.commit()
            except subprocess.TimeoutExpired:
                MobileExecutionService._terminate_process(execution.id)
                MobileExecutionService._finish_exception(execution.id, '执行超时')
            except Exception as exc:
                MobileExecutionService._finish_exception(
                    execution.id, '移动自动化执行异常: {0}'.format(str(exc)[:500])
                )
            finally:
                with MobileExecutionService._lock:
                    MobileExecutionService._processes.pop(execution.id, None)

    @staticmethod
    def _sync_runtime_steps(session, execution_id, execution_case_id, execution_root, synced_count,
                            step_offset=0, steps_file_name='runtime_steps.jsonl'):
        """把脚本上报的 runtime_steps.jsonl 同步成执行过程步骤，并挂载步骤截图。"""
        steps_file = Path(execution_root) / (steps_file_name or 'runtime_steps.jsonl')
        if not steps_file.exists():
            return synced_count
        try:
            lines = [line.strip() for line in steps_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        except Exception:
            return synced_count
        if len(lines) <= synced_count:
            return synced_count
        existing = MobileAutomationDao.list_steps(session, execution_id, execution_case_id)
        existing_keys = set()
        for item in existing:
            key = '{0}:{1}'.format(item.step_no, item.instruction or '')
            existing_keys.add(key)
        for line in lines[synced_count:]:
            try:
                data = json.loads(line)
            except Exception:
                continue
            instruction = str(data.get('instruction') or '').strip()
            if not instruction:
                continue
            # step_no：当前用例的 pytest 包装步骤占 offset+1，脚本步骤从 offset+2 开始
            step_no = int(step_offset) + int(data.get('step_no') or 0) + 1
            key = '{0}:{1}'.format(step_no, instruction)
            if key in existing_keys:
                continue
            step = MobileAutomationDao.create_step(session, {
                'execution_id': int(execution_id),
                'execution_case_id': int(execution_case_id) if execution_case_id else None,
                'step_no': step_no,
                'instruction': instruction,
                'action_type': str(data.get('action_type') or 'ui')[:32],
                'action_payload': data.get('action_payload') or {},
                'status': str(data.get('status') or 'success')[:32],
                'error_message': str(data.get('error_message') or '')[:1000],
            })
            screenshot_rel = str(data.get('screenshot_rel') or '').strip().replace('\\', '/')
            if screenshot_rel and '..' not in screenshot_rel and not screenshot_rel.startswith('/'):
                screenshot_path = Path(execution_root) / screenshot_rel
                if screenshot_path.is_file():
                    artifact = MobileArtifactService.register_file(
                        session, execution_id, screenshot_path, 'screenshot',
                        execution_case_id=execution_case_id, step_id=step.id
                    )
                    if artifact:
                        step.after_screenshot_artifact_id = artifact.id
            existing_keys.add(key)
        return len(lines)

    @staticmethod
    def _finish_exception(execution_id, message):
        with get_db_context() as session:
            execution = MobileAutomationDao.get_execution(session, execution_id)
            if not execution:
                return
            ext = execution.ext or {}
            serial_no = ext.get('device_serial')
            result_cases = MobileAutomationDao.list_execution_cases(session, execution_id)
            for item in result_cases:
                if item.status in (0, 1):
                    item.status = 3
                    item.error_message = message
                    item.finished_time = datetime.now()
            execution.status = MobileExecutionService.STATUS_FAILED
            execution.trigger_message = message
            execution.pending_count = 0
            execution.running_count = 0
            execution.failed_count = len(result_cases)
            execution.end_time = datetime.now()
            for step in MobileAutomationDao.list_steps(session, execution.id):
                if step.status == 'running':
                    step.status = 'failed'
                    step.duration_ms = int((execution.end_time - execution.start_time).total_seconds() * 1000) if execution.start_time else None
                    step.error_message = message
                    MobileExecutionService._capture_step_snapshot(session, execution, serial_no, step.execution_case_id, step, True)
            try:
                log_path = MobileArtifactService.execution_root(
                    execution.execution_no, ext.get('project_name')
                ) / 'console.log'
                report_path = MobileArtifactService.generate_html_report(execution, result_cases, log_path)
                MobileArtifactService.register_file(session, execution.id, report_path, 'html_report')
            except Exception:
                pass
            MobileAutomationDao.release_device(session, serial_no)
            session.commit()

    @staticmethod
    def _terminate_process(execution_id):
        with MobileExecutionService._lock:
            process = MobileExecutionService._processes.get(int(execution_id))
        if process and process.poll() is None:
            process.terminate()

    @staticmethod
    def cancel_execution(session, execution_id):
        execution = MobileAutomationDao.get_execution(session, execution_id)
        if not execution:
            return 0, '未查询到对应移动执行记录'
        if execution.trigger_source != 'mobile_platform':
            return 0, '该执行记录不属于移动自动化'
        if execution.status not in (0, 3):
            return 0, '该执行记录已结束，不能取消'
        MobileExecutionService._terminate_process(execution.id)
        serial_no = (execution.ext or {}).get('device_serial')
        for item in MobileAutomationDao.list_execution_cases(session, execution.id):
            if item.status in (0, 1):
                item.status = 7
                item.finished_time = datetime.now()
        execution.status = MobileExecutionService.STATUS_CANCELED
        execution.trigger_message = '用户取消执行'
        execution.end_time = datetime.now()
        execution.pending_count = 0
        execution.running_count = 0
        MobileAutomationDao.release_device(session, serial_no)
        session.commit()
        return execution.id, ''
