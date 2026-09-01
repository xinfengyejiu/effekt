# encoding: UTF-8
"""巡检系统控制器。"""
import logging
from app.api.service.inspectionService import InspectionService
from app.api.service.inspectionExecutionService import InspectionExecutionService

logger = logging.getLogger(__name__)


class InspectionController(object):

    # ────────────── Group ──────────────
    @staticmethod
    def list_groups(db, params):
        return InspectionService.list_groups(db, params)

    @staticmethod
    def get_group(db, group_id):
        return InspectionService.get_group(db, group_id)

    @staticmethod
    def create_group(db, data, user_id=None):
        return InspectionService.create_group(db, data, user_id)

    @staticmethod
    def update_group(db, group_id, data):
        return InspectionService.update_group(db, group_id, data)

    @staticmethod
    def delete_group(db, group_id):
        return InspectionService.delete_group(db, group_id)

    @staticmethod
    def toggle_group(db, group_id):
        return InspectionService.toggle_group(db, group_id)

    # ────────────── Task ──────────────
    @staticmethod
    def list_tasks(db, params):
        return InspectionService.list_tasks(db, params)

    @staticmethod
    def get_task_detail(db, task_id):
        return InspectionService.get_task_detail(db, task_id)

    @staticmethod
    def create_task(db, data, user_id=None):
        return InspectionService.create_task(db, data, user_id)

    @staticmethod
    def update_task(db, task_id, data):
        return InspectionService.update_task(db, task_id, data)

    @staticmethod
    def delete_task(db, task_id):
        return InspectionService.delete_task(db, task_id)

    @staticmethod
    def toggle_task(db, task_id):
        return InspectionService.toggle_task(db, task_id)

    @staticmethod
    def execute_task(db, task_id, user_id=None):
        return InspectionExecutionService.trigger_execution(db, task_id, trigger_type='manual', user_id=user_id)

    @staticmethod
    def execute_group(db, group_id, user_id=None):
        return InspectionExecutionService.trigger_group_execution(
            db, group_id, trigger_type='manual', user_id=user_id
        )

    # ────────────── Item ──────────────
    @staticmethod
    def list_items(db, params):
        return InspectionService.list_items(db, params)

    @staticmethod
    def create_item(db, data):
        return InspectionService.create_item(db, data)

    @staticmethod
    def update_item(db, item_id, data):
        return InspectionService.update_item(db, item_id, data)

    @staticmethod
    def delete_item(db, item_id):
        return InspectionService.delete_item(db, item_id)

    @staticmethod
    def batch_create_items(db, task_id, items_data):
        return InspectionService.batch_create_items(db, task_id, items_data)

    @staticmethod
    def test_item(db, data):
        """单项测试执行。"""
        from app.api.service.inspectionCheckers import get_checker
        item_type = data.get('item_type', 'api')
        config = data.get('config', {})
        timeout = data.get('timeout_seconds', 30)

        # SQL 类型：解析 db_config_id
        if item_type == 'sql' and config.get('db_config_id'):
            from app.api.dao.inspectionDao import InspectionDao
            from app.core.database import get_session_factory
            tmp_db = get_session_factory()()
            try:
                db_config = InspectionDao.get_db_config(tmp_db, config['db_config_id'])
                if db_config:
                    config['db_connection'] = {
                        'type': db_config.db_type,
                        'host': db_config.host,
                        'port': db_config.port,
                        'database_name': db_config.database_name,
                        'username': db_config.username,
                        'password': db_config.password,
                    }
            finally:
                tmp_db.close()

        checker = get_checker(item_type)
        result = checker.execute(config, timeout=timeout)
        from app.api.service.inspectionCheckers.ai_judge import InspectionAiJudge
        return InspectionAiJudge.apply_ai_to_checker_result(result, config, item_type=item_type)

    # ────────────── DbConfig ──────────────
    @staticmethod
    def list_db_configs(db, params):
        return InspectionService.list_db_configs(db, params)

    @staticmethod
    def create_db_config(db, data, user_id=None):
        return InspectionService.create_db_config(db, data, user_id)

    @staticmethod
    def update_db_config(db, config_id, data):
        return InspectionService.update_db_config(db, config_id, data)

    @staticmethod
    def delete_db_config(db, config_id):
        return InspectionService.delete_db_config(db, config_id)

    @staticmethod
    def test_db_connection(db, data):
        return InspectionService.test_db_connection(db, data)

    # ────────────── Execution ──────────────
    @staticmethod
    def list_executions(db, params):
        return InspectionExecutionService.list_executions(db, params)

    @staticmethod
    def get_execution_detail(db, execution_id):
        return InspectionExecutionService.get_execution_detail(db, execution_id)

    # ────────────── Dashboard / Report ──────────────
    @staticmethod
    def get_dashboard(db, project_id=None):
        return InspectionService.get_dashboard(db, project_id)

    @staticmethod
    def get_trend(db, project_id=None, days=7):
        return InspectionService.get_trend(db, project_id, days)
