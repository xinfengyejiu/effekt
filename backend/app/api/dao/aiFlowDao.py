# encoding: UTF-8
from ..model.aiFlowModel import AiSkillFlow
from .aiBaseDao import AiBaseDao


class AiFlowDao(AiBaseDao):
    @staticmethod
    def get_flow_by_code(session, flow_code):
        return AiBaseDao.get_by_code(session, AiSkillFlow, 'flow_code', flow_code)
