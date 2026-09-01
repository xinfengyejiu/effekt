# encoding: UTF-8
import json
from datetime import date, datetime
from decimal import Decimal

from ..model.bugModel import Bug
from ..model.caseModel import Module, TestCase
from ..model.documentSourceModel import DocumentSource
from ..model.preciseTestModel import (PreciseAnalysis, PreciseChangedFile, PreciseCoverageReport,
                                      PreciseIncrementalCoverage, PreciseQualityGate,
                                      PreciseRecommendation)


class AiReviewContextService(object):
    @staticmethod
    def build_context(session, review):
        source_type = review.source_type or 'manual'
        input_payload = review.input_payload or {}
        context = {
            'sourceType': source_type,
            'sourceId': review.source_id,
            'sourceSummary': {},
            'existingCases': AiReviewContextService._project_cases(session, review.project_id),
            'changeSummary': {},
            'bugSummary': {},
            'coverageSummary': {},
            'rawText': ''
        }
        if source_type == 'manual':
            context.update(AiReviewContextService._manual_context(input_payload))
        elif source_type == 'document':
            context.update(AiReviewContextService._document_context(session, review.source_id))
        elif source_type == 'precise_analysis':
            context.update(AiReviewContextService._precise_context(session, review.source_id))
        elif source_type == 'case':
            context.update(AiReviewContextService._case_context(session, review.source_id))
        elif source_type == 'bug':
            context.update(AiReviewContextService._bug_context(session, review.source_id))
        elif source_type == 'release':
            context.update(AiReviewContextService._release_context(session, input_payload))
        else:
            context['rawText'] = input_payload.get('content') or ''
            context['sourceSummary'] = {'message': '暂不支持的来源类型，已按手工内容评审'}
        return AiReviewContextService._json_safe(context), ''

    @staticmethod
    def _manual_context(input_payload):
        content = input_payload.get('content') or input_payload.get('rawText') or ''
        return {
            'sourceSummary': {'title': input_payload.get('title') or '手工输入', 'contentLength': len(content)},
            'rawText': content
        }

    @staticmethod
    def _document_context(session, source_id):
        item = AiReviewContextService._get_by_id(session, DocumentSource, source_id)
        if not item:
            return {'sourceSummary': {'error': '未查询到需求文档'}, 'rawText': ''}
        content = item.content or ''
        return {
            'sourceSummary': {
                'documentId': item.id,
                'source': item.source,
                'type': item.type,
                'status': item.status,
                'contentLength': len(content)
            },
            'rawText': content[:12000]
        }

    @staticmethod
    def _precise_context(session, analysis_id):
        analysis = AiReviewContextService._get_by_id(session, PreciseAnalysis, analysis_id)
        if not analysis:
            return {'sourceSummary': {'error': '未查询到精准测试分析'}, 'rawText': ''}
        changed_files = session.query(PreciseChangedFile).filter(
            PreciseChangedFile.analysis_id == int(analysis_id),
            PreciseChangedFile.is_delete == 0
        ).order_by(PreciseChangedFile.id.asc()).limit(80).all()
        recommendations = session.query(PreciseRecommendation).filter(
            PreciseRecommendation.analysis_id == int(analysis_id),
            PreciseRecommendation.is_delete == 0
        ).order_by(PreciseRecommendation.id.asc()).limit(80).all()
        coverages = session.query(PreciseCoverageReport).filter(
            PreciseCoverageReport.analysis_id == int(analysis_id),
            PreciseCoverageReport.is_delete == 0
        ).order_by(PreciseCoverageReport.id.desc()).limit(5).all()
        increments = session.query(PreciseIncrementalCoverage).filter(
            PreciseIncrementalCoverage.analysis_id == int(analysis_id),
            PreciseIncrementalCoverage.is_delete == 0
        ).order_by(PreciseIncrementalCoverage.uncovered_changed_line_count.desc()).limit(50).all()
        gate = session.query(PreciseQualityGate).filter(
            PreciseQualityGate.analysis_id == int(analysis_id),
            PreciseQualityGate.is_delete == 0
        ).order_by(PreciseQualityGate.id.desc()).first()
        change_summary = {
            'analysis': AiReviewContextService._to_dict(analysis),
            'changedFiles': [AiReviewContextService._to_dict(item) for item in changed_files],
            'recommendations': [AiReviewContextService._to_dict(item) for item in recommendations],
        }
        coverage_summary = {
            'reports': [AiReviewContextService._to_dict(item) for item in coverages],
            'incrementalFiles': [AiReviewContextService._to_dict(item) for item in increments],
            'gate': AiReviewContextService._to_dict(gate) if gate else {}
        }
        raw_text = AiReviewContextService._compact_text([
            analysis.title,
            analysis.description,
            json.dumps(change_summary, ensure_ascii=False, default=AiReviewContextService._json_default),
            json.dumps(coverage_summary, ensure_ascii=False, default=AiReviewContextService._json_default)
        ])
        return {
            'sourceSummary': {
                'analysisId': analysis.id,
                'analysisNo': analysis.analysis_no,
                'title': analysis.title,
                'riskLevel': analysis.risk_level,
                'status': analysis.status
            },
            'changeSummary': change_summary,
            'coverageSummary': coverage_summary,
            'rawText': raw_text[:16000]
        }

    @staticmethod
    def _case_context(session, case_id):
        row = session.query(TestCase, Module).outerjoin(
            Module, TestCase.module_id == Module.id
        ).filter(TestCase.id == int(case_id), TestCase.is_delete == 0).first() if case_id else None
        if not row:
            return {'sourceSummary': {'error': '未查询到测试用例'}, 'rawText': ''}
        case, module = row
        case_data = AiReviewContextService._to_dict(case)
        case_data['moduleName'] = module.name if module else ''
        raw_text = AiReviewContextService._compact_text([
            case.title,
            case.preconditions,
            case.steps,
            case.expected_results
        ])
        return {'sourceSummary': case_data, 'rawText': raw_text}

    @staticmethod
    def _bug_context(session, bug_id):
        row = session.query(Bug, Module).outerjoin(
            Module, Bug.module_id == Module.id
        ).filter(Bug.id == int(bug_id), Bug.is_delete == 0).first() if bug_id else None
        if not row:
            return {'sourceSummary': {'error': '未查询到缺陷'}, 'bugSummary': {}, 'rawText': ''}
        bug, module = row
        bug_data = AiReviewContextService._to_dict(bug)
        bug_data['moduleName'] = module.name if module else ''
        raw_text = AiReviewContextService._compact_text([
            bug.title,
            bug.description,
            bug.steps,
            bug.solution
        ])
        return {'sourceSummary': bug_data, 'bugSummary': bug_data, 'rawText': raw_text}

    @staticmethod
    def _release_context(session, input_payload):
        analysis_id = input_payload.get('analysisId') or input_payload.get('analysis_id')
        if analysis_id:
            return AiReviewContextService._precise_context(session, analysis_id)
        return {
            'sourceSummary': {'title': input_payload.get('title') or '发布前评审'},
            'rawText': input_payload.get('content') or json.dumps(input_payload, ensure_ascii=False)
        }

    @staticmethod
    def _project_cases(session, project_id):
        if not project_id:
            return []
        rows = session.query(TestCase, Module).outerjoin(
            Module, TestCase.module_id == Module.id
        ).filter(
            TestCase.project_id == int(project_id),
            TestCase.is_delete == 0,
            TestCase.status != 0
        ).order_by(TestCase.priority.asc(), TestCase.id.desc()).limit(30).all()
        result = []
        for case, module in rows:
            item = AiReviewContextService._to_dict(case)
            item['moduleName'] = module.name if module else ''
            result.append(item)
        return result

    @staticmethod
    def _get_by_id(session, model_cls, obj_id):
        if not obj_id:
            return None
        filters = [model_cls.id == int(obj_id)]
        if hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def _to_dict(item):
        if not item:
            return {}
        data = item.to_dict() if hasattr(item, 'to_dict') else dict(item)
        return AiReviewContextService._json_safe(data)

    @staticmethod
    def _compact_text(values):
        return '\n'.join([str(value) for value in values if value not in (None, '')])

    @staticmethod
    def _json_safe(data):
        return json.loads(json.dumps(data, ensure_ascii=False, default=AiReviewContextService._json_default))

    @staticmethod
    def _json_default(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, date):
            return value.strftime('%Y-%m-%d')
        if isinstance(value, Decimal):
            return float(value)
        return str(value)
