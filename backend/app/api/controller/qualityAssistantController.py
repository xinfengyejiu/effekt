# encoding: UTF-8
"""对话式质量助手控制器。"""
from app.api.service.qualityAssistantService import QualityAssistantService


class QualityAssistantController(object):

    @staticmethod
    def examples():
        return QualityAssistantService.examples()

    @staticmethod
    def chat(db, body, user):
        return QualityAssistantService.chat(db, body, user)

    @staticmethod
    def session_detail(db, session_id, user_id):
        return QualityAssistantService.get_session_detail(db, session_id, user_id)

    @staticmethod
    def latest_session(db, user_id):
        return QualityAssistantService.get_latest_session_detail(db, user_id)

    @staticmethod
    def clear_session(db, session_id, user_id):
        return QualityAssistantService.clear_session(db, session_id, user_id)

    @staticmethod
    def execute_action(db, body, user):
        return QualityAssistantService.execute_action(db, body, user)
