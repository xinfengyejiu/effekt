# encoding: UTF-8
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy import or_

from ..controller.baseCrudController import BaseCrudController
from ..dao.testAssetGovernanceDao import TestAssetGovernanceDao
from ..model.aiReviewModel import AiTestReview, AiTestReviewCaseSuggestion
from ..model.bugModel import Bug
from ..model.caseModel import Module, TestCase
from ..model.planModel import PlanCase
from ..model.preciseTestModel import PreciseRecommendation
from ..model.testAssetGovernanceModel import TestAssetAction, TestAssetIssue, TestAssetScan
from .aiCommonService import AiCommonService
from .aiService import AIService


class TestAssetGovernanceService(object):
    VALID_ISSUE_STATUS = {'open', 'accepted', 'ignored', 'fixed', 'reopened'}
    VALID_ACTION_TYPES = {
        'keep', 'merge', 'improve', 'deprecate', 'accept_suggestion',
        'ignore', 'mark_fixed', 'reopen'
    }
    DUPLICATE_THRESHOLD_MIN = 0.9
    SEVERITY_DEDUCTION = {'critical': 20, 'high': 12, 'medium': 6, 'low': 2}

    @staticmethod
    def create_scan(session, req_data, user_id=None):
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        title = AiCommonService.get(req_data, 'title')
        if not project_id or not title:
            return 0, 'projectId、title 为必传参数'

        options = TestAssetGovernanceService._normalize_options(req_data)
        data = {
            'scan_no': AiCommonService.gen_no('TAG'),
            'project_id': int(project_id),
            'title': title,
            'scan_type': AiCommonService.get(req_data, 'scanType', 'scan_type', default='full'),
            'options_json': options,
            'summary_json': {},
            'status': 'pending',
            'created_by': user_id,
            'is_delete': 0
        }
        AiCommonService.fill_product_project_names(session, data, req_data)
        obj, err_msg = TestAssetGovernanceDao.create(session, TestAssetScan, data)
        if err_msg:
            return 0, err_msg
        return obj.id, ''

    @staticmethod
    def list_scans(session, req_data):
        items, total = TestAssetGovernanceDao.list_scans(session, TestAssetScan, req_data)
        return {'list': BaseCrudController.serialize_list(items), 'total': total}

    @staticmethod
    def scan_detail(session, scan_id):
        scan = TestAssetGovernanceDao.get_by_id(session, TestAssetScan, scan_id)
        if not scan:
            return {}, '未查询到测试资产治理扫描'
        data = BaseCrudController.serialize(scan)
        issues = TestAssetGovernanceDao.get_issues(session, scan.id)
        issue_rows = BaseCrudController.serialize_list(issues)
        TestAssetGovernanceService._enrich_issue_case_refs(session, issue_rows)
        actions = TestAssetGovernanceDao.get_actions_by_issue_ids(session, [item.id for item in issues])
        actions_by_issue = defaultdict(list)
        for action in BaseCrudController.serialize_list(actions):
            actions_by_issue[int(action.get('issue_id'))].append(action)
        for issue in issue_rows:
            issue['actions'] = actions_by_issue.get(int(issue.get('id')), [])
        data['issues'] = issue_rows
        data['actions'] = BaseCrudController.serialize_list(actions)
        return data, ''

    @staticmethod
    def list_issues(session, req_data):
        items, total = TestAssetGovernanceDao.list_issues(session, req_data)
        rows = BaseCrudController.serialize_list(items)
        TestAssetGovernanceService._enrich_issue_case_refs(session, rows)
        return {'list': rows, 'total': total}

    @staticmethod
    def execute_scan(session, scan_id):
        scan = TestAssetGovernanceDao.get_by_id(session, TestAssetScan, scan_id)
        if not scan:
            return {}, '未查询到测试资产治理扫描'

        now = datetime.now()
        TestAssetGovernanceDao.update_by_id(session, TestAssetScan, scan.id, {
            'status': 'running',
            'error_message': '',
            'started_time': now,
            'finished_time': None
        })
        try:
            _, err_msg = TestAssetGovernanceDao.soft_delete_by_scan(session, scan.id)
            if err_msg:
                raise RuntimeError(err_msg)

            context = TestAssetGovernanceService._load_context(session, scan)
            issues = []
            issues.extend(TestAssetGovernanceService._detect_duplicate_cases(context))
            issues.extend(TestAssetGovernanceService._detect_weak_cases(context))
            issues.extend(TestAssetGovernanceService._detect_stale_cases(context))
            issues.extend(TestAssetGovernanceService._detect_coverage_gaps(context))
            issues.extend(TestAssetGovernanceService._detect_ai_suggestions(context))
            issues = TestAssetGovernanceService._json_safe(issues)

            _, err_msg = TestAssetGovernanceDao.batch_create(session, TestAssetIssue, issues)
            if err_msg:
                raise RuntimeError(err_msg)

            summary = TestAssetGovernanceService._build_summary(context, issues)
            summary = TestAssetGovernanceService._enhance_summary_with_ai(summary, issues)
            summary = TestAssetGovernanceService._json_safe(summary)
            TestAssetGovernanceDao.update_by_id(session, TestAssetScan, scan.id, {
                'summary_json': summary,
                'health_score': int(summary.get('healthScore') or summary.get('health_score') or 0),
                'status': 'success',
                'finished_time': datetime.now(),
                'error_message': ''
            })
            return TestAssetGovernanceService.scan_detail(session, scan.id)
        except Exception as exc:
            TestAssetGovernanceDao.update_by_id(session, TestAssetScan, scan.id, {
                'status': 'failed',
                'error_message': str(exc),
                'finished_time': datetime.now()
            })
            return {}, str(exc)

    @staticmethod
    def update_issue(session, req_data, user_id=None):
        issue_id = AiCommonService.get(req_data, 'issueId', 'issue_id', 'id')
        status = AiCommonService.get(req_data, 'status', 'actionStatus', 'action_status')
        if not issue_id or not status:
            return 0, 'issueId、status 为必传参数'
        if status not in TestAssetGovernanceService.VALID_ISSUE_STATUS:
            return 0, '不支持的问题状态'
        issue = TestAssetGovernanceDao.get_by_id(session, TestAssetIssue, issue_id)
        if not issue:
            return 0, '未查询到治理问题'

        update_info = {'action_status': status}
        if status in ('ignored', 'fixed'):
            update_info['resolved_by'] = user_id
            update_info['resolved_time'] = datetime.now()
        elif status in ('open', 'reopened'):
            update_info['resolved_by'] = None
            update_info['resolved_time'] = None
        update_id, err_msg = TestAssetGovernanceDao.update_by_id(session, TestAssetIssue, issue.id, update_info)
        if err_msg:
            return 0, err_msg

        action_type = {
            'open': 'reopen',
            'reopened': 'reopen',
            'accepted': 'improve',
            'ignored': 'ignore',
            'fixed': 'mark_fixed'
        }.get(status, 'improve')
        TestAssetGovernanceDao.create(session, TestAssetAction, {
            'issue_id': int(issue.id),
            'action_type': action_type,
            'action_payload': {
                'status': status,
                'comment': AiCommonService.get(req_data, 'comment', default='')
            },
            'result_payload': {'issueStatus': status},
            'status': 'success',
            'created_by': user_id
        })
        return update_id, ''

    @staticmethod
    def apply_action(session, req_data, user_id=None):
        issue_id = AiCommonService.get(req_data, 'issueId', 'issue_id', 'id')
        action_type = AiCommonService.get(req_data, 'actionType', 'action_type')
        if not issue_id or not action_type:
            return 0, 'issueId、actionType 为必传参数'
        if action_type not in TestAssetGovernanceService.VALID_ACTION_TYPES:
            return 0, '不支持的治理动作'
        issue = TestAssetGovernanceDao.get_by_id(session, TestAssetIssue, issue_id)
        if not issue:
            return 0, '未查询到治理问题'

        result_payload = {}
        action_status = TestAssetGovernanceService._status_after_action(action_type)
        if action_type == 'deprecate':
            case_ref = AiCommonService.get(req_data, 'caseId', 'case_id', 'caseKey', 'case_key')
            if not case_ref:
                return 0, 'deprecate 动作需要用例编号或ID'
            case_ref = str(case_ref).strip()
            related_ids = [str(item) for item in (issue.related_case_ids or [])]
            case = None
            if str(case_ref) in related_ids:
                case = TestAssetGovernanceDao.get_by_id(session, TestCase, case_ref)
            else:
                related_int_ids = [int(item) for item in related_ids if str(item).isdigit()]
                if related_int_ids:
                    case = session.query(TestCase).filter(
                        TestCase.id.in_(related_int_ids),
                        TestCase.project_id == int(issue.project_id),
                        TestCase.case_key == str(case_ref),
                        TestCase.is_delete == 0
                    ).first()
            if not case:
                return 0, '用例编号或ID不属于该问题的关联用例'
            if not case or int(case.project_id) != int(issue.project_id):
                return 0, '未查询到该项目下的测试用例'
            _, err_msg = TestAssetGovernanceDao.update_by_id(session, TestCase, case.id, {'status': 2})
            if err_msg:
                return 0, err_msg
            result_payload = {'caseId': int(case.id), 'caseKey': case.case_key or '', 'caseStatus': 2}

        action_obj, err_msg = TestAssetGovernanceDao.create(session, TestAssetAction, {
            'issue_id': int(issue.id),
            'action_type': action_type,
            'action_payload': TestAssetGovernanceService._json_safe(dict(req_data)),
            'result_payload': result_payload,
            'status': 'success',
            'created_by': user_id
        })
        if err_msg:
            return 0, err_msg

        update_info = {'action_status': action_status}
        if action_status in ('ignored', 'fixed'):
            update_info['resolved_by'] = user_id
            update_info['resolved_time'] = datetime.now()
        if action_status in ('open', 'reopened'):
            update_info['resolved_by'] = None
            update_info['resolved_time'] = None
        update_id, err_msg = TestAssetGovernanceDao.update_by_id(session, TestAssetIssue, issue.id, update_info)
        if err_msg:
            return 0, err_msg
        return action_obj.id if action_obj else update_id, ''

    @staticmethod
    def _load_context(session, scan):
        modules = session.query(Module).filter(
            Module.project_id == int(scan.project_id),
            Module.is_delete == 0
        ).order_by(Module.sort_order.asc(), Module.id.asc()).all()
        module_map = {int(item.id): item for item in modules}
        module_name_map = {item.name: item for item in modules if item.name}

        cases = session.query(TestCase).filter(
            TestCase.project_id == int(scan.project_id),
            TestCase.is_delete == 0
        ).order_by(TestCase.id.asc()).all()
        case_ids = [int(item.id) for item in cases]

        execution_stats = TestAssetGovernanceService._load_execution_stats(session, case_ids)
        bug_stats = TestAssetGovernanceService._load_bug_stats(session, scan.project_id)
        precise_signals = TestAssetGovernanceService._load_precise_signals(
            session, case_ids, list(module_name_map.keys())
        )
        ai_suggestions = TestAssetGovernanceService._load_ai_suggestions(session, scan.project_id, module_name_map)

        case_rows = []
        for case in cases:
            row = BaseCrudController.serialize(case)
            module = module_map.get(int(case.module_id)) if case.module_id else None
            row['moduleName'] = module.name if module else ''
            row['modulePath'] = module.path if module else ''
            row['active'] = TestAssetGovernanceService._is_active_case(row)
            case_rows.append(row)

        module_rows = []
        active_counts = defaultdict(int)
        for case in case_rows:
            if case.get('active') and case.get('module_id'):
                active_counts[int(case.get('module_id'))] += 1
        for module in modules:
            row = BaseCrudController.serialize(module)
            row['activeCaseCount'] = active_counts.get(int(module.id), 0)
            module_rows.append(row)

        return {
            'scan': BaseCrudController.serialize(scan),
            'cases': TestAssetGovernanceService._json_safe(case_rows),
            'modules': TestAssetGovernanceService._json_safe(module_rows),
            'executionStats': TestAssetGovernanceService._json_safe(execution_stats),
            'bugStats': TestAssetGovernanceService._json_safe(bug_stats),
            'preciseSignals': TestAssetGovernanceService._json_safe(precise_signals),
            'aiSuggestions': TestAssetGovernanceService._json_safe(ai_suggestions),
            'options': scan.options_json or {}
        }

    @staticmethod
    def _load_execution_stats(session, case_ids):
        stats = {}
        if not case_ids:
            return stats
        rows = session.query(PlanCase).filter(PlanCase.case_id.in_(case_ids)).all()
        for row in rows:
            case_id = int(row.case_id)
            item = stats.setdefault(case_id, {
                'caseId': case_id,
                'executionCount': 0,
                'passCount': 0,
                'failureCount': 0,
                'blockedCount': 0,
                'lastExecutedTime': None
            })
            if row.executed_time:
                item['executionCount'] += 1
                last_time = item.get('lastExecutedTime')
                if not last_time or row.executed_time > last_time:
                    item['lastExecutedTime'] = row.executed_time
            if row.status == 1:
                item['passCount'] += 1
            elif row.status == 2:
                item['failureCount'] += 1
            elif row.status == 3:
                item['blockedCount'] += 1
        return stats

    @staticmethod
    def _load_bug_stats(session, project_id):
        stats = {
            'byModule': {},
            'byCase': {},
            'total': 0,
            'highSeverityTotal': 0
        }
        bugs = session.query(Bug).filter(
            Bug.project_id == int(project_id),
            Bug.is_delete == 0
        ).all()
        stats['total'] = len(bugs)
        for bug in bugs:
            high = TestAssetGovernanceService._is_high_bug(bug)
            if high:
                stats['highSeverityTotal'] += 1
            if bug.module_id:
                module_item = stats['byModule'].setdefault(int(bug.module_id), {
                    'bugCount': 0,
                    'highSeverityCount': 0,
                    'bugIds': []
                })
                module_item['bugCount'] += 1
                module_item['highSeverityCount'] += 1 if high else 0
                module_item['bugIds'].append(int(bug.id))
            if bug.case_id:
                case_item = stats['byCase'].setdefault(int(bug.case_id), {
                    'bugCount': 0,
                    'highSeverityCount': 0,
                    'bugIds': []
                })
                case_item['bugCount'] += 1
                case_item['highSeverityCount'] += 1 if high else 0
                case_item['bugIds'].append(int(bug.id))
        return stats

    @staticmethod
    def _load_precise_signals(session, case_ids, module_names):
        signals = {
            'byCase': {},
            'byModuleName': {},
            'total': 0,
            'highRiskTotal': 0
        }
        if not case_ids and not module_names:
            return signals
        filters = [PreciseRecommendation.is_delete == 0]
        source_filters = []
        if case_ids:
            source_filters.append(PreciseRecommendation.case_id.in_(case_ids))
        if module_names:
            source_filters.append(PreciseRecommendation.module_name.in_(module_names))
        rows = session.query(PreciseRecommendation).filter(*filters, or_(*source_filters)).all()
        signals['total'] = len(rows)
        for rec in rows:
            high = rec.risk_level in ('high', 'critical') or rec.recommend_level in ('P0', 'P1')
            if high:
                signals['highRiskTotal'] += 1
            data = {
                'id': int(rec.id),
                'caseId': int(rec.case_id) if rec.case_id else None,
                'moduleName': rec.module_name or '',
                'apiPath': rec.api_path or '',
                'recommendLevel': rec.recommend_level or '',
                'riskLevel': rec.risk_level or '',
                'accepted': rec.accepted,
                'executionStatus': rec.execution_status
            }
            if rec.case_id:
                case_item = signals['byCase'].setdefault(int(rec.case_id), {'recommendations': []})
                case_item['recommendations'].append(data)
            if rec.module_name:
                module_item = signals['byModuleName'].setdefault(rec.module_name, {'recommendations': []})
                module_item['recommendations'].append(data)
        return signals

    @staticmethod
    def _load_ai_suggestions(session, project_id, module_name_map):
        rows = session.query(AiTestReviewCaseSuggestion, AiTestReview).join(
            AiTestReview, AiTestReviewCaseSuggestion.review_id == AiTestReview.id
        ).filter(
            AiTestReview.project_id == int(project_id),
            AiTestReview.is_delete == 0,
            AiTestReviewCaseSuggestion.is_delete == 0
        ).order_by(AiTestReviewCaseSuggestion.created_time.desc()).all()
        suggestions = []
        for suggestion, review in rows:
            module = module_name_map.get(suggestion.module_name or '')
            suggestions.append({
                'id': int(suggestion.id),
                'reviewId': int(review.id),
                'reviewTitle': review.title,
                'moduleName': suggestion.module_name or '',
                'moduleId': int(module.id) if module else None,
                'caseTitle': suggestion.case_title,
                'preconditions': suggestion.preconditions or '',
                'steps': suggestion.steps or '',
                'expectedResults': suggestion.expected_results or '',
                'priority': suggestion.priority,
                'caseType': suggestion.case_type,
                'tags': suggestion.tags or [],
                'matchedCaseId': int(suggestion.matched_case_id) if suggestion.matched_case_id else None,
                'createdCaseId': int(suggestion.created_case_id) if suggestion.created_case_id else None,
                'actionStatus': suggestion.action_status or ''
            })
        return suggestions

    @staticmethod
    def _detect_duplicate_cases(context):
        cases = [item for item in context.get('cases') or [] if TestAssetGovernanceService._is_active_case(item)]
        threshold = TestAssetGovernanceService._duplicate_threshold(context.get('options') or {})
        issues = []
        normalized = []
        for case in cases:
            text = TestAssetGovernanceService._normalize_case_text(case)
            if len(text) >= 12:
                normalized.append((case, text))
        for index, (left, left_text) in enumerate(normalized):
            for right, right_text in normalized[index + 1:]:
                ratio = SequenceMatcher(None, left_text, right_text).ratio()
                if ratio < threshold:
                    continue
                severity = 'high' if ratio >= 0.9 else 'medium'
                issues.append(TestAssetGovernanceService._issue_row(
                    context,
                    issue_type='duplicate_case',
                    severity=severity,
                    title='发现疑似重复用例：{} / {}'.format(left.get('title'), right.get('title'))[:255],
                    description='两个用例的标题、步骤、预期和标签文本相似度达到 {:.2f}，建议确认是否需要合并或保留一个主用例。'.format(ratio),
                    module_id=left.get('module_id') or right.get('module_id'),
                    module_name=left.get('moduleName') or right.get('moduleName') or '',
                    evidence={
                        'score': round(ratio, 4),
                        'threshold': threshold,
                        'cases': [
                            TestAssetGovernanceService._compact_case(left),
                            TestAssetGovernanceService._compact_case(right)
                        ]
                    },
                    suggestion={
                        'action': 'merge',
                        'primaryCaseId': left.get('id'),
                        'duplicateCaseId': right.get('id'),
                        'message': '确认业务语义后，将重复步骤合并到主用例，另一个用例可废弃。'
                    },
                    related_case_ids=[left.get('id'), right.get('id')]
                ))
        return issues

    @staticmethod
    def _duplicate_threshold(options):
        try:
            threshold = float((options or {}).get('duplicateThreshold') or TestAssetGovernanceService.DUPLICATE_THRESHOLD_MIN)
        except (TypeError, ValueError):
            threshold = TestAssetGovernanceService.DUPLICATE_THRESHOLD_MIN
        return max(TestAssetGovernanceService.DUPLICATE_THRESHOLD_MIN, threshold)

    @staticmethod
    def _detect_weak_cases(context):
        issues = []
        for case in context.get('cases') or []:
            if not TestAssetGovernanceService._is_active_case(case):
                continue
            weak_points = []
            if len(TestAssetGovernanceService._clean_text(case.get('steps'))) < 8:
                weak_points.append('步骤缺失或过短')
            expected = TestAssetGovernanceService._clean_text(case.get('expected_results'))
            if len(expected) < 8:
                weak_points.append('预期结果缺失或过短')
            elif TestAssetGovernanceService._is_weak_assertion(expected):
                weak_points.append('预期结果断言过泛')
            if not weak_points:
                continue
            severity = 'medium' if len(weak_points) > 1 else 'low'
            issues.append(TestAssetGovernanceService._issue_row(
                context,
                issue_type='weak_case',
                severity=severity,
                title='低质量用例：{}'.format(case.get('title'))[:255],
                description='该用例存在{}，建议补充可执行步骤、数据条件和可验证断言。'.format('、'.join(weak_points)),
                module_id=case.get('module_id'),
                module_name=case.get('moduleName') or '',
                evidence={
                    'weakPoints': weak_points,
                    'case': TestAssetGovernanceService._compact_case(case),
                    'stepsLength': len(TestAssetGovernanceService._clean_text(case.get('steps'))),
                    'expectedLength': len(expected)
                },
                suggestion={
                    'action': 'improve',
                    'message': '补充明确输入数据、操作路径、状态变化和可核验的预期结果。'
                },
                related_case_ids=[case.get('id')]
            ))
        return issues

    @staticmethod
    def _detect_stale_cases(context):
        options = context.get('options') or {}
        stale_days = int(options.get('staleDays') or 180)
        cutoff = datetime.now() - timedelta(days=stale_days)
        execution_stats = TestAssetGovernanceService._int_key_map(context.get('executionStats') or {})
        issues = []
        for case in context.get('cases') or []:
            if not TestAssetGovernanceService._is_active_case(case):
                continue
            case_id = int(case.get('id'))
            stats = execution_stats.get(case_id, {})
            last_executed = TestAssetGovernanceService._parse_datetime(stats.get('lastExecutedTime'))
            created_time = TestAssetGovernanceService._parse_datetime(case.get('created_time'))
            stale_reason = ''
            if last_executed and last_executed < cutoff:
                stale_reason = '最近执行时间早于 {} 天阈值'.format(stale_days)
            elif not last_executed and created_time and created_time < cutoff:
                stale_reason = '创建超过 {} 天但没有执行记录'.format(stale_days)
            if not stale_reason:
                continue
            issues.append(TestAssetGovernanceService._issue_row(
                context,
                issue_type='stale_case',
                severity='medium' if not last_executed else 'low',
                title='过期用例：{}'.format(case.get('title'))[:255],
                description='{}，建议重新评审有效性并安排回归执行。'.format(stale_reason),
                module_id=case.get('module_id'),
                module_name=case.get('moduleName') or '',
                evidence={
                    'staleDays': stale_days,
                    'cutoff': cutoff.strftime('%Y-%m-%d %H:%M:%S'),
                    'case': TestAssetGovernanceService._compact_case(case),
                    'executionStats': TestAssetGovernanceService._json_safe(stats)
                },
                suggestion={
                    'action': 'improve',
                    'message': '确认需求是否仍有效，必要时更新步骤/预期，并纳入下一轮回归。'
                },
                related_case_ids=[case.get('id')]
            ))
        return issues

    @staticmethod
    def _detect_coverage_gaps(context):
        bug_by_module = TestAssetGovernanceService._int_key_map((context.get('bugStats') or {}).get('byModule') or {})
        precise_by_module = (context.get('preciseSignals') or {}).get('byModuleName') or {}
        suggestions_by_module = defaultdict(list)
        for suggestion in context.get('aiSuggestions') or []:
            if TestAssetGovernanceService._is_unprocessed_suggestion(suggestion):
                suggestions_by_module[suggestion.get('moduleName') or ''].append(suggestion)

        issues = []
        for module in context.get('modules') or []:
            if module.get('status') == 2 or int(module.get('activeCaseCount') or 0) > 0:
                continue
            module_id = int(module.get('id'))
            module_name = module.get('name') or ''
            bug_info = bug_by_module.get(module_id, {})
            precise_info = precise_by_module.get(module_name, {})
            ai_items = suggestions_by_module.get(module_name, [])
            if not bug_info and not precise_info and not ai_items:
                continue
            high_pressure = (bug_info.get('highSeverityCount') or 0) > 0 or len(precise_info.get('recommendations') or []) > 0
            severity = 'high' if high_pressure else 'medium'
            issues.append(TestAssetGovernanceService._issue_row(
                context,
                issue_type='coverage_gap',
                severity=severity,
                title='模块存在覆盖缺口：{}'.format(module_name)[:255],
                description='该模块暂无活动用例，但存在缺陷、精准测试推荐或 AI 建议，建议补充核心覆盖。',
                module_id=module_id,
                module_name=module_name,
                evidence={
                    'module': module,
                    'bugInfo': bug_info,
                    'preciseRecommendations': precise_info.get('recommendations') or [],
                    'aiSuggestions': ai_items
                },
                suggestion={
                    'action': 'accept_suggestion' if ai_items else 'improve',
                    'message': '优先补充该模块主流程、历史缺陷回归和变更影响用例。'
                },
                related_case_ids=[]
            ))
        return issues

    @staticmethod
    def _detect_ai_suggestions(context):
        issues = []
        for suggestion in context.get('aiSuggestions') or []:
            if not TestAssetGovernanceService._is_unprocessed_suggestion(suggestion):
                continue
            issues.append(TestAssetGovernanceService._issue_row(
                context,
                issue_type='ai_suggestion',
                severity='medium',
                title='AI建议用例待处理：{}'.format(suggestion.get('caseTitle'))[:255],
                description='AI测试评审已生成建议用例，但尚未导入或关联到现有用例库。',
                module_id=suggestion.get('moduleId'),
                module_name=suggestion.get('moduleName') or '',
                evidence={
                    'suggestion': suggestion,
                    'reviewId': suggestion.get('reviewId'),
                    'reviewTitle': suggestion.get('reviewTitle')
                },
                suggestion={
                    'action': 'accept_suggestion',
                    'message': '确认建议用例后导入用例库，或关联到已有覆盖用例。'
                },
                related_case_ids=[]
            ))
        return issues

    @staticmethod
    def _build_summary(context, issues):
        cases = context.get('cases') or []
        active_cases = [item for item in cases if TestAssetGovernanceService._is_active_case(item)]
        modules = context.get('modules') or []
        issue_type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        score = 100
        for issue in issues:
            issue_type_counts[issue.get('issue_type')] += 1
            severity = issue.get('severity') or 'medium'
            severity_counts[severity] += 1
            score -= TestAssetGovernanceService.SEVERITY_DEDUCTION.get(severity, 6)
        score = max(0, int(score))
        recommended_actions = TestAssetGovernanceService._recommended_actions(issue_type_counts, severity_counts)
        summary_text = '本次扫描覆盖 {} 条用例、{} 个模块，发现 {} 个治理问题，资产健康分 {}。'.format(
            len(cases), len(modules), len(issues), score
        )
        return {
            'totalCases': len(cases),
            'activeCases': len(active_cases),
            'aiGeneratedCases': len([item for item in cases if int(item.get('is_ai_generated') or 0) == 1]),
            'moduleCount': len(modules),
            'issueCount': len(issues),
            'issueTypeCounts': dict(issue_type_counts),
            'severityCounts': dict(severity_counts),
            'healthScore': score,
            'summary': summary_text,
            'recommendedActions': recommended_actions
        }

    @staticmethod
    def _enhance_summary_with_ai(summary, issues):
        if not issues:
            return summary
        prompt = '''你是资深测试资产治理专家。请基于扫描摘要和问题列表，优化中文摘要和推荐动作，必须只输出JSON。
输入摘要：
{summary}
问题列表：
{issues}

输出结构：
{{
  "summary": "不超过180字的治理摘要",
  "recommendedActions": ["动作1", "动作2"],
  "healthScore": {health_score}
}}
'''.format(
            summary=json.dumps(summary, ensure_ascii=False, default=TestAssetGovernanceService._json_default),
            issues=json.dumps(issues[:30], ensure_ascii=False, default=TestAssetGovernanceService._json_default)[:12000],
            health_score=int(summary.get('healthScore') or 0)
        )
        ai_result, err_msg = AIService.request_json(prompt, 'AI测试资产治理摘要')
        if err_msg or not isinstance(ai_result, dict):
            return summary
        result = dict(summary)
        if ai_result.get('summary'):
            result['summary'] = str(ai_result.get('summary'))[:500]
        if isinstance(ai_result.get('recommendedActions'), list) and ai_result.get('recommendedActions'):
            result['recommendedActions'] = [str(item) for item in ai_result.get('recommendedActions')[:8]]
        try:
            result['healthScore'] = int(ai_result.get('healthScore') if ai_result.get('healthScore') is not None else result.get('healthScore'))
        except (TypeError, ValueError):
            pass
        return result

    @staticmethod
    def _issue_row(context, issue_type, severity, title, description, module_id=None, module_name='',
                   evidence=None, suggestion=None, related_case_ids=None):
        scan = context.get('scan') or {}
        return {
            'scan_id': int(scan.get('id')),
            'product_id': TestAssetGovernanceService._to_int(scan.get('product_id')),
            'project_id': int(scan.get('project_id')),
            'module_id': TestAssetGovernanceService._to_int(module_id),
            'module_name': module_name or '',
            'issue_type': issue_type,
            'severity': severity or 'medium',
            'title': title or '未命名治理问题',
            'description': description or '',
            'evidence_json': evidence or {},
            'suggestion_json': suggestion or {},
            'related_case_ids': [int(item) for item in related_case_ids or [] if item not in (None, '')],
            'action_status': 'open',
            'is_delete': 0
        }

    @staticmethod
    def _enrich_issue_case_refs(session, issue_rows):
        case_ids = set()
        for issue in issue_rows or []:
            for raw_id in issue.get('related_case_ids') or issue.get('relatedCaseIds') or []:
                case_id = TestAssetGovernanceService._to_int(raw_id)
                if case_id:
                    case_ids.add(case_id)
        if not case_ids:
            return issue_rows

        cases = session.query(TestCase).filter(
            TestCase.id.in_(list(case_ids)),
            TestCase.is_delete == 0
        ).all()
        case_map = {int(case.id): case for case in cases}
        for issue in issue_rows or []:
            related_cases = []
            related_keys = []
            for raw_id in issue.get('related_case_ids') or issue.get('relatedCaseIds') or []:
                case_id = TestAssetGovernanceService._to_int(raw_id)
                if not case_id:
                    continue
                case = case_map.get(case_id)
                if not case:
                    continue
                case_key = case.case_key or ''
                related_cases.append({
                    'id': case_id,
                    'case_id': case_id,
                    'caseId': case_id,
                    'case_key': case_key,
                    'caseKey': case_key,
                    'title': case.title or ''
                })
                if case_key:
                    related_keys.append(case_key)
            issue['related_cases'] = related_cases
            issue['relatedCases'] = related_cases
            issue['related_case_keys'] = related_keys
            issue['relatedCaseKeys'] = related_keys
        return issue_rows

    @staticmethod
    def _normalize_options(req_data):
        options = AiCommonService.get(req_data, 'optionsJson', 'options_json', 'options', default={})
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except ValueError:
                options = {}
        if not isinstance(options, dict):
            options = {}
        for key in ('staleDays', 'duplicateThreshold'):
            value = AiCommonService.get(req_data, key, AiCommonService.camel_to_snake(key))
            if value not in (None, ''):
                options[key] = value
        return options

    @staticmethod
    def _recommended_actions(issue_type_counts, severity_counts):
        actions = []
        if issue_type_counts.get('duplicate_case'):
            actions.append('优先确认重复用例，保留主用例并记录合并处理结果。')
        if issue_type_counts.get('weak_case'):
            actions.append('补强低质量用例的步骤、数据条件和可验证预期。')
        if issue_type_counts.get('stale_case'):
            actions.append('安排过期用例复审和回归执行，清理已失效场景。')
        if issue_type_counts.get('coverage_gap'):
            actions.append('对缺陷和变更压力较高但无用例的模块补充覆盖。')
        if issue_type_counts.get('ai_suggestion'):
            actions.append('处理 AI 建议用例，导入或关联到已有用例库。')
        if severity_counts.get('critical') or severity_counts.get('high'):
            actions.insert(0, '先处理高风险治理项，再进入发布或大规模回归。')
        return actions or ['当前资产风险较低，建议保持周期性治理扫描。']

    @staticmethod
    def _status_after_action(action_type):
        return {
            'keep': 'ignored',
            'merge': 'accepted',
            'improve': 'accepted',
            'deprecate': 'fixed',
            'accept_suggestion': 'accepted',
            'ignore': 'ignored',
            'mark_fixed': 'fixed',
            'reopen': 'reopened'
        }.get(action_type, 'accepted')

    @staticmethod
    def _is_active_case(case):
        return int(case.get('is_delete') or 0) == 0 and int(case.get('status') or 1) != 2

    @staticmethod
    def _is_high_bug(bug):
        try:
            return int(bug.severity or 0) <= 1
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_unprocessed_suggestion(suggestion):
        status = (suggestion.get('actionStatus') or '').lower()
        return status in ('', 'pending', 'open') and not suggestion.get('createdCaseId') and not suggestion.get('matchedCaseId')

    @staticmethod
    def _normalize_case_text(case):
        values = [
            case.get('title'),
            case.get('steps'),
            case.get('expected_results'),
            ' '.join(case.get('tags') or []) if isinstance(case.get('tags'), list) else case.get('tags')
        ]
        return re.sub(r'\s+', '', ''.join([str(item).lower() for item in values if item not in (None, '')]))

    @staticmethod
    def _clean_text(value):
        return re.sub(r'\s+', '', str(value or ''))

    @staticmethod
    def _is_weak_assertion(expected):
        generic_words = ['正常', '成功', '通过', '无异常', '正确']
        if not any(word in expected for word in generic_words):
            return False
        concrete_markers = ['状态', '字段', '返回', '提示', '数据库', '金额', '数量', '权限', '编码', '时间', '列表', '详情']
        return len(expected) <= 20 or not any(marker in expected for marker in concrete_markers)

    @staticmethod
    def _compact_case(case):
        return {
            'id': case.get('id'),
            'caseKey': case.get('case_key'),
            'title': case.get('title'),
            'moduleId': case.get('module_id'),
            'moduleName': case.get('moduleName'),
            'priority': case.get('priority'),
            'status': case.get('status')
        }

    @staticmethod
    def _int_key_map(data):
        result = {}
        for key, value in data.items():
            try:
                result[int(key)] = value
            except (TypeError, ValueError):
                result[key] = value
        return result

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None

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
        return json.loads(json.dumps(data, ensure_ascii=False, default=TestAssetGovernanceService._json_default))

    @staticmethod
    def _json_default(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, Decimal):
            return float(value)
        return str(value)
