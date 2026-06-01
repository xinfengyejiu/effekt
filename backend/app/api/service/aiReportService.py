# encoding: UTF-8
from ..dao.aiBaseDao import AiBaseDao
from ..model.aiReportModel import AiQualityReport
from .aiCommonService import AiCommonService


class AiReportService(object):
    UPDATE_FIELDS = ['title', 'risk_level', 'summary', 'metrics', 'findings', 'recommendations', 'markdown_content', 'html_content']

    @staticmethod
    def create_report(session, req_data, user_id=None):
        data = {
            'report_no': AiCommonService.get(req_data, 'reportNo', 'report_no') or AiCommonService.gen_no('AIR'),
            'project_id': int(AiCommonService.get(req_data, 'projectId', 'project_id') or 0),
            'task_id': AiCommonService.get(req_data, 'taskId', 'task_id'),
            'report_type': AiCommonService.get(req_data, 'reportType', 'report_type', default='task'),
            'title': req_data.get('title') or 'AI质量报告',
            'risk_level': AiCommonService.get(req_data, 'riskLevel', 'risk_level'),
            'summary': req_data.get('summary'),
            'metrics': req_data.get('metrics') or {},
            'findings': req_data.get('findings') or [],
            'recommendations': req_data.get('recommendations') or [],
            'markdown_content': AiCommonService.get(req_data, 'markdownContent', 'markdown_content'),
            'html_content': AiCommonService.get(req_data, 'htmlContent', 'html_content'),
            'created_by': user_id
        }
        AiCommonService.fill_product_project_names(session, data, req_data)
        return AiCommonService.create_record(session, AiQualityReport, data, ['report_no', 'project_id', 'report_type', 'title'])

    @staticmethod
    def report_detail(session, report_id):
        return AiCommonService.detail_record(session, AiQualityReport, report_id)

    @staticmethod
    def report_list(session, req_data):
        filters = []
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(AiQualityReport.project_id == int(project_id))
        report_type = AiCommonService.get(req_data, 'reportType', 'report_type')
        if report_type:
            filters.append(AiQualityReport.report_type == report_type)
        risk_level = AiCommonService.get(req_data, 'riskLevel', 'risk_level')
        if risk_level:
            filters.append(AiQualityReport.risk_level == risk_level)
        items, total = AiBaseDao.list_by_filters(session, AiQualityReport, filters, AiCommonService.get(req_data, 'page', default=1), AiCommonService.get(req_data, 'limit', default=20), req_data.get('keyword'), ['report_no', 'title', 'summary'])
        return AiCommonService.list_result(items, total, session, True)
