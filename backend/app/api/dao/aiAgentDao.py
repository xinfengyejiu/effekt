# encoding: UTF-8
from ..model.aiAgentModel import AiAgent, AiAgentExecution
from .aiBaseDao import AiBaseDao


class AiAgentDao(AiBaseDao):
    @staticmethod
    def get_agent_by_code(session, agent_code):
        return AiBaseDao.get_by_code(session, AiAgent, 'agent_code', agent_code)

    @staticmethod
    def count_running_execution(session, agent_id):
        return session.query(AiAgentExecution).filter(
            AiAgentExecution.agent_id == int(agent_id),
            AiAgentExecution.status == 'running'
        ).count()
