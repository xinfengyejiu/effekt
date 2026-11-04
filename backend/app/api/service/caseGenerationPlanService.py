# encoding: UTF-8
"""需求→用例生成计划：大纲、预览候选、覆盖报告。"""
from __future__ import print_function

import json
import logging
import os
import re
import uuid

from app.api.dao.documentSourceDao import DocumentSourceDao
from app.api.model.caseModel import CaseGenerationPlan
from app.api.service.documentSourceService import DocumentSourceService

logger = logging.getLogger(__name__)


class CaseGenerationPlanService(object):

    @staticmethod
    def ensure_table(session):
        # SqlSession.execute 内部会再包一层 text()，这里必须传原始 SQL 字符串
        session.execute('''
            CREATE TABLE IF NOT EXISTS case_generation_plan (
                id BIGSERIAL PRIMARY KEY,
                project_id BIGINT NOT NULL,
                document_ids BIGINT[] DEFAULT '{}'::bigint[],
                status VARCHAR(32) DEFAULT 'outline',
                import_mode VARCHAR(16) DEFAULT 'preview',
                outline JSONB DEFAULT '{}'::jsonb,
                candidate_cases JSONB DEFAULT '[]'::jsonb,
                coverage JSONB DEFAULT '{}'::jsonb,
                template JSONB DEFAULT '{}'::jsonb,
                generation_id VARCHAR(64),
                created_by BIGINT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        session.execute('''
            CREATE INDEX IF NOT EXISTS idx_case_generation_plan_project
            ON case_generation_plan(project_id, status)
        ''')
        session.commit()

    @staticmethod
    def get_by_id(session, plan_id):
        CaseGenerationPlanService.ensure_table(session)
        return session.query(CaseGenerationPlan).filter(CaseGenerationPlan.id == int(plan_id)).first()

    @staticmethod
    def get_latest_by_project(session, project_id):
        """按项目取最近一条生成计划（刷新页面后恢复向导状态）。"""
        CaseGenerationPlanService.ensure_table(session)
        if project_id in (None, ''):
            return None
        return (
            session.query(CaseGenerationPlan)
            .filter(CaseGenerationPlan.project_id == int(project_id))
            .order_by(CaseGenerationPlan.updated_time.desc(), CaseGenerationPlan.id.desc())
            .first()
        )

    @staticmethod
    def to_dict(plan):
        if not plan:
            return {}
        return {
            'id': plan.id,
            'projectId': plan.project_id,
            'documentIds': list(plan.document_ids or []),
            'status': plan.status,
            'importMode': plan.import_mode or 'preview',
            'outline': plan.outline or {},
            'candidateCases': plan.candidate_cases or [],
            'coverage': plan.coverage or {},
            'template': plan.template or {},
            'generationId': plan.generation_id,
            'createdBy': plan.created_by,
            'createdTime': str(plan.created_time) if plan.created_time else None,
            'updatedTime': str(plan.updated_time) if plan.updated_time else None,
        }

    @staticmethod
    def _load_documents_content(session, document_ids):
        combined = []
        failed = []
        for doc_id in document_ids:
            document = DocumentSourceDao.get_by_id(session, doc_id)
            if not document:
                failed.append({'documentId': doc_id, 'error': '文档不存在'})
                continue
            content = document.content
            if document.type in (
                DocumentSourceService.DOCUMENT_TYPE_PDF,
                DocumentSourceService.DOCUMENT_TYPE_EXCEL,
                DocumentSourceService.DOCUMENT_TYPE_MARKDOWN
            ) and not content:
                content = DocumentSourceService.extract_document_content(document)
                if content:
                    DocumentSourceDao.update_by_id(session, doc_id, {
                        'content': content,
                        'status': DocumentSourceService.DOCUMENT_STATUS_PARSED
                    })
            if not content:
                failed.append({'documentId': doc_id, 'error': '文档内容为空'})
                continue
            # 代码PRD偶发存入推理草稿：尽量裁到真实标题后再生成大纲
            try:
                from app.api.service.projectCodePrdService import ProjectCodePrdService
                ai_model = (getattr(document, 'ai_model', None) or '').strip()
                source = (getattr(document, 'source', None) or '')
                if ai_model == 'code-prd' or 'code-prd' in source or ProjectCodePrdService._looks_like_scratchpad(content):
                    content = ProjectCodePrdService._sanitize_prd_markdown(content)
            except Exception:
                pass
            if not (content or '').strip():
                failed.append({'documentId': doc_id, 'error': '文档内容无效（疑似空PRD/推理草稿）'})
                continue
            combined.append(u'【文档ID: {0}】\n{1}\n'.format(doc_id, content))
        return u'\n---\n'.join(combined), failed

    @staticmethod
    def create_outline(session, project_id, document_ids, user_id, template=None, import_mode='preview'):
        from app.api.service.aiService import AIService

        CaseGenerationPlanService.ensure_table(session)
        document_ids = [int(x) for x in (document_ids or []) if str(x).strip()]
        if not document_ids:
            return None, 'documentIds 为必传参数'
        if not project_id:
            return None, 'projectId 为必传参数'

        template = dict(template or {})
        template['project_id'] = int(project_id)
        context_template, context_err = DocumentSourceService._attach_generation_context(session, template)
        if context_err:
            return None, context_err

        merged_content, failed = CaseGenerationPlanService._load_documents_content(session, document_ids)
        if not merged_content:
            return None, u'没有可处理的文档内容: ' + u'; '.join(f.get('error', '') for f in failed)

        outline, err = AIService.generate_requirement_outline(
            merged_content, context_template, user_id=user_id
        )
        if err:
            return None, err

        plan = CaseGenerationPlan(
            project_id=int(project_id),
            document_ids=document_ids,
            status='ready',
            import_mode=(import_mode or 'preview').lower(),
            outline=outline,
            candidate_cases=[],
            coverage={},
            template={
                'priority': context_template.get('priority', 2),
                'case_type': context_template.get('case_type', 1),
                'tags': context_template.get('tags') or ['AI生成'],
                'skill_ids': context_template.get('skill_ids') or [],
                'rule_ids': context_template.get('rule_ids') or [],
            },
            created_by=user_id,
        )
        session.add(plan)
        session.flush()
        session.commit()
        data = CaseGenerationPlanService.to_dict(plan)
        data['failedDocs'] = failed
        return data, ''

    @staticmethod
    def update_plan(session, plan_id, test_points=None, import_mode=None, candidate_cases=None, status=None):
        plan = CaseGenerationPlanService.get_by_id(session, plan_id)
        if not plan:
            return None, '生成计划不存在'
        outline = dict(plan.outline or {})
        if test_points is not None:
            if not isinstance(test_points, list):
                return None, 'testPoints 必须是数组'
            outline['testPoints'] = test_points
            plan.outline = outline
        if import_mode in ('preview', 'auto'):
            plan.import_mode = import_mode
        if candidate_cases is not None:
            if not isinstance(candidate_cases, list):
                return None, 'candidateCases 必须是数组'
            plan.candidate_cases = candidate_cases
        if status:
            plan.status = status
        session.flush()
        session.commit()
        return CaseGenerationPlanService.to_dict(plan), ''

    @staticmethod
    def append_candidates(session_factory, plan_id, cases, test_point_id=''):
        if not plan_id or not session_factory:
            return
        session = session_factory()
        try:
            CaseGenerationPlanService.ensure_table(session)
            plan = session.query(CaseGenerationPlan).filter(CaseGenerationPlan.id == int(plan_id)).first()
            if not plan:
                return
            existing = list(plan.candidate_cases or [])
            for case in cases or []:
                item = dict(case)
                item['selected'] = True if item.get('selected', True) else False
                item['candidateId'] = item.get('candidateId') or uuid.uuid4().hex
                if test_point_id:
                    item['testPointId'] = test_point_id
                elif not item.get('testPointId'):
                    item['testPointId'] = ''
                existing.append(item)
            try:
                from app.api.service.aiCaseQualityService import AiCaseQualityService
                existing = AiCaseQualityService.annotate_near_duplicates(session, plan.project_id, existing)
            except Exception:
                pass
            plan.candidate_cases = existing
            plan.status = 'preview'
            session.commit()
        except Exception as exc:
            logger.error('append_candidates failed: %s', exc)
            try:
                session.rollback()
            except Exception:
                pass
        finally:
            session.close()

    @staticmethod
    def set_generation_meta(session_factory, plan_id, generation_id=None, status=None):
        if not plan_id or not session_factory:
            return
        session = session_factory()
        try:
            CaseGenerationPlanService.ensure_table(session)
            plan = session.query(CaseGenerationPlan).filter(CaseGenerationPlan.id == int(plan_id)).first()
            if not plan:
                return
            if generation_id:
                plan.generation_id = generation_id
            if status:
                plan.status = status
            session.commit()
        except Exception as exc:
            logger.error('set_generation_meta failed: %s', exc)
            try:
                session.rollback()
            except Exception:
                pass
        finally:
            session.close()

    @staticmethod
    def build_coverage(plan):
        outline = plan.outline or {}
        test_points = outline.get('testPoints') or []
        candidates = plan.candidate_cases or []
        covered_ids = set()
        case_links = []
        for case in candidates:
            tp_id = str(case.get('testPointId') or '').strip()
            matched = None
            if tp_id:
                for point in test_points:
                    if str(point.get('id') or '') == tp_id:
                        matched = point
                        covered_ids.add(tp_id)
                        break
            if not matched:
                title = CaseGenerationPlanService._norm(case.get('title'))
                module = CaseGenerationPlanService._norm(case.get('module_name'))
                for point in test_points:
                    pid = str(point.get('id') or '')
                    if pid in covered_ids:
                        continue
                    p_title = CaseGenerationPlanService._norm(point.get('title'))
                    p_module = CaseGenerationPlanService._norm(point.get('modulePath') or point.get('module_path'))
                    if p_title and (p_title in title or title in p_title):
                        if (not p_module) or (not module) or (p_module in module) or (module in p_module):
                            matched = point
                            covered_ids.add(pid)
                            break
            case_links.append({
                'candidateId': case.get('candidateId'),
                'title': case.get('title'),
                'testPointId': (matched or {}).get('id') or case.get('testPointId') or '',
                'matched': bool(matched),
            })

        covered = []
        uncovered = []
        for point in test_points:
            if point.get('selected') is False:
                continue
            item = {
                'id': point.get('id'),
                'title': point.get('title'),
                'modulePath': point.get('modulePath') or point.get('module_path') or '',
                'priority': point.get('priority'),
            }
            if str(point.get('id') or '') in covered_ids:
                covered.append(item)
            else:
                uncovered.append(item)

        selected_points = [p for p in test_points if p.get('selected') is not False]
        report = {
            'totalPoints': len(selected_points),
            'coveredCount': len(covered),
            'uncoveredCount': len(uncovered),
            'candidateCount': len(candidates),
            'covered': covered,
            'uncovered': uncovered,
            'caseLinks': case_links,
        }
        return report

    @staticmethod
    def refresh_coverage(session, plan_id):
        plan = CaseGenerationPlanService.get_by_id(session, plan_id)
        if not plan:
            return None, '生成计划不存在'
        report = CaseGenerationPlanService.build_coverage(plan)
        plan.coverage = report
        session.flush()
        session.commit()
        data = CaseGenerationPlanService.to_dict(plan)
        return data, ''

    @staticmethod
    def import_selected(session, plan_id, user_id, candidate_ids=None):
        plan = CaseGenerationPlanService.get_by_id(session, plan_id)
        if not plan:
            return None, '生成计划不存在'
        document_ids = list(plan.document_ids or [])
        if not document_ids:
            return None, '计划未关联文档'
        candidates = list(plan.candidate_cases or [])
        selected = []
        id_set = set(str(x) for x in (candidate_ids or [])) if candidate_ids else None
        for case in candidates:
            cid = str(case.get('candidateId') or '')
            if id_set is not None:
                if cid not in id_set:
                    continue
            elif not case.get('selected', True):
                continue
            item = dict(case)
            item['selected'] = True
            item['plan_id'] = int(plan.id)
            item['planId'] = int(plan.id)
            if plan.generation_id:
                item['generation_id'] = plan.generation_id
                item['generationId'] = plan.generation_id
            selected.append(item)
        if not selected:
            return None, '没有可导入的候选用例'
        # 导入前近重复标注（不拦截，仅写入候选供前端展示；入库仍按人确认）
        try:
            from app.api.service.aiCaseQualityService import AiCaseQualityService
            selected = AiCaseQualityService.annotate_near_duplicates(session, plan.project_id, selected)
        except Exception:
            pass
        result = DocumentSourceService.import_cases(
            session, document_ids[0], selected, user_id, auto_create_module=True, return_detail=True
        )
        if result.get('error'):
            return None, result.get('error')
        plan.status = 'imported'
        plan.coverage = CaseGenerationPlanService.build_coverage(plan)
        session.flush()
        session.commit()
        data = CaseGenerationPlanService.to_dict(plan)
        data['importResult'] = result
        return data, ''

    @staticmethod
    def selected_test_points(plan):
        outline = (plan.outline or {}) if plan else {}
        points = outline.get('testPoints') or []
        return [p for p in points if p.get('selected') is not False]

    @staticmethod
    def _norm(value):
        return re.sub(r'\s+', '', str(value or '').strip()).lower()
