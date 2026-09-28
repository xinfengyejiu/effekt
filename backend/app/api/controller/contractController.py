# encoding: UTF-8
"""契约测试控制器。"""
from app.api.service.contractSuiteService import ContractSuiteService
from app.api.service.contractExecutionService import ContractExecutionService
from app.api.service.contractAiService import ContractAiService


class ContractController(object):

    @staticmethod
    def list_suites(db, params):
        return ContractSuiteService.list_suites(db, params)

    @staticmethod
    def get_suite(db, suite_id):
        return ContractSuiteService.get_suite_detail(db, suite_id)

    @staticmethod
    def create_suite(db, data, user_id=None):
        return ContractSuiteService.create_suite(db, data, user_id)

    @staticmethod
    def update_suite(db, suite_id, data):
        return ContractSuiteService.update_suite(db, suite_id, data)

    @staticmethod
    def delete_suite(db, suite_id):
        return ContractSuiteService.delete_suite(db, suite_id)

    @staticmethod
    def toggle_suite(db, suite_id):
        return ContractSuiteService.toggle_suite(db, suite_id)

    @staticmethod
    def preview_source(db, data):
        return ContractSuiteService.preview_source(db, data)

    @staticmethod
    def run_suite(db, suite_id, user_id=None):
        return ContractExecutionService.trigger_suite_run(db, suite_id, trigger_type='manual', user_id=user_id)

    @staticmethod
    def list_runs(db, params):
        return ContractExecutionService.list_runs(db, params)

    @staticmethod
    def get_run(db, run_id):
        return ContractExecutionService.get_run_detail(db, run_id)

    @staticmethod
    def ai_design(data):
        return ContractAiService.design_interface(data or {})

    @staticmethod
    def ai_analyze(db, data):
        data = data or {}
        run_item_id = data.get('run_item_id') or data.get('id')
        if not run_item_id:
            return None, '缺少 run_item_id'
        use_llm = data.get('use_llm', True)
        return ContractExecutionService.analyze_run_item(db, run_item_id, use_llm=bool(use_llm))
