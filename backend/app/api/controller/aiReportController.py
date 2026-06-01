# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.aiReportService import AiReportService


class AiReportController(BaseCrudController):
    def report_create(self):
        return AiReportService.create_report(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def report_list(self):
        return AiReportService.report_list(self.session, self.req_data)

    def report_detail(self):
        report_id = self._get(self.req_data, 'reportId', 'id')
        if not report_id:
            return {}, 'reportId 为必传参数'
        return AiReportService.report_detail(self.session, report_id)
