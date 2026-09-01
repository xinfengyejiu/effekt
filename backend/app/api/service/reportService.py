# encoding: UTF-8
import os
import re
from datetime import datetime

from ..dao.planDao import PlanDao
from ..dao.projectDao import ProjectDao
from ..dao.reportDao import ReportDao
from ..model.planModel import TestPlan
from ..model.reportModel import Report


class ReportService(object):
    HTML_REPORT_DIR = os.path.join(os.getcwd(), 'attachment', 'test_report')

    @staticmethod
    def create(session, model_cls, add_info):
        return ReportDao.create(session, model_cls, add_info)

    @staticmethod
    def get_by_id(session, model_cls, obj_id):
        return ReportDao.get_by_id(session, model_cls, obj_id)

    @staticmethod
    def list_by_filters(session, model_cls, filter_list, page_num=1, page_size=20, order_column=None, asc=False):
        return ReportDao.list_by_filters(session, model_cls, filter_list, int(page_num), int(page_size), order_column, asc)

    @staticmethod
    def delete_report(session, report_id):
        report = ReportDao.get_by_id(session, Report, report_id)
        if not report:
            return 0, '未查询到对应报告！'
        file_url = report.file_url
        delete_id, err_msg = ReportDao.delete_by_id(session, Report, report_id)
        if err_msg:
            return delete_id, err_msg
        ReportService._remove_html_report_file(file_url)
        return delete_id, ''

    @staticmethod
    def upload_html_report(session, form_data, files):
        product_id = form_data.get('productId') or form_data.get('product_id')

        project_id = form_data.get('projectId') or form_data.get('project_id')
        plan_id = form_data.get('planId') or form_data.get('plan_id')

        report_name = form_data.get('name') or form_data.get('reportName') or form_data.get('report_name')
        generated_by = form_data.get('generatedBy') or form_data.get('generated_by')
        upload_file = files.get('file') if files else None
        if not product_id or not project_id:
            return 0, 'productId、projectId 为必传参数'
        if not upload_file or not upload_file.filename:
            return 0, 'file 为必传参数'
        original_name = upload_file.filename or ''
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in ('.html', '.htm'):
            return 0, '仅支持上传 html、htm 文件'
        project = ProjectDao.get_by_id(session, ProjectDao.project_model(), project_id)
        if not project:
            return 0, '未查询到对应项目！'
        if str(project.product_id) != str(product_id):
            return 0, '项目不属于所选产品'
        content_bytes = upload_file.read()
        html_content = ReportService._decode_html_content(content_bytes)
        if not html_content.strip():
            return 0, 'HTML 文件内容不能为空'
        file_path, file_url = ReportService._save_html_report_file(content_bytes, report_name or original_name, ext)
        add_info = {
            'plan_id': int(plan_id) if plan_id else None,
            'project_id': int(project_id),
            'product_id': int(product_id),

            'name': report_name or os.path.splitext(original_name)[0] or 'HTML测试报告',
            'report_type': 2,
            'summary': {
                'source': 'upload_html',
                'fileName': original_name,
                'fileSize': len(content_bytes)
            },
            'content': html_content,
            'file_url': file_url,
            'generated_by': generated_by
        }
        return ReportDao.create(session, Report, add_info)

    @staticmethod
    def _decode_html_content(content_bytes):
        for encoding in ('utf-8-sig', 'utf-8', 'gbk'):
            try:
                return content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content_bytes.decode('utf-8', errors='ignore')

    @staticmethod
    def _save_html_report_file(content_bytes, report_name, ext):
        os.makedirs(ReportService.HTML_REPORT_DIR, exist_ok=True)
        safe_name = re.sub(r'[\\/:*?"<>|\s]+', '_', str(report_name or '').strip()).strip('_') or 'html_report'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        file_name = '{}_{}{}'.format(safe_name[:80], timestamp, ext)
        file_path = os.path.join(ReportService.HTML_REPORT_DIR, file_name)
        with open(file_path, 'wb') as writer:
            writer.write(content_bytes)
        return file_path, 'attachment/test_report/{}'.format(file_name)

    @staticmethod
    def _remove_html_report_file(file_url):
        if not file_url:
            return
        normalized = str(file_url).replace('\\', '/').lstrip('/')
        prefix = 'attachment/test_report/'
        if not normalized.startswith(prefix):
            return
        file_name = os.path.basename(normalized)
        file_path = os.path.abspath(os.path.join(ReportService.HTML_REPORT_DIR, file_name))
        base_dir = os.path.abspath(ReportService.HTML_REPORT_DIR)
        if not file_path.startswith(base_dir + os.sep):
            return
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

    @staticmethod
    def generate_report(session, plan_id, generated_by=None):

        plan = PlanDao.get_by_id(session, TestPlan, plan_id)
        if not plan:
            return 0, '未查询到对应计划！'
        project = ProjectDao.get_by_id(session, ProjectDao.project_model(), plan.project_id)
        if not project:
            return 0, '未查询到对应项目！'
        # 复用计划统计，保证计划详情和报告中的指标口径一致。
        stats = PlanDao.plan_stats(session, plan_id)
        # MVP 阶段先生成简单 HTML，后续可替换为模板渲染器。
        content = '<html><body><h1>{}</h1><p>总用例：{}</p><p>通过率：{}%</p></body></html>'.format(
            plan.name, stats['total_cases'], stats['pass_rate']
        )
        add_info = {
            'plan_id': int(plan_id),
            'project_id': plan.project_id,
            'product_id': project.product_id,
            'name': '{}_报告'.format(plan.name),
            'report_type': 1,
            'summary': stats,
            'content': content,
            'generated_by': generated_by
        }
        return ReportDao.create(session, Report, add_info)
