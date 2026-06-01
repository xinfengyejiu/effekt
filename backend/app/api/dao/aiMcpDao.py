# encoding: UTF-8
from ..model.aiMcpModel import AiMcpConnector
from .aiBaseDao import AiBaseDao


class AiMcpDao(AiBaseDao):
    @staticmethod
    def get_connector_by_code(session, connector_code):
        return AiBaseDao.get_by_code(session, AiMcpConnector, 'connector_code', connector_code)
