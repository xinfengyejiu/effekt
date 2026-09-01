# encoding: UTF-8
"""巡检执行引擎。"""
from app.api.service.inspectionCheckers.api_checker import ApiChecker
from app.api.service.inspectionCheckers.sql_checker import SqlChecker
from app.api.service.inspectionCheckers.script_checker import ScriptChecker
from app.api.service.inspectionCheckers.auto_case_checker import AutoCaseChecker

CHECKER_MAP = {
    'api': ApiChecker,
    'sql': SqlChecker,
    'script': ScriptChecker,
    'auto_case': AutoCaseChecker,
}


def get_checker(item_type):
    """根据巡检项类型获取对应的执行引擎。"""
    cls = CHECKER_MAP.get(item_type)
    if cls is None:
        raise ValueError('未知的巡检项类型: {}'.format(item_type))
    return cls()
