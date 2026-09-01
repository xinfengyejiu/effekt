# encoding: UTF-8
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal

from ..controller.baseCrudController import BaseCrudController
from ..dao.aiReviewDao import AiReviewDao
from ..model.aiReviewModel import AiTestReview, AiTestReviewCaseSuggestion, AiTestReviewFinding
from ..model.caseModel import Module, TestCase
from .aiCommonService import AiCommonService
from .aiReviewContextService import AiReviewContextService
from .aiService import AIService
from .caseService import CaseService


logger = logging.getLogger(__name__)


class AiReviewService(object):
    VALID_REVIEW_TYPES = {'requirement', 'change', 'case', 'bug', 'release'}
    VALID_SOURCE_TYPES = {'manual', 'document', 'precise_analysis', 'case', 'bug', 'release'}
    VALID_FINDING_STATUS = {'open', 'accepted', 'ignored', 'fixed'}

    @staticmethod
    def create_review(session, req_data, user_id=None):
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        review_type = AiCommonService.get(req_data, 'reviewType', 'review_type')
        source_type = AiCommonService.get(req_data, 'sourceType', 'source_type', default='manual')
        title = AiCommonService.get(req_data, 'title')
        if not project_id or not review_type or not title:
            return 0, 'projectId、reviewType、title 为必传参数'
        if review_type not in AiReviewService.VALID_REVIEW_TYPES:
            return 0, '不支持的评审类型'
        if source_type not in AiReviewService.VALID_SOURCE_TYPES:
            return 0, '不支持的来源类型'
        data = {
            'review_no': AiReviewService._gen_no(),
            'project_id': int(project_id),
            'review_type': review_type,
            'source_type': source_type,
            'source_id': AiReviewService._to_int(AiCommonService.get(req_data, 'sourceId', 'source_id')),
            'title': title,
            'input_payload': AiCommonService.get(req_data, 'inputPayload', 'input_payload', default={}),
            'status': 'pending',
            'created_by': user_id,
            'is_delete': 0
        }
        AiCommonService.fill_product_project_names(session, data, req_data)
        obj, err_msg = AiReviewDao.create(session, AiTestReview, data)
        if err_msg:
            return 0, err_msg
        return obj.id, ''

    @staticmethod
    def list_reviews(session, req_data):
        items, total = AiReviewDao.list_reviews(session, AiTestReview, req_data)
        return {'list': BaseCrudController.serialize_list(items), 'total': total}

    @staticmethod
    def review_detail(session, review_id):
        review = AiReviewDao.get_by_id(session, AiTestReview, review_id)
        if not review:
            return {}, '未查询到AI测试评审'
        data = BaseCrudController.serialize(review)
        data['findings'] = BaseCrudController.serialize_list(AiReviewDao.get_findings(session, review.id))
        case_suggestions = BaseCrudController.serialize_list(AiReviewDao.get_case_suggestions(session, review.id))
        AiReviewService._enrich_case_suggestion_refs(session, case_suggestions)
        data['caseSuggestions'] = case_suggestions
        return data, ''

    @staticmethod
    def execute_review(session, review_id):
        review = AiReviewDao.get_by_id(session, AiTestReview, review_id)
        if not review:
            return {}, '未查询到AI测试评审'
        AiReviewDao.update_by_id(session, AiTestReview, review.id, {'status': 'running', 'error_message': ''})
        context_payload, err_msg = AiReviewContextService.build_context(session, review)
        if err_msg:
            AiReviewDao.update_by_id(session, AiTestReview, review.id, {'status': 'failed', 'error_message': err_msg})
            return {}, err_msg
        result, ai_err = AiReviewService._request_ai_review(review, context_payload)
        if ai_err:
            result = AiReviewService._fallback_review(review, context_payload, ai_err)
        normalized = AiReviewService._normalize_result(result)
        AiReviewDao.soft_delete_by_review(session, AiTestReviewFinding, review.id)
        AiReviewDao.soft_delete_by_review(session, AiTestReviewCaseSuggestion, review.id)
        findings = AiReviewService._finding_rows(review.id, normalized)
        finding_objs, err_msg = AiReviewDao.batch_create(session, AiTestReviewFinding, findings)
        if err_msg:
            AiReviewDao.update_by_id(session, AiTestReview, review.id, {'status': 'failed', 'error_message': err_msg})
            return {}, err_msg
        suggestions = AiReviewService._case_suggestion_rows(review.id, normalized, finding_objs)
        _, err_msg = AiReviewDao.batch_create(session, AiTestReviewCaseSuggestion, suggestions)
        if err_msg:
            AiReviewDao.update_by_id(session, AiTestReview, review.id, {'status': 'failed', 'error_message': err_msg})
            return {}, err_msg
        update_info = {
            'status': 'success',
            'context_payload': context_payload,
            'result_summary': normalized,
            'risk_level': normalized.get('riskLevel') or normalized.get('risk_level'),
            'score': int(normalized.get('score') or 0),
            'error_message': ai_err or ''
        }
        AiReviewDao.update_by_id(session, AiTestReview, review.id, update_info)
        return AiReviewService.review_detail(session, review.id)

    @staticmethod
    def confirm_review(session, req_data, user_id=None):
        review_id = AiCommonService.get(req_data, 'reviewId', 'review_id', 'id')
        if not review_id:
            return 0, 'reviewId 为必传参数'
        review = AiReviewDao.get_by_id(session, AiTestReview, review_id)
        if not review:
            return 0, '未查询到AI测试评审'
        summary = review.result_summary or {}
        summary['confirmInfo'] = {
            'confirmedBy': user_id,
            'confirmedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'comment': AiCommonService.get(req_data, 'comment', default='')
        }
        return AiReviewDao.update_by_id(session, AiTestReview, review.id, {'status': 'confirmed', 'result_summary': summary})

    @staticmethod
    def update_finding(session, req_data):
        finding_id = AiCommonService.get(req_data, 'findingId', 'finding_id', 'id')
        status = AiCommonService.get(req_data, 'status')
        if not finding_id or not status:
            return 0, 'findingId、status 为必传参数'
        if status not in AiReviewService.VALID_FINDING_STATUS:
            return 0, '不支持的风险项状态'
        return AiReviewDao.update_by_id(session, AiTestReviewFinding, finding_id, {'status': status})

    @staticmethod
    def import_suggested_case(session, req_data, user_id=None):
        suggestion_id = AiCommonService.get(req_data, 'suggestionId', 'suggestion_id', 'id')
        if not suggestion_id:
            return 0, 'suggestionId 为必传参数'
        suggestion = AiReviewDao.get_by_id(session, AiTestReviewCaseSuggestion, suggestion_id)
        if not suggestion:
            return 0, '未查询到建议用例'
        review = AiReviewDao.get_by_id(session, AiTestReview, suggestion.review_id)
        if not review:
            return 0, '未查询到AI测试评审'
        module_id = AiReviewService._find_module_id(session, review.project_id, suggestion.module_name)
        tags = AiReviewService._normalize_tags(suggestion.tags)
        if 'AI评审' not in tags:
            tags.append('AI评审')
        add_info = {
            'project_id': review.project_id,
            'module_id': module_id,
            'case_key': CaseService.next_case_key(session, review.project_id, module_id, review.product_id),
            'title': suggestion.case_title,
            'preconditions': suggestion.preconditions or '',
            'steps': suggestion.steps or '',
            'expected_results': suggestion.expected_results or '',
            'priority': int(suggestion.priority if suggestion.priority is not None else 2),
            'case_type': int(suggestion.case_type if suggestion.case_type is not None else 1),
            'tags': tags,
            'status': 1,
            'is_auto': 0,
            'is_ai_generated': 1,
            'created_by': user_id,
            'is_delete': 0
        }
        case_id, err_msg = CaseService.create(session, TestCase, add_info)
        if err_msg:
            return 0, err_msg
        AiReviewDao.update_by_id(session, AiTestReviewCaseSuggestion, suggestion.id, {
            'created_case_id': case_id,
            'matched_case_id': case_id,
            'action_status': 'imported'
        })
        return case_id, ''

    @staticmethod
    def link_existing_case(session, req_data):
        suggestion_id = AiCommonService.get(req_data, 'suggestionId', 'suggestion_id', 'id')
        case_ref = AiCommonService.get(req_data, 'caseId', 'case_id', 'caseKey', 'case_key')
        if not suggestion_id or not case_ref:
            return 0, 'suggestionId、用例编号或ID 为必传参数'
        suggestion = AiReviewDao.get_by_id(session, AiTestReviewCaseSuggestion, suggestion_id)
        if not suggestion:
            return 0, '未查询到建议用例'
        review = AiReviewDao.get_by_id(session, AiTestReview, suggestion.review_id)
        if not review:
            return 0, '未查询到AI测试评审'
        case = AiReviewService._find_case_by_ref(session, review.project_id, case_ref)
        if not case:
            return 0, '未查询到测试用例'
        return AiReviewDao.update_by_id(session, AiTestReviewCaseSuggestion, suggestion_id, {
            'matched_case_id': int(case.id),
            'action_status': 'linked'
        })

    @staticmethod
    def _request_ai_review(review, context_payload):
        from config.ai_config import AIConfig

        tasks = AiReviewService._build_review_agent_tasks(context_payload)
        if not tasks:
            tasks = [{
                'index': 1,
                'title': '完整上下文评审',
                'focus': '完整上下文',
                'context': context_payload
            }]
        review_concurrency = max(1, int(getattr(AIConfig, 'REVIEW_AGENT_CONCURRENCY', 3) or 3))
        max_workers = min(review_concurrency, max(1, len(tasks)))
        results = []
        errors = []
        logger.info('AI测试评审启动subagent: review_id=%s, task_count=%s, agent_count=%s', review.id, len(tasks), max_workers)

        def run_agent(task):
            prompt = AiReviewService._build_review_agent_prompt(review, task)
            result, err_msg = AIService.request_json(
                prompt,
                'AI测试评审-{}'.format(task.get('title') or task.get('index')),
                read_timeout=240,
                max_retries=1,
                max_tokens=3072,
                temperature=0.2,
                system_prompt='你是资深测试架构师。必须只输出可解析JSON，不要输出Markdown或解释文本。'
            )
            if err_msg or not isinstance(result, dict):
                raise RuntimeError(err_msg or 'AI测试评审结果格式错误')
            normalized = AiReviewService._normalize_result(result)
            normalized['_agentTitle'] = task.get('title') or ''
            return normalized

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(run_agent, task): task for task in tasks}
            for future in as_completed(future_map):
                task = future_map[future]
                try:
                    results.append(future.result())
                except Exception as err:
                    err_msg = '{}: {}'.format(task.get('title') or '评审agent', str(err))
                    errors.append(err_msg)
                    logger.warning('AI测试评审subagent失败: review_id=%s, %s', review.id, err_msg)

        if results:
            merged = AiReviewService._merge_review_agent_results(review, context_payload, results, errors)
            return merged, ''
        return {}, '; '.join(errors) or 'AI测试评审全部agent失败'

    @staticmethod
    def _build_review_agent_tasks(context_payload):
        tasks = []
        index = 1
        from config.ai_config import AIConfig

        source_summary = context_payload.get('sourceSummary') or {}
        raw_text = context_payload.get('rawText') or ''
        chunk_size = max(2000, int(getattr(AIConfig, 'REVIEW_AGENT_CHUNK_SIZE', 6000) or 6000))
        for part_index, text in enumerate(AiReviewService._split_text(raw_text, chunk_size), 1):
            tasks.append({
                'index': index,
                'title': '来源内容评审{}'.format(part_index),
                'focus': '需求/变更/来源正文的风险、歧义和遗漏测试点',
                'context': {
                    'sourceType': context_payload.get('sourceType'),
                    'sourceId': context_payload.get('sourceId'),
                    'sourceSummary': source_summary,
                    'rawText': text
                }
            })
            index += 1
        existing_cases = context_payload.get('existingCases') or []
        if existing_cases:
            for part_index, cases in enumerate(AiReviewService._chunk_list(existing_cases, 10), 1):
                tasks.append({
                    'index': index,
                    'title': '已有用例覆盖评审{}'.format(part_index),
                    'focus': '已有用例覆盖度、重复、缺失和建议补充用例',
                    'context': {
                        'sourceSummary': source_summary,
                        'existingCases': cases
                    }
                })
                index += 1
        change_summary = context_payload.get('changeSummary') or {}
        if change_summary:
            tasks.append({
                'index': index,
                'title': '变更影响评审',
                'focus': '代码变更影响面、回归范围和阻断风险',
                'context': {
                    'sourceSummary': source_summary,
                    'changeSummary': AiReviewService._limit_json_payload(change_summary, 12000)
                }
            })
            index += 1
        coverage_summary = context_payload.get('coverageSummary') or {}
        if coverage_summary:
            tasks.append({
                'index': index,
                'title': '覆盖率风险评审',
                'focus': '覆盖率门禁、增量未覆盖代码和自动化补齐建议',
                'context': {
                    'sourceSummary': source_summary,
                    'coverageSummary': AiReviewService._limit_json_payload(coverage_summary, 12000)
                }
            })
            index += 1
        bug_summary = context_payload.get('bugSummary') or {}
        if bug_summary:
            tasks.append({
                'index': index,
                'title': '缺陷风险评审',
                'focus': '缺陷复现、修复验证、回归和数据风险',
                'context': {
                    'sourceSummary': source_summary,
                    'bugSummary': bug_summary
                }
            })
        return tasks[:8]

    @staticmethod
    def _build_review_agent_prompt(review, task):
        return '''你是资深测试架构师，请作为并行评审subagent，只基于当前分片上下文输出AI测试评审JSON，不要输出额外文字。
评审类型：{review_type}
来源类型：{source_type}
标题：{title}
当前agent：{agent_title}
评审重点：{focus}
分片上下文：
{context}

必须输出如下JSON结构：
{{
  "conclusion": "通过/建议补充后通过/风险较高不建议通过",
  "riskLevel": "low/medium/high/critical",
  "score": 0,
  "summary": "当前分片评审摘要",
  "missingTestPoints": ["遗漏测试点"],
  "riskFindings": [
    {{
      "findingType": "missing_case/risk/ambiguity/dependency/data/automation/performance/security",
      "riskLevel": "low/medium/high/critical",
      "moduleName": "模块",
      "apiPath": "接口或空字符串",
      "title": "风险标题",
      "description": "风险描述",
      "suggestion": "处理建议",
      "evidence": {{"agentTitle": "{agent_title}"}}
    }}
  ],
  "suggestedCases": [
    {{
      "moduleName": "模块",
      "caseTitle": "用例标题",
      "preconditions": "前置条件",
      "steps": "操作步骤",
      "expectedResults": "预期结果",
      "priority": 2,
      "caseType": 1,
      "tags": ["AI评审"]
    }}
  ],
  "recommendedActions": ["后续动作"],
  "blockSuggestion": "是否建议阻断及原因"
}}
'''.format(
            review_type=review.review_type,
            source_type=review.source_type,
            title=review.title,
            agent_title=task.get('title') or '评审agent',
            focus=task.get('focus') or '测试评审',
            context=json.dumps(task.get('context') or {}, ensure_ascii=False, default=AiReviewService._json_default)[:12000]
        )

    @staticmethod
    def _merge_review_agent_results(review, context_payload, results, errors=None):
        risk_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        max_risk = 'low'
        scores = []
        summaries = []
        missing_points = []
        findings = []
        suggested_cases = []
        actions = []
        block_suggestions = []
        for result in results:
            risk = str(result.get('riskLevel') or result.get('risk_level') or 'medium').lower()
            if risk_order.get(risk, 2) > risk_order.get(max_risk, 1):
                max_risk = risk
            try:
                scores.append(int(result.get('score')))
            except (TypeError, ValueError):
                pass
            if result.get('summary'):
                summaries.append('{}：{}'.format(result.get('_agentTitle') or '评审agent', result.get('summary')))
            missing_points.extend(result.get('missingTestPoints') or [])
            for item in result.get('riskFindings') or []:
                finding = dict(item)
                evidence = finding.get('evidence') or {}
                if not isinstance(evidence, dict):
                    evidence = {'rawEvidence': evidence}
                evidence.setdefault('agentTitle', result.get('_agentTitle') or '')
                finding['evidence'] = evidence
                findings.append(finding)
            suggested_cases.extend(result.get('suggestedCases') or [])
            actions.extend(result.get('recommendedActions') or [])
            if result.get('blockSuggestion'):
                block_suggestions.append(result.get('blockSuggestion'))
        if errors:
            actions.append('部分评审agent失败，建议人工复核失败分片：{}'.format('; '.join(errors[:2])))
        return {
            'conclusion': AiReviewService._conclusion_by_risk(max_risk),
            'riskLevel': max_risk,
            'score': min(scores) if scores else (60 if max_risk in ('high', 'critical') else 75),
            'summary': '；'.join(summaries[:6]) or '并行评审完成，共{}个agent返回结果。'.format(len(results)),
            'missingTestPoints': AiReviewService._dedupe_text_list(missing_points, 30),
            'riskFindings': AiReviewService._dedupe_items(findings, 'title', 50),
            'suggestedCases': AiReviewService._dedupe_items(suggested_cases, 'caseTitle', 40),
            'recommendedActions': AiReviewService._dedupe_text_list(actions, 20),
            'blockSuggestion': '；'.join(AiReviewService._dedupe_text_list(block_suggestions, 5))
        }

    @staticmethod
    def _fallback_review(review, context_payload, reason=''):
        raw_text = context_payload.get('rawText') or ''
        existing_cases = context_payload.get('existingCases') or []
        change_summary = context_payload.get('changeSummary') or {}
        coverage_summary = context_payload.get('coverageSummary') or {}
        risk_level = 'medium'
        score = 75
        findings = []
        if change_summary.get('changedFiles'):
            findings.append({
                'findingType': 'risk',
                'riskLevel': 'high',
                'moduleName': '变更影响模块',
                'apiPath': '',
                'title': '代码变更需要补充影响面验证',
                'description': '当前评审来源包含代码变更，需要确认变更文件对应的接口、模块和回归用例是否覆盖。',
                'suggestion': '结合精准测试推荐用例执行P0/P1回归，并检查未覆盖变更行。',
                'evidence': {'changedFileCount': len(change_summary.get('changedFiles') or [])}
            })
            risk_level = 'high'
            score = 68
        if coverage_summary.get('incrementalFiles'):
            findings.append({
                'findingType': 'automation',
                'riskLevel': 'high',
                'moduleName': '增量覆盖率',
                'apiPath': '',
                'title': '存在增量覆盖率风险',
                'description': '覆盖率报告中存在需要关注的增量文件，请确认未覆盖代码是否包含核心逻辑。',
                'suggestion': '补充自动化或手工用例覆盖未覆盖变更行。',
                'evidence': {'fileCount': len(coverage_summary.get('incrementalFiles') or [])}
            })
        if not existing_cases:
            findings.append({
                'findingType': 'missing_case',
                'riskLevel': 'medium',
                'moduleName': '',
                'apiPath': '',
                'title': '项目下未查询到可复用测试用例',
                'description': '当前项目缺少可参考的已有用例，评审结论可信度会下降。',
                'suggestion': '先补充核心流程、异常分支、权限边界和数据校验用例。',
                'evidence': {}
            })
        if not findings:
            findings.append({
                'findingType': 'risk',
                'riskLevel': 'medium',
                'moduleName': '',
                'apiPath': '',
                'title': '需要人工确认测试点完整性',
                'description': 'AI服务不可用或返回异常，已生成本地兜底评审。',
                'suggestion': '人工检查需求主流程、异常流程、权限边界和数据准备。',
                'evidence': {'fallbackReason': reason}
            })
        suggested_cases = [{
            'moduleName': findings[0].get('moduleName') or '',
            'caseTitle': '{}-核心流程与异常分支评审补充用例'.format(review.title[:80]),
            'preconditions': '测试环境可用，测试数据已准备。',
            'steps': '1. 执行主流程。\n2. 执行异常输入。\n3. 执行权限不足或边界数据场景。',
            'expectedResults': '主流程成功，异常场景提示清晰，权限和数据边界符合预期。',
            'priority': 1 if risk_level == 'high' else 2,
            'caseType': 1,
            'tags': ['AI评审', review.review_type]
        }]
        return {
            'conclusion': '建议补充后通过' if risk_level != 'critical' else '风险较高不建议通过',
            'riskLevel': risk_level,
            'score': score,
            'summary': 'AI服务暂不可用，平台已基于评审上下文生成兜底结论。输入文本长度{}，已有用例{}条。'.format(len(raw_text), len(existing_cases)),
            'missingTestPoints': ['主流程', '异常分支', '权限边界', '数据校验'],
            'riskFindings': findings,
            'suggestedCases': suggested_cases,
            'recommendedActions': ['补充建议用例', '执行核心回归', '确认高风险项处理状态'],
            'blockSuggestion': '如存在高风险变更或未覆盖代码，建议补充验证后再通过评审。'
        }

    @staticmethod
    def _normalize_result(result):
        data = dict(result or {})
        data.setdefault('conclusion', '建议补充后通过')
        data.setdefault('riskLevel', data.get('risk_level') or 'medium')
        try:
            data['score'] = int(data.get('score') if data.get('score') is not None else 70)
        except (TypeError, ValueError):
            data['score'] = 70
        data.setdefault('summary', '')
        data.setdefault('missingTestPoints', [])
        data.setdefault('riskFindings', [])
        data.setdefault('suggestedCases', [])
        data.setdefault('recommendedActions', [])
        data.setdefault('blockSuggestion', '')
        return AiReviewService._json_safe(data)

    @staticmethod
    def _finding_rows(review_id, result):
        rows = []
        for item in result.get('riskFindings') or []:
            rows.append({
                'review_id': int(review_id),
                'finding_type': item.get('findingType') or item.get('finding_type') or 'risk',
                'risk_level': item.get('riskLevel') or item.get('risk_level') or result.get('riskLevel') or 'medium',
                'module_name': item.get('moduleName') or item.get('module_name') or '',
                'api_path': item.get('apiPath') or item.get('api_path') or '',
                'title': item.get('title') or '未命名风险项',
                'description': item.get('description') or '',
                'suggestion': item.get('suggestion') or '',
                'evidence_json': item.get('evidence') or item.get('evidenceJson') or item.get('evidence_json') or {},
                'status': 'open',
                'is_delete': 0
            })
        for point in result.get('missingTestPoints') or []:
            rows.append({
                'review_id': int(review_id),
                'finding_type': 'missing_case',
                'risk_level': result.get('riskLevel') or 'medium',
                'module_name': '',
                'api_path': '',
                'title': str(point)[:255],
                'description': str(point),
                'suggestion': '补充对应测试点和回归用例',
                'evidence_json': {},
                'status': 'open',
                'is_delete': 0
            })
        return rows

    @staticmethod
    def _case_suggestion_rows(review_id, result, finding_objs):
        rows = []
        default_finding_id = finding_objs[0].id if finding_objs else None
        for item in result.get('suggestedCases') or []:
            rows.append({
                'review_id': int(review_id),
                'finding_id': item.get('findingId') or item.get('finding_id') or default_finding_id,
                'module_name': item.get('moduleName') or item.get('module_name') or '',
                'case_title': item.get('caseTitle') or item.get('case_title') or item.get('title') or 'AI评审建议用例',
                'preconditions': item.get('preconditions') or '',
                'steps': item.get('steps') or '',
                'expected_results': item.get('expectedResults') or item.get('expected_results') or '',
                'priority': int(item.get('priority') if item.get('priority') is not None else 2),
                'case_type': int(item.get('caseType') or item.get('case_type') or 1),
                'tags': AiReviewService._normalize_tags(item.get('tags')),
                'action_status': 'pending',
                'is_delete': 0
            })
        return rows

    @staticmethod
    def _enrich_case_suggestion_refs(session, rows):
        case_ids = set()
        for row in rows or []:
            for key in ('matched_case_id', 'matchedCaseId', 'created_case_id', 'createdCaseId'):
                case_id = AiReviewService._to_int(row.get(key))
                if case_id:
                    case_ids.add(case_id)
        if not case_ids:
            return rows

        cases = session.query(TestCase).filter(
            TestCase.id.in_(list(case_ids)),
            TestCase.is_delete == 0
        ).all()
        case_map = {int(case.id): case for case in cases}
        for row in rows or []:
            for prefix in ('matched', 'created'):
                case_id = (
                    AiReviewService._to_int(row.get('{}_case_id'.format(prefix))) or
                    AiReviewService._to_int(row.get('{}CaseId'.format(prefix)))
                )
                case = case_map.get(case_id) if case_id else None
                if not case:
                    continue
                row['{}_case_key'.format(prefix)] = case.case_key or ''
                row['{}CaseKey'.format(prefix)] = case.case_key or ''
                row['{}_case_title'.format(prefix)] = case.title or ''
                row['{}CaseTitle'.format(prefix)] = case.title or ''
        return rows

    @staticmethod
    def _find_case_by_ref(session, project_id, case_ref):
        if not case_ref:
            return None
        case_ref = str(case_ref).strip()
        if not case_ref:
            return None
        filters = [TestCase.project_id == int(project_id), TestCase.is_delete == 0]
        if str(case_ref).isdigit():
            return session.query(TestCase).filter(
                TestCase.id == int(case_ref),
                *filters
            ).first()
        return session.query(TestCase).filter(
            TestCase.case_key == str(case_ref),
            *filters
        ).first()

    @staticmethod
    def _find_module_id(session, project_id, module_name):
        if not module_name:
            return None
        module = session.query(Module).filter(
            Module.project_id == int(project_id),
            Module.name == module_name,
            Module.is_delete == 0
        ).first()
        return module.id if module else None

    @staticmethod
    def _normalize_tags(tags):
        if tags is None:
            return []
        if isinstance(tags, str):
            return [item.strip() for item in tags.split(',') if item.strip()]
        if isinstance(tags, list):
            return [str(item) for item in tags if item not in (None, '')]
        return []

    @staticmethod
    def _split_text(text, size):
        text = str(text or '').strip()
        if not text:
            return []
        size = max(1000, int(size or 6000))
        return [text[index:index + size] for index in range(0, len(text), size)]

    @staticmethod
    def _chunk_list(items, size):
        items = list(items or [])
        size = max(1, int(size or 10))
        return [items[index:index + size] for index in range(0, len(items), size)]

    @staticmethod
    def _limit_json_payload(payload, limit):
        text = json.dumps(payload or {}, ensure_ascii=False, default=AiReviewService._json_default)
        if len(text) <= limit:
            return payload or {}
        return {'truncated': True, 'content': text[:limit]}

    @staticmethod
    def _dedupe_text_list(items, limit):
        result = []
        seen = set()
        for item in items or []:
            text = str(item or '').strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
            if len(result) >= limit:
                break
        return result

    @staticmethod
    def _dedupe_items(items, key, limit):
        result = []
        seen = set()
        for item in items or []:
            if not isinstance(item, dict):
                continue
            value = item.get(key) or item.get(AiReviewService._camel_to_snake(key)) or item.get('title') or json.dumps(item, ensure_ascii=False, default=AiReviewService._json_default)[:120]
            marker = str(value or '').strip()
            if not marker or marker in seen:
                continue
            seen.add(marker)
            result.append(item)
            if len(result) >= limit:
                break
        return result

    @staticmethod
    def _conclusion_by_risk(risk_level):
        risk = str(risk_level or 'medium').lower()
        if risk == 'critical':
            return '风险较高不建议通过'
        if risk == 'high':
            return '建议补充后通过'
        return '通过' if risk == 'low' else '建议补充后通过'

    @staticmethod
    def _camel_to_snake(name):
        result = []
        for char in str(name or ''):
            if char.isupper() and result:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)

    @staticmethod
    def _gen_no():
        return 'AIR{}'.format(datetime.now().strftime('%Y%m%d%H%M%S%f')[:20])

    @staticmethod
    def _to_int(value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _json_safe(data):
        return json.loads(json.dumps(data, ensure_ascii=False, default=AiReviewService._json_default))

    @staticmethod
    def _json_default(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, Decimal):
            return float(value)
        return str(value)
