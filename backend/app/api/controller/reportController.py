# encoding: UTF-8
from .baseCrudController import BaseCrudController
from ..model.planModel import TestPlan
from ..model.reportModel import Report
from ..service.reportService import ReportService


class ReportController(BaseCrudController):
    """测试报告相关接口控制器。"""

    def report_list(self):
        """分页查询报告列表，可按产品、项目、计划过滤。"""
        filters = []
        product_id = self._get(self.req_data, 'productId', 'product_id')
        if product_id:
            filters.append(Report.product_id == int(product_id))
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        if project_id:
            filters.append(Report.project_id == int(project_id))
        plan_id = self._get(self.req_data, 'planId', 'plan_id')
        if plan_id:
            filters.append(Report.plan_id == int(plan_id))
        items, total = ReportService.list_by_filters(self.session, Report, filters, self._get(self.req_data, 'pageNo', default=1), self._get(self.req_data, 'pageSize', default=20), Report.generated_time)
        result_list = []
        for item in items:
            item_dict = self.serialize(item)
            plan = self.session.query(TestPlan).filter(TestPlan.id == item.plan_id).first()
            item_dict['plan_name'] = plan.name if plan else None
            result_list.append(item_dict)
        return {'list': result_list, 'total': total}

    def report_detail(self):
        """查询报告详情，返回 summary 和 HTML content。"""
        report_id = self._get(self.req_data, 'reportId', 'report_id', 'id')
        if not report_id:
            return {}, 'reportId 为必传参数'
        item = ReportService.get_by_id(self.session, Report, report_id)
        if not item:
            return {}, '未查询到对应报告！'
        return self.serialize(item), ''

    def report_generate(self):
        """同步生成报告：聚合计划执行数据并落库。"""
        plan_id = self._get(self.req_data, 'planId', 'plan_id')
        if not plan_id:
            return 0, 'planId 为必传参数'
        return ReportService.generate_report(self.session, plan_id, self._get(self.req_data, 'generatedBy', 'generated_by'))

    def report_delete(self):
        """删除测试报告。"""
        report_id = self._get(self.req_data, 'reportId', 'report_id', 'id')
        if not report_id:
            return 0, 'reportId 为必传参数'
        return ReportService.delete_report(self.session, report_id)

    def report_upload_html(self):
        """上传 HTML 测试报告并落库。"""

        return ReportService.upload_html_report(self.session, self.req_data.form, self.req_data.files)
