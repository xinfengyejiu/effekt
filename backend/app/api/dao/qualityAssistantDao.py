# encoding: UTF-8
"""对话式质量助手 DAO。"""
from app.api.model.qualityAssistantModel import QaAssistantSession, QaAssistantMessage


class QualityAssistantDao(object):

    @staticmethod
    def create_session(session, values):
        obj = QaAssistantSession(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def get_session(session, session_id=None, session_no=None, user_id=None):
        query = session.query(QaAssistantSession).filter(QaAssistantSession.is_delete == 0)
        if session_id not in (None, ''):
            query = query.filter(QaAssistantSession.id == int(session_id))
        if session_no not in (None, ''):
            query = query.filter(QaAssistantSession.session_no == str(session_no))
        if user_id not in (None, ''):
            query = query.filter(QaAssistantSession.user_id == int(user_id))
        return query.first()

    @staticmethod
    def update_session(session, session_id, values):
        obj = session.query(QaAssistantSession).filter(
            QaAssistantSession.id == int(session_id),
            QaAssistantSession.is_delete == 0,
        ).first()
        if obj:
            for k, v in values.items():
                setattr(obj, k, v)
            session.flush()
        return obj

    @staticmethod
    def soft_delete_session(session, session_id, user_id=None):
        obj = QualityAssistantDao.get_session(session, session_id=session_id, user_id=user_id)
        if obj:
            obj.is_delete = 1
            session.flush()
        return obj

    @staticmethod
    def create_message(session, values):
        obj = QaAssistantMessage(**values)
        session.add(obj)
        session.flush()
        return obj

    @staticmethod
    def list_messages(session, session_id, limit=50):
        return session.query(QaAssistantMessage).filter(
            QaAssistantMessage.session_id == int(session_id)
        ).order_by(QaAssistantMessage.id.asc()).limit(int(limit)).all()

    @staticmethod
    def get_latest_session(session, user_id):
        return session.query(QaAssistantSession).filter(
            QaAssistantSession.user_id == int(user_id),
            QaAssistantSession.is_delete == 0,
        ).order_by(QaAssistantSession.updated_time.desc(), QaAssistantSession.id.desc()).first()
