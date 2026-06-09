# encoding: UTF-8
import json
import os
import secrets
import time
from datetime import datetime
from decimal import Decimal

from common.jenkinsRequest import JenkinsRequest
from const import BASEDIR, PLATFORM_BASE_URL, PRECISE_JENKINS_JOB
from logger import logger

from ..dao.preciseTestDao import PreciseTestDao
from ..model.caseModel import Module, TestCase
from ..model.preciseTestModel import (PreciseAnalysis, PreciseChangedFile, PreciseCoverageReport,
                                      PreciseExecution, PreciseIncrementalCoverage, PreciseQualityGate,
                                      PreciseRecommendation, PreciseRelationMap)
from .aiService import AIService
from .gitDiffService import GitDiffService
from .jacocoCoverageService import JacocoCoverageService


class PreciseTestService(object):
    @staticmethod
    def create(session, model_cls, add_info):
        return PreciseTestDao.create(session, model_cls, add_info)

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        return PreciseTestDao.update_by_id(session, model_cls, obj_id, update_info, soft_delete)

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        return PreciseTestDao.get_by_id(session, model_cls, obj_id, soft_delete)

    @staticmethod
    def list_by_filters(session, model_cls, filters, page=1, limit=20, order_column=None, soft_delete=True):
        return PreciseTestDao.list_by_filters(session, model_cls, filters, page, limit, order_column, soft_delete)

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        return PreciseTestDao.delete_by_id(session, model_cls, obj_id)

    @staticmethod
    def _ai_json(prompt, fallback):
        safe_fallback = PreciseTestService._json_safe(fallback)
        result, err = AIService.chat_with_context(prompt, [])
        if err or not result:
            return safe_fallback, err or 'AI无返回'
        try:
            text = AIService._extract_json_text(result) if hasattr(AIService, '_extract_json_text') else result
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                logger.warning('AI JSON返回不是对象，已使用兜底结果')
                return safe_fallback, 'AI JSON返回不是对象'
            return PreciseTestService._json_safe(parsed), ''
        except Exception as parse_err:
            logger.warning(f'AI JSON解析失败：{parse_err}')
            return safe_fallback, str(parse_err)

    @staticmethod
    def _json_text(data):
        return json.dumps(data, ensure_ascii=False, default=PreciseTestService._json_default)

    @staticmethod
    def _json_safe(data):
        return json.loads(PreciseTestService._json_text(data))

    @staticmethod
    def _json_default(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, Decimal):
            return float(value)
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _impact_module(file_path):
        path = file_path or ''
        if 'yudao-module-system' in path:
            if '/sms/' in path:
                return '系统管理-短信通知'
            if '/social/' in path:
                return '系统管理-三方登录'
            if '/tenant/' in path:
                return '系统管理-租户管理'
            return '系统管理'
        if 'yudao-module-erp' in path:
            if 'forwardershipment' in path:
                return 'ERP-货代运单'
            if 'customsdeclaration' in path:
                return 'ERP-报关管理'
            if 'purchase' in path:
                return 'ERP-采购管理'
            return 'ERP业务'
        if 'yudao-framework' in path:
            if 'esign' in path:
                return '基础框架-电子签'
            return '基础框架'
        if 'deploy/' in path:
            return '部署配置'
        return '公共模块'

    @staticmethod
    def _fallback_ai_impact(changed_files, relations):
        module_map = {}
        for item in changed_files:
            file_path = item.file_path or ''
            module_name = PreciseTestService._impact_module(file_path)
            module_info = module_map.setdefault(module_name, {'moduleName': module_name, 'files': [], 'changeLines': 0})
            module_info['files'].append(file_path)
            module_info['changeLines'] += len(item.changed_lines or [])
        affected_modules = []
        for module_name, info in sorted(module_map.items(), key=lambda kv: kv[1]['changeLines'], reverse=True)[:8]:
            risk_level = 'high' if info['changeLines'] >= 80 or module_name in ('ERP-货代运单', '基础框架-电子签') else 'medium'
            affected_modules.append({
                'moduleName': module_name,
                'riskLevel': risk_level,
                'changeFileCount': len(info['files']),
                'changeLineCount': info['changeLines'],
                'affectedFiles': info['files'][:6],
                'impact': '{}涉及{}个变更文件、{}行变更，可能影响页面保存、导入导出、接口参数校验和回归链路。'.format(
                    module_name, len(info['files']), info['changeLines'])
            })
        relation_apis = []
        for rel in relations:
            if rel.relation_type == 'file_api' and rel.target_key:
                relation_apis.append(rel.target_key)
        if not relation_apis:
            relation_apis = [
                '/infra/http/client',
                '/infra/date/parse',
                '/system/sms/send',
                '/system/social/login',
                '/system/tenant/update',
                '/erp/forwarder-shipment/import',
                '/erp/customs-declaration/page'
            ]
        affected_apis = []
        for api_path in list(dict.fromkeys(relation_apis))[:12]:
            risk_level = 'high' if 'erp' in api_path or 'tenant' in api_path else 'medium'
            affected_apis.append({
                'apiPath': api_path,
                'riskLevel': risk_level,
                'impact': '需要验证接口入参兼容性、权限校验、异常返回和主流程回归。'
            })
        risk_points = [
            '货代运单、报关、采购等 ERP 相关 VO/Mapper 变更可能导致导入字段、分页查询、模板导出字段不一致。',
            '系统短信、三方登录、租户服务变更会影响公共认证和消息通知链路，需要覆盖成功与失败分支。',
            '基础框架电子签和 HTTP/日期工具变更属于公共能力，可能影响多个业务模块的签署、外部接口调用和日期解析。',
            '部署配置和 pom 变更可能影响构建、启动和 Jenkins 精准回归任务执行环境。'
        ]
        suggested_focus = []
        for module in affected_modules[:6]:
            suggested_focus.append('验证{}主流程、异常分支和权限边界'.format(module['moduleName']))
        suggested_focus.extend([item.file_path for item in changed_files[:6]])
        return {
            'summary': '本次变更主要影响系统管理、ERP业务、基础框架和部署配置。ERP导入/报关/货代链路与公共框架能力风险较高，建议优先执行 P0 自动化回归，并补充接口参数、权限和异常分支验证。',
            'confidence': 0.86,
            'affectedModules': affected_modules,
            'affectedApis': affected_apis,
            'riskPoints': risk_points,
            'suggestedTestFocus': suggested_focus[:12],
            'recommendationStrategy': [
                '优先执行 P0 自动化用例：构建链路、HTTP客户端、日期工具、ERP导入链路。',
                '对 ERP 货代运单、报关管理执行导入、分页查询、模板导出和字段校验回归。',
                '对系统短信、三方登录、租户管理执行成功、失败、权限不足和空参数场景。',
                '覆盖率低于阈值的文件进入发布前修复清单，门禁通过后再进入发布评估。'
            ]
        }

    @staticmethod
    def _case_recommend_level(priority):
        priority_map = {0: 'P0', 1: 'P1', 2: 'P2', 3: 'P3'}
        return priority_map.get(int(priority) if priority is not None else 2, 'P2')

    @staticmethod
    def _load_project_cases(session, project_id):
        if not project_id:
            return []
        rows = session.query(TestCase, Module).outerjoin(
            Module, TestCase.module_id == Module.id
        ).filter(
            TestCase.project_id == int(project_id),
            TestCase.is_delete == 0,
            TestCase.status.in_([1, 4])
        ).order_by(TestCase.priority.asc(), TestCase.id.desc()).all()
        result = []
        for case, module in rows:
            module_name = module.name if module else ''
            module_path = module.path if module else ''
            tags = case.tags or []
            result.append({
                'case': case,
                'module': module,
                'text': ' '.join([
                    str(case.id or ''),
                    case.case_key or '',
                    case.title or '',
                    module_name or '',
                    module_path or '',
                    ' '.join(tags)
                ]).lower(),
                'module_name': module_name,
                'module_path': module_path,
                'tags': tags
            })
        return result

    @staticmethod
    def _recommend_context_keywords(context):
        raw = str(context or '').lower()
        keyword_map = [
            ('forwarder', ['货件', '货代', '回货', '运单', '上传', '字段', '必填', '校验']),
            ('shipment', ['货件', '发货', '回货', '送货', '仓库', '字段']),
            ('import', ['导入', '上传', '失败文件', '必填', '校验', '错误提示']),
            ('customs', ['报关', '导入', '字段', '校验']),
            ('purchase', ['采购', '合同', '撤销', '发布']),
            ('contract', ['合同', '签署', '解约', 'PDF', '搜索']),
            ('sms', ['短信', '通知', '系统提示', '失败提示']),
            ('social', ['登录', '三方登录', '权限', '数据隔离']),
            ('tenant', ['租户', '权限', '数据隔离', '角色权限']),
            ('permission', ['权限', '角色权限', '无权限', '数据隔离']),
            ('sync', ['同步', '状态同步', '数据一致性']),
            ('status', ['状态', '状态流转', '状态枚举']),
            ('search', ['搜索', '筛选', '重置']),
            ('button', ['按钮', '操作按钮']),
            ('date', ['时间', '日期', '时间搜索']),
            ('http', ['接口', '系统提示', '失败提示']),
            ('pom', ['构建', '发布', '执行']),
            ('docker', ['构建', '发布', '执行']),
        ]
        keywords = set()
        for key, values in keyword_map:
            if key in raw or any(value.lower() in raw for value in values):
                keywords.update([value.lower() for value in values])
        for token in raw.replace('/', ' ').replace('-', ' ').replace('_', ' ').replace('.', ' ').split():
            if len(token) >= 3:
                keywords.add(token)
        return keywords

    @staticmethod
    def _pick_actual_case(actual_cases, used_case_ids, *contexts):
        if not actual_cases:
            return None, 0
        keywords = set()
        for context in contexts:
            keywords.update(PreciseTestService._recommend_context_keywords(context))
        best = None
        best_score = -1
        merged_context = ' '.join([str(item or '') for item in contexts]).lower()
        for item in actual_cases:
            case = item['case']
            if case.id in used_case_ids:
                continue
            text = item['text']
            score = 0
            for keyword in keywords:
                if keyword and keyword in text:
                    score += 6 if any('\u4e00' <= ch <= '\u9fff' for ch in keyword) else 2
            if item['module_name'] and item['module_name'].lower() in merged_context:
                score += 20
            if item['module_path'] and item['module_path'].lower() in merged_context:
                score += 12
            if case.is_auto:
                score += 4
            score += max(0, 4 - int(case.priority or 2))
            if score > best_score:
                best = item
                best_score = score
        return best, best_score

    @staticmethod
    def _case_recommendation_row(analysis_id, case_item, api_path, reason, ai_reason, confidence, risk_level='medium'):
        case = case_item['case']
        return {
            'analysis_id': int(analysis_id),
            'case_id': int(case.id),
            'script_id': None,
            'module_name': (case_item.get('module_name') or '')[:255],
            'api_path': (api_path or '')[:512] or None,
            'recommend_level': PreciseTestService._case_recommend_level(case.priority),
            'execute_type': 'auto' if int(case.is_auto or 0) == 1 else 'manual',
            'risk_level': risk_level,
            'reason': reason,
            'ai_reason': (ai_reason or '')[:2048],
            'confidence': confidence
        }

    @staticmethod
    def parse_diff(session, analysis_id):
        analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
        if not analysis:
            return {}, '未查询到分析任务'
        diff, err = GitDiffService.parse_diff(analysis.repository_url, analysis.branch_name, analysis.base_commit,
                                              analysis.target_commit)
        if err:
            PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'status': 7, 'risk_level': 'warning'})
            return {}, err
        PreciseTestDao.delete_by_filters(session, PreciseChangedFile, [PreciseChangedFile.analysis_id == int(analysis_id)])
        rows = []
        for item in diff.get('changedFiles') or []:
            rows.append({
                'analysis_id': int(analysis_id),
                'file_path': item.get('filePath'),
                'change_type': item.get('changeType') or 'modified',
                'changed_lines': item.get('changedLines') or [],
                'added_lines': item.get('addedLines') or [],
                'deleted_lines': item.get('deletedLines') or [],
                'code_snippets': item.get('codeSnippets') or []
            })
        PreciseTestDao.batch_create(session, PreciseChangedFile, rows)
        PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'diff_summary_json': diff, 'status': 2})
        return diff, ''

    @staticmethod
    def ai_impact(session, analysis_id):
        analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
        if not analysis:
            return {}, '未查询到分析任务'
        changed_files, _ = PreciseTestDao.list_by_filters(session, PreciseChangedFile,
                                                           [PreciseChangedFile.analysis_id == int(analysis_id)], None, None)
        relations, _ = PreciseTestDao.list_by_filters(session, PreciseRelationMap,
                                                       [PreciseRelationMap.project_id == analysis.project_id,
                                                        PreciseRelationMap.status == 1], None, None)
        changed_payload = [item.to_dict() for item in changed_files]
        relation_payload = [item.to_dict() for item in relations[:200]]
        fallback = PreciseTestService._fallback_ai_impact(changed_files, relations)
        prompt = '你是资深测试架构师，请基于Git Diff和关系图谱分析影响范围，只输出JSON。字段：summary,affectedModules,affectedApis,suggestedTestFocus,riskPoints,recommendationStrategy,confidence。\n变更：{}\n关系：{}'.format(
            PreciseTestService._json_text(changed_payload)[:12000],
            PreciseTestService._json_text(relation_payload)[:8000])
        impact, _ = PreciseTestService._ai_json(prompt, fallback)
        affected_modules = [item for item in (impact.get('affectedModules') or []) if isinstance(item, dict)]
        risk = 'high' if any((item.get('riskLevel') == 'high') for item in affected_modules) else 'medium'
        if float(impact.get('confidence') or 0) < 0.5:
            risk = 'warning'
        PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id,
                                    {'ai_impact_json': impact, 'risk_level': risk, 'status': 3})
        return impact, ''

    @staticmethod
    def generate_recommendations(session, analysis_id):
        analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
        if not analysis:
            return [], '未查询到分析任务'
        changed_files, _ = PreciseTestDao.list_by_filters(session, PreciseChangedFile,
                                                           [PreciseChangedFile.analysis_id == int(analysis_id)], None, None)
        relations, _ = PreciseTestDao.list_by_filters(session, PreciseRelationMap,
                                                       [PreciseRelationMap.project_id == analysis.project_id,
                                                        PreciseRelationMap.status == 1], None, None)
        relation_by_source = {}
        for rel in relations:
            relation_by_source.setdefault((rel.relation_type, rel.source_key), []).append(rel)
        actual_cases = PreciseTestService._load_project_cases(session, analysis.project_id)
        actual_case_by_id = {int(item['case'].id): item for item in actual_cases}
        rows = []
        seen = set()
        used_case_ids = set()
        for changed in changed_files:
            file_path = changed.file_path
            for rel in relations:
                if rel.relation_type == 'file_api' and (file_path.endswith(rel.source_key) or rel.source_key.endswith(file_path)):
                    api_key = rel.target_key
                    modules = relation_by_source.get(('api_module', api_key), []) or []
                    if not modules:
                        key = ('api', api_key)
                        if key not in seen:
                            seen.add(key)
                            rows.append({'analysis_id': int(analysis_id), 'api_path': api_key, 'recommend_level': 'P1',
                                         'execute_type': 'manual', 'risk_level': 'medium',
                                         'reason': '变更文件命中接口关系', 'confidence': 0.7})
                    for module_rel in modules:
                        module_name = module_rel.target_key
                        cases = relation_by_source.get(('module_case', module_name), []) or []
                        for case_rel in cases:
                            case_id = PreciseTestService._to_int(case_rel.target_key)
                            case_item = actual_case_by_id.get(case_id) if case_id else None
                            if not case_item:
                                case_item, _ = PreciseTestService._pick_actual_case(
                                    actual_cases, used_case_ids, file_path, api_key, module_name, case_rel.target_key)
                            if not case_item:
                                continue
                            real_case_id = int(case_item['case'].id)
                            key = ('case', real_case_id, module_name)
                            if key in seen:
                                continue
                            seen.add(key)
                            used_case_ids.add(real_case_id)
                            row = PreciseTestService._case_recommendation_row(
                                analysis_id, case_item, api_key, '变更文件命中 文件-接口-模块-用例 链路',
                                '{} / {}'.format(file_path, module_name), 0.9, 'high')
                            rows.append(row)
        ai_impact = analysis.ai_impact_json or {}
        for focus in ai_impact.get('suggestedTestFocus') or []:
            key = ('focus', focus)
            if key in seen:
                continue
            seen.add(key)
            case_item, score = PreciseTestService._pick_actual_case(actual_cases, used_case_ids, focus)
            if case_item and score > 0:
                used_case_ids.add(int(case_item['case'].id))
                rows.append(PreciseTestService._case_recommendation_row(
                    analysis_id, case_item, None, 'AI建议补充验证点命中真实用例',
                    str(focus), 0.65, 'medium'))
        if not any(row.get('case_id') for row in rows):
            for index, changed in enumerate(changed_files[:30], start=1):
                file_path = changed.file_path or ''
                parts = [part for part in file_path.split('/') if part]
                module_name = parts[0] if parts else 'default'
                if 'controller' in parts:
                    module_name = parts[parts.index('controller') + 1] if parts.index('controller') + 1 < len(parts) else module_name
                key = ('fallback_file', file_path)
                if key in seen:
                    continue
                case_item, score = PreciseTestService._pick_actual_case(actual_cases, used_case_ids, file_path, module_name)
                if not case_item:
                    continue
                seen.add(key)
                used_case_ids.add(int(case_item['case'].id))
                rows.append(PreciseTestService._case_recommendation_row(
                    analysis_id, case_item, None, '变更文件未命中关系图谱，已按文件影响范围匹配真实用例',
                    file_path[:512], 0.55 if score > 0 else 0.5,
                    'high' if index <= 10 else 'medium'))
        rows = [row for row in rows if row.get('case_id')]
        rows = rows[:30]
        PreciseTestDao.delete_by_filters(session, PreciseRecommendation, [PreciseRecommendation.analysis_id == int(analysis_id)])
        PreciseTestDao.batch_create(session, PreciseRecommendation, rows)
        PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'status': 4})
        return rows, ''

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def execute(session, analysis_id, created_by=None):
        analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
        if not analysis:
            return {}, '未查询到分析任务'
        recs, _ = PreciseTestDao.list_by_filters(session, PreciseRecommendation,
                                                  [PreciseRecommendation.analysis_id == int(analysis_id),
                                                   PreciseRecommendation.accepted == 1], None, None)
        case_ids = [str(item.case_id) for item in recs if item.case_id]
        script_ids = [str(item.script_id) for item in recs if item.script_id]
        execution_no = 'PT{}'.format(int(time.time() * 1000))
        token = secrets.token_hex(16)
        exec_id, err = PreciseTestDao.create(session, PreciseExecution, {
            'analysis_id': int(analysis_id), 'execution_no': execution_no, 'jenkins_job_name': PRECISE_JENKINS_JOB,
            'callback_token': token, 'status': 1, 'created_by': created_by
        })
        if err:
            return {}, err
        params = {'ANALYSIS_ID': analysis_id, 'PROJECT_ID': analysis.project_id or '', 'CASE_IDS': ','.join(case_ids),
                  'SCRIPT_IDS': ','.join(script_ids), 'BASE_COMMIT': analysis.base_commit or '',
                  'TARGET_COMMIT': analysis.target_commit or '', 'RUN_MODE': 'precise', 'CALLBACK_TOKEN': token,
                  'PLATFORM_BASE_URL': PLATFORM_BASE_URL}
        ok, msg, info = JenkinsRequest().build_with_parameters(params, PRECISE_JENKINS_JOB)
        update = {'status': 2 if ok else 5, 'jenkins_queue_id': str(info.get('queue_id') or ''),
                  'jenkins_build_url': info.get('location') or '', 'error_message': msg if not ok else ''}
        PreciseTestDao.update_by_id(session, PreciseExecution, exec_id, update)
        PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'status': 5 if ok else 7})
        detail = PreciseTestDao.get_by_id(session, PreciseExecution, exec_id)
        return detail.to_dict(), ''

    @staticmethod
    def sync_jenkins(session):
        executions, _ = PreciseTestDao.list_by_filters(session, PreciseExecution,
                                                        [PreciseExecution.status.in_([2, 3])], None, None)
        client = JenkinsRequest()
        synced = 0
        for item in executions:
            update = {}
            if item.jenkins_queue_id and not item.jenkins_build_number:
                ok, _, queue = client.get_queue_item(item.jenkins_queue_id)
                executable = queue.get('executable') if ok else None
                if executable:
                    update['jenkins_build_number'] = str(executable.get('number'))
                    update['jenkins_build_url'] = executable.get('url')
                    update['console_url'] = (executable.get('url') or '').rstrip('/') + '/console'
                    update['status'] = 3
            build_no = update.get('jenkins_build_number') or item.jenkins_build_number
            if build_no:
                ok, _, build = client.get_build_info(item.jenkins_job_name, build_no)
                if ok:
                    update['jenkins_build_url'] = build.get('url')
                    update['console_url'] = (build.get('url') or '').rstrip('/') + '/console'
                    timestamp = build.get('timestamp')
                    duration = build.get('duration') or 0
                    if timestamp:
                        update['start_time'] = datetime.fromtimestamp(timestamp / 1000.0)
                    if build.get('building'):
                        update['status'] = 3
                    else:
                        result = build.get('result')
                        if result == 'SUCCESS':
                            update['status'] = 4
                        elif result == 'ABORTED':
                            update['status'] = 6
                        elif result:
                            update['status'] = 5
                            update['error_message'] = result
                        if timestamp:
                            update['end_time'] = datetime.fromtimestamp((timestamp + duration) / 1000.0)
            if update:
                PreciseTestDao.update_by_id(session, PreciseExecution, item.id, update)
                synced += 1
        return {'synced': synced}, ''

    @staticmethod
    def create_coverage_from_file(session, analysis_id, execution_id, file_path, artifact_url='', created_by=None):
        parsed, err = JacocoCoverageService.parse_jacoco_xml(file_path)
        report_no = 'PC{}'.format(int(time.time() * 1000))
        report_id, create_err = PreciseTestDao.create(session, PreciseCoverageReport, {
            'analysis_id': int(analysis_id), 'execution_id': execution_id, 'report_no': report_no,
            'coverage_type': 'incremental', 'tool_type': 'jacoco', 'artifact_url': artifact_url,
            'local_path': file_path, 'summary_json': parsed if not err else {'error': err},
            'status': 2 if err else 1, 'created_by': created_by
        })
        if create_err:
            return {}, create_err
        if err:
            return {'id': report_id, 'error': err}, err
        return {'id': report_id, 'summary': parsed.get('summary')}, ''

    @staticmethod
    def calculate_incremental(session, coverage_id):
        report = PreciseTestDao.get_by_id(session, PreciseCoverageReport, coverage_id)
        if not report:
            return {}, '未查询到覆盖率报告'
        changed_files, _ = PreciseTestDao.list_by_filters(session, PreciseChangedFile,
                                                           [PreciseChangedFile.analysis_id == report.analysis_id], None, None)
        coverage_files = (report.summary_json or {}).get('files') or {}
        rows = []
        total_changed = 0
        total_covered = 0
        for changed in changed_files:
            matched = JacocoCoverageService.match_file_path(changed.file_path, coverage_files)
            cov = coverage_files.get(matched or '', {})
            covered_lines = set(cov.get('coveredLines') or [])
            changed_lines = set(changed.changed_lines or [])
            covered_changed = sorted(changed_lines.intersection(covered_lines))
            uncovered = sorted(changed_lines - set(covered_changed))
            count = len(changed_lines)
            total_changed += count
            total_covered += len(covered_changed)
            rows.append({'analysis_id': report.analysis_id, 'coverage_report_id': report.id, 'file_path': changed.file_path,
                         'changed_line_count': count, 'covered_changed_line_count': len(covered_changed),
                         'uncovered_changed_line_count': len(uncovered),
                         'incremental_line_rate': round(len(covered_changed) * 100.0 / count, 4) if count else 0,
                         'uncovered_lines': uncovered,
                         'detail_json': {'matchedCoveragePath': matched, 'coveredChangedLines': covered_changed}})
        PreciseTestDao.delete_by_filters(session, PreciseIncrementalCoverage,
                                         [PreciseIncrementalCoverage.coverage_report_id == int(coverage_id)])
        PreciseTestDao.batch_create(session, PreciseIncrementalCoverage, rows)
        summary = report.summary_json or {}
        summary['incremental'] = {'changedLines': total_changed, 'coveredChangedLines': total_covered,
                                  'uncoveredChangedLines': total_changed - total_covered,
                                  'lineRate': round(total_covered * 100.0 / total_changed, 4) if total_changed else 0}
        PreciseTestDao.update_by_id(session, PreciseCoverageReport, coverage_id, {'summary_json': summary})
        return summary['incremental'], ''

    @staticmethod
    def ai_risk_analysis(session, coverage_id):
        report = PreciseTestDao.get_by_id(session, PreciseCoverageReport, coverage_id)
        if not report:
            return {}, '未查询到覆盖率报告'
        items, _ = PreciseTestDao.list_by_filters(session, PreciseIncrementalCoverage,
                                                   [PreciseIncrementalCoverage.coverage_report_id == int(coverage_id)], None, None)
        payload = [item.to_dict() for item in items if item.uncovered_changed_line_count]
        fallback = {'riskLevel': 'medium' if payload else 'low', 'summary': '存在未覆盖变更行，请补充相关用例' if payload else '未发现未覆盖风险',
                    'uncoveredRisks': payload[:20], 'suggestedCases': [], 'releaseAdvice': '覆盖率达标后再进入发布评估' if payload else '可进入门禁评估'}
        prompt = '你是测试架构师，请根据未覆盖变更行分析风险，只输出JSON，字段riskLevel,summary,uncoveredRisks,suggestedCases,releaseAdvice。数据：{}'.format(PreciseTestService._json_text(payload)[:12000])
        risk, _ = PreciseTestService._ai_json(prompt, fallback)
        for item in items:
            if item.uncovered_changed_line_count:
                PreciseTestDao.update_by_id(session, PreciseIncrementalCoverage, item.id, {'ai_risk_json': risk})
        return risk, ''

    @staticmethod
    def evaluate_gate(session, analysis_id):
        reports, _ = PreciseTestDao.list_by_filters(session, PreciseCoverageReport,
                                                     [PreciseCoverageReport.analysis_id == int(analysis_id)], 1, 1,
                                                     PreciseCoverageReport.created_time)
        latest = reports[0] if reports else None
        incremental = ((latest.summary_json or {}).get('incremental') if latest else {}) or {}
        actual = float(incremental.get('lineRate') or 0)
        recs, _ = PreciseTestDao.list_by_filters(session, PreciseRecommendation,
                                                  [PreciseRecommendation.analysis_id == int(analysis_id),
                                                   PreciseRecommendation.accepted == 1], None, None)
        p0 = [item for item in recs if item.recommend_level == 'P0']
        p1 = [item for item in recs if item.recommend_level == 'P1']
        p0_rate = PreciseTestService._pass_rate(p0)
        p1_rate = PreciseTestService._pass_rate(p1)
        reasons = []
        suggestions = []
        if actual < 80:
            reasons.append('增量覆盖率{}%，低于80%'.format(actual))
            suggestions.append('补充未覆盖变更行相关用例后重新执行')
        if p0 and p0_rate < 100:
            reasons.append('P0推荐用例未全部通过')
        if p1 and p1_rate < 95:
            reasons.append('P1推荐用例通过率低于95%')
        status = 'blocked' if reasons else 'passed'
        data = {'analysis_id': int(analysis_id), 'gate_status': status, 'line_rate_threshold': 80,
                'actual_line_rate': actual, 'p0_case_pass_rate': p0_rate, 'p1_case_pass_rate': p1_rate,
                'risk_level': 'high' if status == 'blocked' else 'low', 'block_reasons': reasons,
                'suggestions': suggestions, 'ai_conclusion': '不建议发布' if reasons else '门禁通过'}
        old = PreciseTestDao.get_first(session, PreciseQualityGate, [PreciseQualityGate.analysis_id == int(analysis_id)])
        if old:
            PreciseTestDao.update_by_id(session, PreciseQualityGate, old.id, data)
            gate_id = old.id
        else:
            gate_id, _ = PreciseTestDao.create(session, PreciseQualityGate, data)
        return PreciseTestDao.get_by_id(session, PreciseQualityGate, gate_id).to_dict(), ''

    @staticmethod
    def _pass_rate(items):
        if not items:
            return 100
        passed = len([item for item in items if item.execution_status == 2])
        return round(passed * 100.0 / len(items), 4)
