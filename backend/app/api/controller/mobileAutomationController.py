# encoding: UTF-8
from app.api.dao.mobileAutomationDao import MobileAutomationDao
from app.api.service.mobileDeviceService import MobileDeviceService
from app.api.service.mobileExecutionService import MobileExecutionService
from app.api.service.mobilePageParserService import MobilePageParserService
from app.api.service.mobileAIVerifyService import MobileAIVerifyService
from app.api.service.mobileScriptGenService import MobileScriptGenService
from app.api.service.mobileScriptDebugService import MobileScriptDebugService


class MobileAutomationController(object):
    @staticmethod
    def environment_check():
        return MobileDeviceService.environment_check()

    @staticmethod
    def start_appium():
        return MobileDeviceService.start_appium()

    @staticmethod
    def scan_devices(session):
        return MobileDeviceService.scan_devices(session)

    @staticmethod
    def list_devices(session, req_data):
        items, total = MobileAutomationDao.list_devices(session, req_data.get('page_no', 1), req_data.get('page_size', 100))
        return {'list': [item.to_dict() for item in items], 'total': total}

    @staticmethod
    def update_device(session, req_data):
        serial_no = req_data.get('serial_no')
        if not serial_no:
            return 0, 'serial_no 为必传参数'
        device = MobileAutomationDao.get_device(session, serial_no)
        if not device:
            return 0, '设备不存在，请先扫描设备'
        for key in ('display_name', 'device_group', 'remark', 'usage_status'):
            if key in req_data:
                setattr(device, key, req_data[key])
        if device.usage_status not in ('idle', 'disabled'):
            return 0, 'usage_status 仅支持 idle 或 disabled'
        session.commit()
        return device.id, ''

    @staticmethod
    def list_apps(session, req_data):
        items, total = MobileAutomationDao.list_apps(
            session, req_data.get('project_id'), req_data.get('page_no', 1), req_data.get('page_size', 100)
        )
        return {'list': [item.to_dict() for item in items], 'total': total}

    @staticmethod
    def create_app(session, req_data, user_id):
        required = ('project_id', 'name', 'package_name')
        missing = [key for key in required if req_data.get(key) in (None, '')]
        if missing:
            return 0, '{0} 为必传参数'.format('、'.join(missing))
        from app.api.model.mobileAutomationModel import MobileApp
        obj = MobileApp(
            project_id=int(req_data['project_id']), name=req_data['name'], package_name=req_data['package_name'],
            launch_activity=req_data.get('launch_activity'), app_type='android', apk_path=req_data.get('apk_path'),
            version_name=req_data.get('version_name'), version_code=req_data.get('version_code'),
            default_capabilities=req_data.get('default_capabilities') or {},
            install_before_run=int(bool(req_data.get('install_before_run', False))),
            clear_data_before_run=int(bool(req_data.get('clear_data_before_run', False))),
            enabled=int(bool(req_data.get('enabled', True))), created_by=user_id,
        )
        session.add(obj)
        session.commit()
        return obj.id, ''

    @staticmethod
    def update_app(session, req_data):
        app_id = req_data.get('id')
        if not app_id:
            return 0, 'id 为必传参数'
        app = MobileAutomationDao.get_app(session, app_id)
        if not app:
            return 0, '应用配置不存在'
        for key in ('name', 'package_name', 'launch_activity', 'apk_path', 'version_name', 'version_code',
                    'default_capabilities', 'install_before_run', 'clear_data_before_run', 'enabled'):
            if key in req_data:
                setattr(app, key, req_data[key])
        session.commit()
        return app.id, ''

    @staticmethod
    def delete_app(session, app_id):
        app = MobileAutomationDao.get_app(session, app_id)
        if not app:
            return 0, '应用配置不存在'
        app.enabled = 0
        session.commit()
        return app.id, ''

    @staticmethod
    def page_snapshot(session, req_data):
        for key in ('execution_id', 'execution_no', 'device_serial'):
            if not req_data.get(key):
                return {}, '{0} 为必传参数'.format(key)
        return MobilePageParserService.capture(
            session, req_data['execution_id'], req_data['execution_no'], req_data['device_serial'], req_data.get('execution_case_id')
        ), ''

    @staticmethod
    def list_configs(session, req_data):
        return MobileExecutionService.list_configs(session, req_data)

    @staticmethod
    def get_config(session, config_id):
        return MobileExecutionService.get_config(session, config_id)

    @staticmethod
    def save_config(session, req_data, user_id):
        return MobileExecutionService.save_config(session, req_data, user_id)

    @staticmethod
    def delete_config(session, config_id):
        return MobileExecutionService.delete_config(session, config_id)

    @staticmethod
    def run_config(session, config_id, user_id):
        return MobileExecutionService.run_config(session, config_id, user_id)

    @staticmethod
    def create_execution(session, req_data, user_id):
        return MobileExecutionService.create_execution(session, req_data, user_id)

    @staticmethod
    def retry_execution(session, execution_id, user_id):
        return MobileExecutionService.retry_execution(session, execution_id, user_id)

    @staticmethod
    def cancel_execution(session, execution_id):
        return MobileExecutionService.cancel_execution(session, execution_id)

    @staticmethod
    def list_executions(session, req_data):
        items, total = MobileAutomationDao.list_executions(
            session, req_data.get('project_id'), req_data.get('page_no', 1), req_data.get('page_size', 20)
        )
        return {'list': [item.to_dict() for item in items], 'total': total}

    @staticmethod
    def execution_detail(session, execution_id):
        item = MobileAutomationDao.get_execution(session, execution_id)
        if not item or item.trigger_source != 'mobile_platform':
            return {}, '移动执行记录不存在'
        return item.to_dict(), ''

    @staticmethod
    def execution_progress(session, execution_id):
        return MobileExecutionService.execution_progress(session, execution_id)

    @staticmethod
    def execution_cases(session, execution_id):
        return {'list': [item.to_dict() for item in MobileAutomationDao.list_execution_cases(session, execution_id)]}

    @staticmethod
    def execution_steps(session, execution_id, execution_case_id=None):
        return {'list': [item.to_dict() for item in MobileAutomationDao.list_steps(session, execution_id, execution_case_id)]}

    @staticmethod
    def execution_artifacts(session, execution_id, execution_case_id=None):
        return {'list': [item.to_dict() for item in MobileAutomationDao.list_artifacts(session, execution_id, execution_case_id)]}

    # ─ AI 相关 ──

    @staticmethod
    def ai_verify_execution_case(session, execution_case_id):
        """对单个用例执行结果进行 AI 验证（手动触发）。"""
        from app.api.model.automationModel import AutoExecutionCase
        case_item = session.query(AutoExecutionCase).filter(
            AutoExecutionCase.id == int(execution_case_id)
        ).first()
        if not case_item:
            return None, '用例执行记录不存在'

        from app.api.dao.mobileAutomationDao import MobileAutomationDao
        from app.api.model.mobileAutomationModel import MobileExecutionStep

        # 获取该用例的最新步骤快照
        steps = MobileAutomationDao.list_steps(session, case_item.execution_id, case_item.id)
        page_snapshot = {}
        for step in reversed(steps):
            if step.page_snapshot:
                page_snapshot = step.page_snapshot
                break

        # 获取 pytest 退出码信息
        exit_code = 0
        error_message = case_item.error_message or ''
        if case_item.status == 3:
            exit_code = 1

        verify_result = MobileAIVerifyService.verify(
            case_title=case_item.case_title or '',
            case_steps=[],
            page_snapshot=page_snapshot,
            exit_code=exit_code,
            error_message=error_message,
        )

        # 写入 ext
        ext = case_item.ext or {}
        ext['ai_verify'] = verify_result
        case_item.ext = ext

        # 根据 AI 结果更新状态
        new_status = MobileAIVerifyService.decide_case_status(verify_result.get('verdict', ''), exit_code)
        case_item.status = new_status
        if verify_result.get('reason'):
            case_item.result_message = '{0} [AI: {1}]'.format(
                case_item.result_message or '', verify_result['reason'][:100]
            ).strip()

        session.commit()
        return {'verdict': verify_result.get('verdict'), 'confidence': verify_result.get('confidence'),
                'reason': verify_result.get('reason'), 'new_status': new_status, 'ai_available': verify_result.get('ai_available', True)}, ''

    @staticmethod
    def ai_generate_scripts(session, req_data, user_id):
        """AI 自动生成 pytest 脚本。"""
        required = ('project_id', 'case_ids')
        missing = [key for key in required if req_data.get(key) in (None, '', [])]
        if missing:
            return None, '{0} 为必传参数'.format('、'.join(missing))
        result, error = MobileScriptGenService.generate_scripts(
            req_data['project_id'], req_data['case_ids'], session
        )
        if error:
            return None, error
        return result, ''

    @staticmethod
    def ai_generate_and_debug_scripts(session, req_data, user_id):
        """AI 生成脚本并自动调试修复。"""
        required = ('project_id', 'case_ids', 'device_serial', 'mobile_app_id')
        missing = [key for key in required if req_data.get(key) in (None, '', [])]
        if missing:
            return None, '{0} 为必传参数'.format('、'.join(missing))
        max_retries = int(req_data.get('max_retries', 3))
        if max_retries < 1:
            max_retries = 1
        elif max_retries > 10:
            max_retries = 10
        result, error = MobileScriptDebugService.debug_and_fix(
            req_data['project_id'], req_data['case_ids'], session,
            req_data['device_serial'], req_data['mobile_app_id'],
            max_retries=max_retries,
        )
        if error:
            return None, error
        return result, ''
