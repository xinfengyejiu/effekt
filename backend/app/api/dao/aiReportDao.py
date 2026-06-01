# encoding: UTF-8
from ..model.aiReportModel import AiQualityReport
from .aiBaseDao import AiBaseDao


class AiReportDao(AiBaseDao):
    @staticmethod
    def get_report_by_no(session, report_no):
        return AiBaseDao.get_by_code(session, AiQualityReport, 'report_no', report_no)
