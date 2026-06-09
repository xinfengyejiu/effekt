# encoding: UTF-8
import os
import time

from werkzeug.utils import secure_filename

from .baseCrudController import BaseCrudController
from ..model.caseModel import Module, TestCase
from ..model.productModel import Product
from ..model.projectModel import Project
from ..model.preciseTestModel import (PreciseAnalysis, PreciseChangedFile, PreciseCoverageReport,
                                      PreciseExecution, PreciseIncrementalCoverage, PreciseQualityGate,
                                      PreciseRecommendation, PreciseRelationMap)
from ..service.gitDiffService import GitDiffService
from ..service.preciseTestService import PreciseTestService


class PreciseTestController(BaseCrudController):
    @staticmethod
    def _snake_key(name):
        result = []
        for char in name:
            if char.isupper():
                result.append('_')
                result.append(char.lower())
            else:
                result.append(char)
        return ''.join(result).lstrip('_')

    def _json_body(self):
        if hasattr(self.req_data, 'get_json'):
            return self.req_data.get_json(silent=True) or {}
        return self.req_data or {}

    def _query_args(self):
        if hasattr(self.req_data, 'args'):
            return self.req_data.args
        return self.req_data or {}

    def _page(self):
        req_data = self._query_args()
        return (self._get(req_data, 'pageNo', 'page', default=1),
                self._get(req_data, 'pageSize', 'size', default=20))

    def _collect(self, req_data, fields):
        data = {}
        for field in fields:
            value = self._get(req_data, field, self._snake_key(field))
            if value is not None:
                data[self._snake_key(field)] = value
        return data

    def _list(self, model_cls, filters, order_column=None, soft_delete=True):
        page_no, page_size = self._page()
        items, total = PreciseTestService.list_by_filters(self.session, model_cls, filters, page_no, page_size,
                                                          order_column or getattr(model_cls, 'created_time', None),
                                                          soft_delete)
        rows = self.serialize_list(items, ['is_delete'])
        self._fill_product_project_names(rows)
        return {'list': rows, 'total': total}

    def _detail(self, model_cls, obj_id, name='id', soft_delete=True):
        if not obj_id:
            return {}, f'{name} 为必传参数'
        item = PreciseTestService.get_by_id(self.session, model_cls, obj_id, soft_delete)
        if not item:
            return {}, '未查询到对应记录！'
        detail = self.serialize(item, ['is_delete'])
        self._fill_product_project_names([detail])
        return detail, ''

    def _fill_product_project_names(self, rows):
        if not rows:
            return rows
        product_ids = set()
        project_ids = set()
        for row in rows:
            product_id = row.get('product_id') or row.get('productId')
            project_id = row.get('project_id') or row.get('projectId')
            if product_id not in (None, ''):
                product_ids.add(int(product_id))
            if project_id not in (None, ''):
                project_ids.add(int(project_id))
        products = {}
        projects = {}
        if project_ids:
            projects = {item.id: item for item in self.session.query(Project).filter(
                Project.id.in_(project_ids), Project.is_delete == 0).all()}
            product_ids.update([item.product_id for item in projects.values() if item.product_id])
        if product_ids:
            products = {item.id: item.name for item in self.session.query(Product).filter(
                Product.id.in_(product_ids), Product.is_delete == 0).all()}
        for row in rows:
            project_id = row.get('project_id') or row.get('projectId')
            product_id = row.get('product_id') or row.get('productId')
            project = projects.get(int(project_id)) if project_id not in (None, '') else None
            if project:
                row.setdefault('project_name', project.name)
                row.setdefault('projectName', project.name)
                if not product_id and project.product_id:
                    product_id = project.product_id
                    row.setdefault('product_id', product_id)
                    row.setdefault('productId', product_id)
            product_name = products.get(int(product_id)) if product_id not in (None, '') else None
            if product_name:
                row.setdefault('product_name', product_name)
                row.setdefault('productName', product_name)
        return rows

    def _fill_case_names(self, rows):
        if not rows:
            return rows
        case_ids = set()
        for row in rows:
            case_id = row.get('case_id') or row.get('caseId')
            if case_id not in (None, ''):
                case_ids.add(int(case_id))
        if not case_ids:
            return rows
        cases = self.session.query(TestCase, Module).outerjoin(
            Module, TestCase.module_id == Module.id
        ).filter(
            TestCase.id.in_(case_ids),
            TestCase.is_delete == 0
        ).all()
        case_map = {int(case.id): (case, module) for case, module in cases}
        priority_map = {0: 'P0', 1: 'P1', 2: 'P2', 3: 'P3'}
        for row in rows:
            case_id = row.get('case_id') or row.get('caseId')
            if case_id in (None, ''):
                continue
            case_info = case_map.get(int(case_id))
            if not case_info:
                continue
            case, module = case_info
            row.setdefault('case_key', case.case_key)
            row.setdefault('caseKey', case.case_key)
            row.setdefault('case_title', case.title)
            row.setdefault('caseTitle', case.title)
            row.setdefault('case_priority', priority_map.get(int(case.priority or 2), 'P2'))
            row.setdefault('casePriority', priority_map.get(int(case.priority or 2), 'P2'))
            row.setdefault('case_is_auto', int(case.is_auto or 0))
            row.setdefault('caseIsAuto', int(case.is_auto or 0))
            if module:
                row.setdefault('actual_module_name', module.name)
                row.setdefault('actualModuleName', module.name)
                row.setdefault('module_path', module.path)
                row.setdefault('modulePath', module.path)
        return rows

    def _create(self, model_cls, required_fields, allowed_fields, defaults=None):
        req_data = self._json_body()
        for field in required_fields:
            if not self._get(req_data, field, self._snake_key(field)):
                return 0, f'{field} 为必传参数'
        add_info = self._collect(req_data, allowed_fields)
        for key, value in (defaults or {}).items():
            add_info.setdefault(key, value)
        return PreciseTestService.create(self.session, model_cls, add_info)

    def _update(self, model_cls, obj_id, allowed_fields, name='id', soft_delete=True):
        if not obj_id:
            return 0, f'{name} 为必传参数'
        req_data = self._json_body()
        update_info = self._collect(req_data, allowed_fields)
        if not update_info:
            return int(obj_id), ''
        return PreciseTestService.update_by_id(self.session, model_cls, obj_id, update_info, soft_delete)

    def _delete(self, model_cls, obj_id, name='id'):
        if not obj_id:
            return 0, f'{name} 为必传参数'
        return PreciseTestService.delete_by_id(self.session, model_cls, obj_id)

    def analysis_list(self):
        req_data = self._query_args()
        filters = []
        project_id = self._get(req_data, 'projectId', 'project_id')
        product_id = self._get(req_data, 'productId', 'product_id')
        status = self._get(req_data, 'status')
        keyword = self._get(req_data, 'keyword', 'title')
        if project_id:
            filters.append(PreciseAnalysis.project_id == int(project_id))
        if product_id:
            filters.append(PreciseAnalysis.product_id == int(product_id))
        if status not in (None, ''):
            filters.append(PreciseAnalysis.status == int(status))
        if keyword:
            filters.append(PreciseAnalysis.title.like('%{}%'.format(keyword)))
        return self._list(PreciseAnalysis, filters)

    def analysis_create(self):
        fields = ['productId', 'projectId', 'repositoryUrl', 'branchName', 'baseCommit', 'targetCommit', 'title',
                  'description', 'createdBy']
        defaults = {'analysis_no': 'PA{}'.format(int(time.time() * 1000)), 'status': 1, 'is_delete': 0}
        return self._create(PreciseAnalysis, ['repositoryUrl', 'baseCommit', 'targetCommit'], fields, defaults)

    def analysis_detail(self, analysis_id):
        detail, err = self._detail(PreciseAnalysis, analysis_id, 'analysisId')
        if err:
            return detail, err
        req_data = self._query_args()
        include_real_snippets = str(self._get(req_data, 'includeRealSnippets', 'include_real_snippets', default='0')).lower() in ('1', 'true')
        changed_files, _ = PreciseTestService.list_by_filters(
            self.session, PreciseChangedFile, [PreciseChangedFile.analysis_id == int(analysis_id)], None, None)
        recommendations, _ = PreciseTestService.list_by_filters(
            self.session, PreciseRecommendation, [PreciseRecommendation.analysis_id == int(analysis_id)], None, None)
        coverages, _ = PreciseTestService.list_by_filters(
            self.session, PreciseCoverageReport, [PreciseCoverageReport.analysis_id == int(analysis_id)], 1, 20,
            PreciseCoverageReport.created_time)
        gates, _ = PreciseTestService.list_by_filters(
            self.session, PreciseQualityGate, [PreciseQualityGate.analysis_id == int(analysis_id)], 1, 1,
            PreciseQualityGate.created_time)
        changed_rows = self.serialize_list(changed_files, ['is_delete'])
        for row in changed_rows:
            changed_lines = row.get('changed_lines') or row.get('changedLines') or []
            snippets = row.get('code_snippets') or row.get('codeSnippets') or []
            if include_real_snippets and changed_lines:
                real_snippets = GitDiffService.get_code_snippets(
                    detail.get('repository_url') or detail.get('repositoryUrl'),
                    detail.get('branch_name') or detail.get('branchName'),
                    detail.get('target_commit') or detail.get('targetCommit'),
                    row.get('file_path') or row.get('filePath'),
                    changed_lines,
                    3)
                if real_snippets:
                    snippets = real_snippets
            row['code_snippets'] = snippets
            row['codeSnippets'] = snippets
        detail['changedFiles'] = changed_rows
        recommendation_rows = self.serialize_list(recommendations, ['is_delete'])
        self._fill_case_names(recommendation_rows)
        detail['recommendations'] = recommendation_rows
        detail['coverages'] = self.serialize_list(coverages, ['is_delete'])
        detail['qualityGate'] = self.serialize(gates[0], ['is_delete']) if gates else None
        return detail, ''

    def analysis_update(self, analysis_id):
        fields = ['productId', 'projectId', 'repositoryUrl', 'branchName', 'baseCommit', 'targetCommit', 'title',
                  'description', 'riskLevel', 'status']
        return self._update(PreciseAnalysis, analysis_id, fields, 'analysisId')

    def analysis_delete(self, analysis_id):
        return self._delete(PreciseAnalysis, analysis_id, 'analysisId')

    def parse_diff(self, analysis_id):
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        return PreciseTestService.parse_diff(self.session, analysis_id)

    def ai_impact(self, analysis_id):
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        return PreciseTestService.ai_impact(self.session, analysis_id)

    def relation_list(self):
        req_data = self._query_args()
        filters = []
        project_id = self._get(req_data, 'projectId', 'project_id')
        product_id = self._get(req_data, 'productId', 'product_id')
        relation_type = self._get(req_data, 'relationType', 'relation_type')
        keyword = self._get(req_data, 'keyword')
        if project_id:
            filters.append(PreciseRelationMap.project_id == int(project_id))
        if product_id:
            filters.append(PreciseRelationMap.product_id == int(product_id))
        if relation_type:
            filters.append(PreciseRelationMap.relation_type == relation_type)
        if keyword:
            filters.append(PreciseRelationMap.source_key.like('%{}%'.format(keyword)))
        return self._list(PreciseRelationMap, filters)

    def relation_create(self):
        fields = ['productId', 'projectId', 'relationType', 'sourceType', 'sourceKey', 'targetType', 'targetKey',
                  'weight', 'confidence', 'sourceOrigin', 'status', 'createdBy']
        return self._create(PreciseRelationMap, ['relationType', 'sourceKey', 'targetKey'], fields,
                            {'status': 1, 'source_origin': 'manual', 'is_delete': 0})

    def relation_update(self, relation_id):
        fields = ['productId', 'projectId', 'relationType', 'sourceType', 'sourceKey', 'targetType', 'targetKey',
                  'weight', 'confidence', 'sourceOrigin', 'status']
        return self._update(PreciseRelationMap, relation_id, fields, 'relationId')

    def relation_delete(self, relation_id):
        return self._delete(PreciseRelationMap, relation_id, 'relationId')

    def recommendation_generate(self, analysis_id):
        if not analysis_id:
            return [], 'analysisId 为必传参数'
        data, err = PreciseTestService.generate_recommendations(self.session, analysis_id)
        return {'list': data, 'total': len(data)}, err

    def recommendation_list(self, analysis_id):
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        items, total = PreciseTestService.list_by_filters(
            self.session, PreciseRecommendation, [PreciseRecommendation.analysis_id == int(analysis_id)], None, None,
            PreciseRecommendation.created_time)
        rows = self.serialize_list(items, ['is_delete'])
        self._fill_case_names(rows)
        return {'list': rows, 'total': total}, ''

    def recommendation_accept(self):
        req_data = self._json_body()
        ids = self._get(req_data, 'ids', default=[])
        accepted = int(self._get(req_data, 'accepted', default=1))
        if not ids:
            return 0, 'ids 为必传参数'
        if not isinstance(ids, list):
            ids = [ids]
        count = 0
        for item_id in ids:
            _, err = PreciseTestService.update_by_id(self.session, PreciseRecommendation, item_id, {'accepted': accepted})
            if not err:
                count += 1
        return {'updated': count}, ''

    def execute(self, analysis_id):
        req_data = self._json_body()
        created_by = self._get(req_data, 'createdBy', 'created_by')
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        return PreciseTestService.execute(self.session, analysis_id, created_by)

    def execution_list(self):
        PreciseTestService.sync_jenkins(self.session)
        req_data = self._query_args()
        filters = []
        analysis_id = self._get(req_data, 'analysisId', 'analysis_id')
        status = self._get(req_data, 'status')
        if analysis_id:
            filters.append(PreciseExecution.analysis_id == int(analysis_id))
        if status not in (None, ''):
            filters.append(PreciseExecution.status == int(status))
        return self._list(PreciseExecution, filters)

    def sync_jenkins(self):
        return PreciseTestService.sync_jenkins(self.session)

    def coverage_upload(self):
        req_data = self.req_data.form if hasattr(self.req_data, 'form') else self._json_body()
        analysis_id = self._get(req_data, 'analysisId', 'analysis_id')
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        upload_file = self.req_data.files.get('file') if hasattr(self.req_data, 'files') else None
        if not upload_file:
            return {}, 'file 为必传参数'
        filename = secure_filename(upload_file.filename or 'jacoco.xml') or 'jacoco.xml'
        base_dir = os.path.abspath(os.path.join(os.getcwd(), 'resources', 'precise_coverage', str(analysis_id), str(int(time.time() * 1000))))
        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, filename)
        upload_file.save(file_path)
        execution_id = self._get(req_data, 'executionId', 'execution_id')
        created_by = self._get(req_data, 'createdBy', 'created_by')
        return PreciseTestService.create_coverage_from_file(self.session, analysis_id, execution_id, file_path, '', created_by)

    def coverage_list(self):
        req_data = self._query_args()
        filters = []
        analysis_id = self._get(req_data, 'analysisId', 'analysis_id')
        product_id = self._get(req_data, 'productId', 'product_id')
        project_id = self._get(req_data, 'projectId', 'project_id')
        report_no = self._get(req_data, 'reportNo', 'report_no')
        analysis_no = self._get(req_data, 'analysisNo', 'analysis_no')
        keyword = self._get(req_data, 'keyword')
        if analysis_id:
            filters.append(PreciseCoverageReport.analysis_id == int(analysis_id))
        if report_no:
            filters.append(PreciseCoverageReport.report_no.like('%{}%'.format(report_no)))
        if product_id or project_id:
            analysis_query = self.session.query(PreciseAnalysis).filter(PreciseAnalysis.is_delete == 0)
            if product_id:
                analysis_query = analysis_query.filter(PreciseAnalysis.product_id == int(product_id))
            if project_id:
                analysis_query = analysis_query.filter(PreciseAnalysis.project_id == int(project_id))
            if analysis_no:
                analysis_query = analysis_query.filter(PreciseAnalysis.analysis_no.like('%{}%'.format(analysis_no)))
            if keyword:
                analysis_query = analysis_query.filter(PreciseAnalysis.analysis_no.like('%{}%'.format(keyword)))
            analysis_ids = [item.id for item in analysis_query.all()]
            if not analysis_ids:
                return {'list': [], 'total': 0}
            filters.append(PreciseCoverageReport.analysis_id.in_(analysis_ids))
        elif analysis_no or keyword:
            analysis_query = self.session.query(PreciseAnalysis).filter(PreciseAnalysis.is_delete == 0)
            if analysis_no:
                analysis_query = analysis_query.filter(PreciseAnalysis.analysis_no.like('%{}%'.format(analysis_no)))
            if keyword:
                analysis_query = analysis_query.filter(PreciseAnalysis.analysis_no.like('%{}%'.format(keyword)))
            analysis_ids = [item.id for item in analysis_query.all()]
            if not analysis_ids:
                return {'list': [], 'total': 0}
            filters.append(PreciseCoverageReport.analysis_id.in_(analysis_ids))
        result = self._list(PreciseCoverageReport, filters)
        rows = result.get('list') or []
        analysis_ids = [row.get('analysis_id') or row.get('analysisId') for row in rows
                        if row.get('analysis_id') or row.get('analysisId')]
        if analysis_ids:
            analyses = self.session.query(PreciseAnalysis).filter(
                PreciseAnalysis.id.in_([int(item) for item in analysis_ids]),
                PreciseAnalysis.is_delete == 0).all()
            analysis_map = {item.id: item for item in analyses}
            enrich_rows = []
            for row in rows:
                analysis = analysis_map.get(int(row.get('analysis_id') or row.get('analysisId')))
                if analysis:
                    row['analysis_no'] = analysis.analysis_no
                    row['analysisNo'] = analysis.analysis_no
                    row['product_id'] = analysis.product_id
                    row['productId'] = analysis.product_id
                    row['project_id'] = analysis.project_id
                    row['projectId'] = analysis.project_id
                    enrich_rows.append(row)
            self._fill_product_project_names(enrich_rows)
        return result

    def coverage_detail(self, coverage_id):
        detail, err = self._detail(PreciseCoverageReport, coverage_id, 'coverageId')
        if err:
            return detail, err
        req_data = self._query_args()
        include_real_snippets = str(self._get(req_data, 'includeRealSnippets', 'include_real_snippets', default='0')).lower() in ('1', 'true')
        items, _ = PreciseTestService.list_by_filters(
            self.session, PreciseIncrementalCoverage,
            [PreciseIncrementalCoverage.coverage_report_id == int(coverage_id)], None, None)
        analysis = None
        if include_real_snippets:
            analysis = PreciseTestService.get_by_id(self.session, PreciseAnalysis, detail.get('analysis_id') or detail.get('analysisId'))
        changed_files, _ = PreciseTestService.list_by_filters(
            self.session, PreciseChangedFile,
            [PreciseChangedFile.analysis_id == int(detail.get('analysis_id') or detail.get('analysisId'))], None, None)
        changed_by_path = {item.file_path: item for item in changed_files}
        rows = self.serialize_list(items, ['is_delete'])
        for row in rows:
            changed = changed_by_path.get(row.get('file_path') or row.get('filePath'))
            detail_json = row.get('detail_json') or row.get('detailJson') or {}
            if not isinstance(detail_json, dict):
                detail_json = {}
            row['changedLines'] = (changed.changed_lines if changed else []) or detail_json.get('changedLines') or detail_json.get('changed_lines') or []
            uncovered_lines = row.get('uncovered_lines') or row.get('uncoveredLines') or []
            changed_snippets = detail_json.get('changedCodeSnippets') or detail_json.get('changed_code_snippets') or (changed.code_snippets if changed else []) or []
            uncovered_snippets = detail_json.get('uncoveredCodeSnippets') or detail_json.get('uncovered_code_snippets') or []
            if analysis:
                real_changed_snippets = GitDiffService.get_code_snippets(
                    analysis.repository_url, analysis.branch_name, analysis.target_commit,
                    row.get('file_path') or row.get('filePath'), row['changedLines'], 3)
                real_uncovered_snippets = GitDiffService.get_code_snippets(
                    analysis.repository_url, analysis.branch_name, analysis.target_commit,
                    row.get('file_path') or row.get('filePath'), uncovered_lines, 3)
                if real_changed_snippets:
                    changed_snippets = real_changed_snippets
                if real_uncovered_snippets:
                    uncovered_snippets = real_uncovered_snippets
            row['changedCodeSnippets'] = changed_snippets
            row['uncoveredCodeSnippets'] = uncovered_snippets
        detail['incrementalFiles'] = rows
        return detail, ''

    def calculate_incremental(self, coverage_id):
        if not coverage_id:
            return {}, 'coverageId 为必传参数'
        return PreciseTestService.calculate_incremental(self.session, coverage_id)

    def ai_risk_analysis(self, coverage_id):
        if not coverage_id:
            return {}, 'coverageId 为必传参数'
        return PreciseTestService.ai_risk_analysis(self.session, coverage_id)

    def relation_import(self):
        req_data = self._json_body()
        rows = self._get(req_data, 'rows', 'list', default=[])
        if not rows or not isinstance(rows, list):
            return {}, 'rows 为必传数组'
        created = 0
        for row in rows:
            add_info = self._collect(row, ['productId', 'projectId', 'relationType', 'sourceType', 'sourceKey',
                                           'targetType', 'targetKey', 'weight', 'confidence', 'sourceOrigin',
                                           'status', 'createdBy'])
            add_info.setdefault('status', 1)
            add_info.setdefault('source_origin', 'imported')
            add_info.setdefault('is_delete', 0)
            _, err = PreciseTestService.create(self.session, PreciseRelationMap, add_info)
            if not err:
                created += 1
        return {'created': created}, ''

    def execution_detail(self, execution_id):
        return self._detail(PreciseExecution, execution_id, 'executionId')

    def coverage_pull_from_jenkins(self):
        import urllib.request
        req_data = self._json_body()
        analysis_id = self._get(req_data, 'analysisId', 'analysis_id')
        artifact_url = self._get(req_data, 'artifactUrl', 'artifact_url')
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        if not artifact_url:
            return {}, 'artifactUrl 为必传参数'
        base_dir = os.path.abspath(os.path.join(os.getcwd(), 'resources', 'precise_coverage', str(analysis_id), str(int(time.time() * 1000))))
        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, 'jacoco.xml')
        try:
            urllib.request.urlretrieve(artifact_url, file_path)
        except Exception as err:
            return {}, f'拉取JaCoCo产物失败：{err}'
        execution_id = self._get(req_data, 'executionId', 'execution_id')
        created_by = self._get(req_data, 'createdBy', 'created_by')
        return PreciseTestService.create_coverage_from_file(self.session, analysis_id, execution_id, file_path,
                                                           artifact_url, created_by)

    def gate_evaluate(self, analysis_id):
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        return PreciseTestService.evaluate_gate(self.session, analysis_id)

    def gate_result(self, analysis_id):
        if not analysis_id:
            return {}, 'analysisId 为必传参数'
        items, _ = PreciseTestService.list_by_filters(
            self.session, PreciseQualityGate, [PreciseQualityGate.analysis_id == int(analysis_id)], 1, 1,
            PreciseQualityGate.created_time)
        return (self.serialize(items[0], ['is_delete']) if items else {}), ''
