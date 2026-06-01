# encoding: UTF-8
from ..model.aiToolModel import AiTool, AiToolExecution
from .aiBaseDao import AiBaseDao


class AiToolDao(AiBaseDao):
    @staticmethod
    def get_tool_by_code(session, tool_code):
        return AiBaseDao.get_by_code(session, AiTool, 'tool_code', tool_code)

    @staticmethod
    def count_running_execution(session, tool_id):
        return session.query(AiToolExecution).filter(
            AiToolExecution.tool_id == int(tool_id),
            AiToolExecution.status == 'running'
        ).count()
