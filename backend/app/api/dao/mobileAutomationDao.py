# encoding: UTF-8
from datetime import datetime

from sqlalchemy import and_

from app.api.model.automationModel import AutoExecution, AutoExecutionCase
from app.api.model.mobileAutomationModel import MobileApp, MobileArtifact, MobileDevice, MobileExecutionConfig, MobileExecutionConfigCase, MobileExecutionStep


class MobileAutomationDao(object):
    @staticmethod
    def list_configs(session, project_id=None, page_no=1, page_size=20):
        query = session.query(MobileExecutionConfig).filter(MobileExecutionConfig.enabled == 1)
        if project_id not in (None, ''):
            query = query.filter(MobileExecutionConfig.project_id == int(project_id))
        total = query.count()
        items = query.order_by(MobileExecutionConfig.updated_time.desc(), MobileExecutionConfig.id.desc()).offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_config(session, config_id):
        return session.query(MobileExecutionConfig).filter(MobileExecutionConfig.id == int(config_id)).first()

    @staticmethod
    def list_config_cases(session, config_id):
        return session.query(MobileExecutionConfigCase).filter(MobileExecutionConfigCase.config_id == int(config_id)).order_by(MobileExecutionConfigCase.run_order.asc()).all()

    @staticmethod
    def list_devices(session, page_no=1, page_size=100):
        query = session.query(MobileDevice).order_by(MobileDevice.updated_time.desc(), MobileDevice.id.desc())
        total = query.count()
        items = query.offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_device(session, serial_no):
        return session.query(MobileDevice).filter(MobileDevice.serial_no == serial_no).first()

    @staticmethod
    def upsert_device(session, serial_no, values):
        obj = MobileAutomationDao.get_device(session, serial_no)
        if obj is None:
            obj = MobileDevice(serial_no=serial_no, **values)
            session.add(obj)
        else:
            for key, value in values.items():
                setattr(obj, key, value)
        session.flush()
        return obj

    @staticmethod
    def list_apps(session, project_id=None, page_no=1, page_size=100):
        query = session.query(MobileApp)
        if project_id not in (None, ''):
            query = query.filter(MobileApp.project_id == int(project_id))
        total = query.count()
        items = query.order_by(MobileApp.updated_time.desc(), MobileApp.id.desc()).offset(
            (int(page_no) - 1) * int(page_size)
        ).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def get_app(session, app_id):
        return session.query(MobileApp).filter(MobileApp.id == int(app_id)).first()

    @staticmethod
    def create_artifact(session, values):
        obj = MobileArtifact(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def get_artifact(session, artifact_id):
        return session.query(MobileArtifact).filter(MobileArtifact.id == int(artifact_id)).first()

    @staticmethod
    def list_artifacts(session, execution_id, execution_case_id=None):
        query = session.query(MobileArtifact).filter(MobileArtifact.execution_id == int(execution_id))
        if execution_case_id not in (None, ''):
            query = query.filter(MobileArtifact.execution_case_id == int(execution_case_id))
        return query.order_by(MobileArtifact.created_time.asc(), MobileArtifact.id.asc()).all()

    @staticmethod
    def create_step(session, values):
        obj = MobileExecutionStep(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def list_steps(session, execution_id, execution_case_id=None):
        query = session.query(MobileExecutionStep).filter(MobileExecutionStep.execution_id == int(execution_id))
        if execution_case_id not in (None, ''):
            query = query.filter(MobileExecutionStep.execution_case_id == int(execution_case_id))
        return query.order_by(MobileExecutionStep.execution_case_id.asc(), MobileExecutionStep.step_no.asc()).all()

    @staticmethod
    def lock_device(session, serial_no):
        device = session.query(MobileDevice).filter(MobileDevice.serial_no == serial_no).with_for_update().first()
        if not device:
            return None, '设备未登记，请先扫描设备'
        if device.adb_status != 'online':
            return None, '设备当前不在线'
        if device.usage_status != 'idle':
            return None, '设备当前正在被占用或已禁用'
        device.usage_status = 'running'
        session.flush()
        return device, ''

    @staticmethod
    def release_device(session, serial_no):
        device = MobileAutomationDao.get_device(session, serial_no)
        if device and device.usage_status == 'running':
            device.usage_status = 'idle'
            session.flush()

    @staticmethod
    def create_execution(session, values, case_items):
        execution = AutoExecution(**values)
        session.add(execution)
        session.flush()
        for order, case_item in enumerate(case_items, start=1):
            session.add(AutoExecutionCase(
                execution_id=execution.id,
                case_id=case_item.id,
                case_key=case_item.case_key,
                case_title=case_item.title,
                run_order=order,
                status=0,
                ext={}
            ))
        session.flush()
        return execution

    @staticmethod
    def get_execution(session, execution_id):
        return session.query(AutoExecution).filter(AutoExecution.id == int(execution_id)).first()

    @staticmethod
    def list_executions(session, project_id=None, page_no=1, page_size=20):
        query = session.query(AutoExecution).filter(AutoExecution.trigger_source == 'mobile_platform')
        if project_id not in (None, ''):
            query = query.filter(AutoExecution.project_id == int(project_id))
        total = query.count()
        items = query.order_by(AutoExecution.created_time.desc()).offset((int(page_no) - 1) * int(page_size)).limit(int(page_size)).all()
        return items, total

    @staticmethod
    def list_execution_cases(session, execution_id):
        return session.query(AutoExecutionCase).filter(
            AutoExecutionCase.execution_id == int(execution_id)
        ).order_by(AutoExecutionCase.run_order.asc()).all()

    @staticmethod
    def set_execution_status(session, execution_id, status, **extra):
        obj = MobileAutomationDao.get_execution(session, execution_id)
        if obj is None:
            return None
        obj.status = status
        for key, value in extra.items():
            setattr(obj, key, value)
        session.flush()
        return obj
