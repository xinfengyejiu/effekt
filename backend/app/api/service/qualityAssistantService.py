# encoding: UTF-8
"""对话式质量助手：意图解析 + Tool Calling + 回答编排。"""
from __future__ import print_function

import json
import re
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, or_

from app.api.dao.contractDao import ContractDao
from app.api.dao.inspectionDao import InspectionDao
from app.api.dao.qualityAssistantDao import QualityAssistantDao
from app.api.dao.bugDao import BugDao
from app.api.dao.mobileAutomationDao import MobileAutomationDao
from app.api.model.bugModel import Bug
from app.api.model.caseModel import TestCase
from app.api.model.contractModel import ContractFinding, ContractRun, ContractSuite
from app.api.model.inspectionModel import InspectionExecution
from app.api.model.planModel import TestPlan
from app.api.service.contractExecutionService import ContractExecutionService
from app.api.service.qualityAssistantCatalog import (
    PLATFORM_MODULES, match_module, list_modules_by_group, module_route,
)
from logger import logger

INTENT_WHITELIST = {
    'ask_contract_breaking',
    'ask_contract_drift_summary',
    'ask_inspection_failures',
    'ask_inspection_status',
    'recommend_regression_pack',
    'precheck_release_or_test',
    'run_contract_suite',
    'ask_bug_summary',
    'ask_plan_summary',
    'ask_case_summary',
    'ask_ai_case_rewrite_rate',
    'ask_failure_attribution',
    'ask_report_summary',
    'ask_mobile_summary',
    'ask_performance_summary',
    'start_ai_case_gen',
    'navigate_module',
    'navigate',
    'platform_overview',
    'small_talk_or_help',
    'unsupported',
}

EXAMPLES = [
    {'text': '今天哪些 breaking？', 'intent': 'ask_contract_breaking'},
    {'text': '昨晚巡检挂了什么？', 'intent': 'ask_inspection_failures'},
    {'text': '该跑哪包回归？', 'intent': 'recommend_regression_pack'},
    {'text': '提测前还缺什么？', 'intent': 'precheck_release_or_test'},
    {'text': '当前项目有多少未关闭 Bug？', 'intent': 'ask_bug_summary'},
    {'text': '帮我用最新代码PRD全自动生成用例', 'intent': 'start_ai_case_gen'},
    {'text': '本项目 AI 用例改写率怎么样？', 'intent': 'ask_ai_case_rewrite_rate'},
    {'text': '昨晚失败主要像环境还是用例？', 'intent': 'ask_failure_attribution'},
    {'text': '打开用例管理', 'intent': 'navigate_module'},
    {'text': '平台都能做什么？', 'intent': 'platform_overview'},
]

CASE_GEN_WORKFLOW_EVENTS = {
    'wizard_opened',
    'outline_done',
    'generate_done',
    'import_done',
    'coverage_done',
    'wizard_failed',
}


class QualityAssistantService(object):

    # ── Public API ──────────────────────────────────────────────

    @staticmethod
    def examples():
        return {'items': EXAMPLES}

    @staticmethod
    def get_session_detail(db, session_id, user_id):
        sess = QualityAssistantDao.get_session(db, session_id=session_id, user_id=user_id)
        if not sess:
            return None, '会话不存在'
        messages = QualityAssistantDao.list_messages(db, sess.id)
        return {
            'session': sess.to_dict(),
            'messages': [QualityAssistantService._message_to_dict(m) for m in messages],
        }, ''

    @staticmethod
    def get_latest_session_detail(db, user_id):
        sess = QualityAssistantDao.get_latest_session(db, user_id)
        if not sess:
            return {'session': None, 'messages': []}, ''
        messages = QualityAssistantDao.list_messages(db, sess.id)
        return {
            'session': sess.to_dict(),
            'messages': [QualityAssistantService._message_to_dict(m) for m in messages],
        }, ''

    @staticmethod
    def clear_session(db, session_id, user_id):
        sess = QualityAssistantDao.soft_delete_session(db, session_id, user_id=user_id)
        if not sess:
            return None, '会话不存在'
        db.commit()
        return {'cleared': True, 'session_id': int(session_id)}, ''

    @staticmethod
    def chat(db, body, user):
        body = body or {}
        user_id = user.get('user_id')
        message = (body.get('message') or '').strip()
        if not message:
            return None, '请输入问题'

        product_id = body.get('product_id')
        project_id = body.get('project_id')
        context_in = body.get('context') if isinstance(body.get('context'), dict) else {}

        sess, err = QualityAssistantService._ensure_session(
            db, body.get('session_id') or body.get('session_no'),
            user_id, product_id, project_id, message, context_in,
        )
        if err:
            return None, err

        slots = dict(sess.context or {})
        slots.update({k: v for k, v in context_in.items() if v not in (None, '')})
        if product_id not in (None, ''):
            slots['product_id'] = product_id
        if project_id not in (None, ''):
            slots['project_id'] = project_id
        slots.setdefault('time_range', 'last_24h')

        QualityAssistantDao.create_message(db, {
            'session_id': sess.id,
            'role': 'user',
            'content': message,
        })

        parsed = QualityAssistantService._parse_intent(message, slots)
        intent = parsed.get('intent') or 'unsupported'
        if intent not in INTENT_WHITELIST:
            intent = 'unsupported'
        slots.update(parsed.get('slots') or {})

        if parsed.get('need_clarification') and parsed.get('clarify_question'):
            answer = QualityAssistantService._compose_text(
                intent='small_talk_or_help',
                answer_text=parsed['clarify_question'],
                confidence=0.5,
                suggestions=[e['text'] for e in EXAMPLES[:4]],
            )
            tool_trace = [{'tool': 'clarify', 'input': parsed}]
        else:
            answer, tool_trace = QualityAssistantService._dispatch(db, intent, slots, message, user)

        QualityAssistantDao.create_message(db, {
            'session_id': sess.id,
            'role': 'assistant',
            'content': answer.get('answer_text') or '',
            'intent': intent,
            'tool_trace': tool_trace,
            'answer_payload': answer,
        })
        QualityAssistantDao.update_session(db, sess.id, {
            'context': slots,
            'product_id': slots.get('product_id') or sess.product_id,
            'project_id': slots.get('project_id') or sess.project_id,
            'updated_time': datetime.now(),
        })
        db.commit()

        return {
            'session_id': sess.id,
            'session_no': sess.session_no,
            'intent': intent,
            'answer': answer,
            'tool_trace': tool_trace,
        }, ''

    @staticmethod
    def execute_action(db, body, user):
        body = body or {}
        action_type = body.get('type') or body.get('action_type')
        payload = body.get('payload') if isinstance(body.get('payload'), dict) else {}
        user_id = user.get('user_id')

        if action_type == 'run_contract_suite':
            suite_id = payload.get('suite_id') or body.get('suite_id')
            if not suite_id:
                return None, '缺少 suite_id'
            data, err = ContractExecutionService.trigger_suite_run(
                db, suite_id, trigger_type='manual', user_id=user_id,
            )
            if err:
                return None, err
            run_id = data.get('id') if isinstance(data, dict) else None
            answer = QualityAssistantService._compose_text(
                intent='run_contract_suite',
                answer_text='已触发契约套件执行{}。'.format(
                    '：{}'.format(data.get('run_no')) if isinstance(data, dict) and data.get('run_no') else ''
                ),
                citations=[{
                    'type': 'contract_run',
                    'id': run_id,
                    'title': data.get('run_no') or '契约执行',
                    'route': '/contract/run/detail?id={}'.format(run_id) if run_id else '/contract/runs',
                    'highlights': [],
                }] if run_id else [],
                actions=[{
                    'type': 'navigate',
                    'label': '查看执行详情',
                    'route': '/contract/run/detail?id={}'.format(run_id),
                }] if run_id else [],
                suggestions=['今天哪些 breaking？', '该跑哪包回归？'],
            )
            session_id = body.get('session_id')
            if session_id:
                QualityAssistantDao.create_message(db, {
                    'session_id': int(session_id),
                    'role': 'assistant',
                    'content': answer['answer_text'],
                    'intent': 'run_contract_suite',
                    'tool_trace': [{'tool': 'run_contract_suite', 'input': {'suite_id': suite_id}, 'ok': True}],
                    'answer_payload': answer,
                })
                db.commit()
            return {'action_type': action_type, 'result': data, 'answer': answer}, ''

        if action_type == 'navigate':
            route = payload.get('route') or body.get('route')
            if not route:
                return None, '缺少 route'
            return {'action_type': action_type, 'route': route}, ''

        if action_type == 'set_ai_case_run_mode':
            return QualityAssistantService._action_set_ai_case_run_mode(db, body, payload, user)

        if action_type == 'open_ai_case_wizard':
            return QualityAssistantService._action_open_ai_case_wizard(db, body, payload, user)

        if action_type == 'sync_code_prd':
            return QualityAssistantService._action_sync_code_prd(db, body, payload, user)

        return None, '不支持的动作类型：{}'.format(action_type or '-')

    # ── Session helpers ─────────────────────────────────────────

    @staticmethod
    def _ensure_session(db, session_ref, user_id, product_id, project_id, message, context_in):
        sess = None
        if session_ref not in (None, ''):
            ref = str(session_ref)
            if ref.isdigit():
                sess = QualityAssistantDao.get_session(db, session_id=int(ref), user_id=user_id)
            else:
                sess = QualityAssistantDao.get_session(db, session_no=ref, user_id=user_id)
            if session_ref and not sess:
                return None, '会话不存在或无权访问'

        if not sess:
            session_no = 'QA{}{}'.format(datetime.now().strftime('%Y%m%d%H%M%S'), uuid.uuid4().hex[:6].upper())
            title = message[:40] + ('…' if len(message) > 40 else '')
            sess = QualityAssistantDao.create_session(db, {
                'session_no': session_no,
                'user_id': int(user_id),
                'product_id': int(product_id) if product_id not in (None, '') else None,
                'project_id': int(project_id) if project_id not in (None, '') else None,
                'title': title,
                'context': context_in or {},
            })
            db.flush()
        return sess, ''

    @staticmethod
    def _message_to_dict(msg):
        d = msg.to_dict()
        if isinstance(d.get('answer_payload'), dict):
            d['answer'] = d['answer_payload']
        return d

    # ── Intent ──────────────────────────────────────────────────

    @staticmethod
    def _parse_intent(message, slots):
        rule = QualityAssistantService._rule_intent(message)
        if rule:
            return rule

        try:
            from app.api.service.aiService import AIService
            prompt = (
                '你是效能平台质量助手的意图解析器。只输出 JSON，不要解释。\n'
                '可选 intent：' + ', '.join(sorted(INTENT_WHITELIST)) + '\n'
                '字段：intent, slots(object), need_clarification(bool), clarify_question(string)\n'
                'slots 可含：time_range(today|last_24h|last_7d), domain_keyword, suite_id, severity, module_key, '
                'doc_keyword, prefer_code_prd(bool), run_mode(auto|confirm)\n'
                'module_key 可选：' + ', '.join([m['key'] for m in PLATFORM_MODULES]) + '\n'
                '若用户要打开某模块，intent=navigate_module 并填 module_key。\n'
                '当前已知槽位：' + json.dumps(slots, ensure_ascii=False) + '\n'
                '用户问题：' + message
            )
            parsed, err = AIService.request_json(
                prompt,
                error_prefix='质量助手意图解析',
                temperature=0.1,
                max_tokens=400,
                system_prompt='只返回合法 JSON 对象。',
            )
            if err or not isinstance(parsed, dict):
                logger.warning('quality assistant intent LLM fallback: %s', err)
                return {'intent': 'unsupported', 'slots': {}, 'need_clarification': False}
            intent = parsed.get('intent') or 'unsupported'
            if intent not in INTENT_WHITELIST:
                intent = 'unsupported'
            out_slots = parsed.get('slots') if isinstance(parsed.get('slots'), dict) else {}
            return {
                'intent': intent,
                'slots': out_slots,
                'need_clarification': bool(parsed.get('need_clarification')),
                'clarify_question': parsed.get('clarify_question') or '',
            }
        except Exception as exc:
            logger.warning('quality assistant intent parse error: %s', exc)
            return {'intent': 'unsupported', 'slots': {}, 'need_clarification': False}

    @staticmethod
    def _rule_intent(message):
        text = (message or '').strip().lower()
        raw = message or ''

        if re.search(r'(平台.*(功能|模块|覆盖)|都有哪些功能|功能清单|全平台|平台都能做什么)', raw, re.I):
            return {'intent': 'platform_overview', 'slots': {}}

        if re.search(r'(你能做|你会什么|帮助|help|能做什么)', raw, re.I):
            return {'intent': 'small_talk_or_help', 'slots': {}}

        # AI 生成用例须先于「用例统计」，避免「生成测试用例」落到 ask_case_summary
        if re.search(
            r'(生成|写|出).{0,8}(用例|测试用例)|AI\s*生成用例|按.*(PRD|需求|文档).*(生成|写).*用例|'
            r'(代码\s*PRD|代码转PRD).{0,12}(生成|写).{0,6}用例|(大纲|测点).{0,8}(生成|精写)',
            raw,
            re.I,
        ):
            return {
                'intent': 'start_ai_case_gen',
                'slots': QualityAssistantService._slot_case_gen(raw),
            }

        if re.search(r'(提测|发布).*(缺|检查|门禁|就绪)|precheck|提测前', raw, re.I):
            return {'intent': 'precheck_release_or_test', 'slots': {}}

        if re.search(r'(回归|冒烟).*(包|范围|跑什么|推荐)|该跑哪|跑哪包', raw, re.I):
            return {'intent': 'recommend_regression_pack', 'slots': {}}

        if re.search(r'(跑|执行|重跑).*(契约|套件)|run.*(suite|contract)', raw, re.I):
            m = re.search(r'(?:套件|suite)[^\d]*(\d+)', raw, re.I)
            slots = {}
            if m:
                slots['suite_id'] = int(m.group(1))
            return {
                'intent': 'run_contract_suite',
                'slots': slots,
                'need_clarification': 'suite_id' not in slots,
                'clarify_question': '请指定要执行的契约套件 id，或先问「今天哪些 breaking？」从结果里点重跑。',
            }

        if re.search(r'breaking|漂移|契约.*(红|挂|异常|问题)|接口漂移', raw, re.I):
            if re.search(r'稳不稳|汇总|趋势|概览|summary', raw, re.I):
                return {'intent': 'ask_contract_drift_summary', 'slots': QualityAssistantService._slot_time(raw)}
            return {'intent': 'ask_contract_breaking', 'slots': QualityAssistantService._slot_time(raw)}

        if re.search(r'巡检', raw):
            if re.search(r'(绿|状态|都过|通过吗|status)', raw, re.I):
                return {'intent': 'ask_inspection_status', 'slots': QualityAssistantService._slot_time(raw)}
            return {'intent': 'ask_inspection_failures', 'slots': QualityAssistantService._slot_time(raw)}

        if re.search(r'\bbug\b|缺陷|问题单', raw, re.I):
            return {'intent': 'ask_bug_summary', 'slots': QualityAssistantService._slot_time(raw)}

        if re.search(r'测试计划|计划.*(列表|状态|多少)|有哪些计划', raw, re.I):
            return {'intent': 'ask_plan_summary', 'slots': {}}

        if re.search(r'改写率|废稿率|直通率|AI\s*用例.*(改|废)|生成.*(改了多少|被人改)', raw, re.I):
            return {'intent': 'ask_ai_case_rewrite_rate', 'slots': {}}

        if re.search(r'(失败|挂了).*(环境|用例|代码|数据|根因|归因)|(像环境还是用例)|失败归因|根因分类', raw, re.I):
            return {'intent': 'ask_failure_attribution', 'slots': QualityAssistantService._slot_time(raw)}

        if re.search(r'用例.*(多少|统计|汇总)|有多少.*用例', raw, re.I):
            return {'intent': 'ask_case_summary', 'slots': {}}

        if re.search(r'测试报告|报告.*(列表|最近)', raw, re.I):
            return {'intent': 'ask_report_summary', 'slots': {}}

        if re.search(r'移动自动化|移动执行|app.*(失败|执行)', raw, re.I):
            return {'intent': 'ask_mobile_summary', 'slots': QualityAssistantService._slot_time(raw)}

        if re.search(r'性能.*(测试|压测|场景|执行|报告)|压测', raw, re.I):
            return {'intent': 'ask_performance_summary', 'slots': {}}

        # 打开 / 去某某模块
        if re.search(r'^(打开|进入|去|跳转|查看)\s*', raw) or re.search(r'打开|进入|跳到', raw):
            mod = match_module(raw)
            if mod:
                return {'intent': 'navigate_module', 'slots': {'module_key': mod['key']}}

        if re.search(r'打开|跳转|详情', raw) and re.search(r'\d+', raw):
            m = re.search(r'(\d+)', raw)
            return {
                'intent': 'navigate',
                'slots': {'run_id': int(m.group(1))} if m else {},
            }

        domain = None
        for kw in ('支付', '交易', '订单', '用户', '网关', '登录'):
            if kw in raw:
                domain = kw
                break
        if domain and re.search(r'(只看|相关|过滤)', raw):
            return {
                'intent': 'ask_contract_breaking',
                'slots': dict(QualityAssistantService._slot_time(raw), domain_keyword=domain),
            }

        if text in {e['text'].lower() for e in EXAMPLES}:
            for e in EXAMPLES:
                if e['text'].lower() == text:
                    return {'intent': e['intent'], 'slots': {}}

        # 未命中专用意图时：若命中平台模块，则导航/引导，而不是 unsupported
        mod = match_module(raw)
        if mod:
            caps = mod.get('capability') or []
            if 'query' in caps and mod['key'] == 'bug':
                return {'intent': 'ask_bug_summary', 'slots': {}}
            if 'query' in caps and mod['key'] == 'plan':
                return {'intent': 'ask_plan_summary', 'slots': {}}
            if 'query' in caps and mod['key'] == 'case':
                return {'intent': 'ask_case_summary', 'slots': {}}
            if 'query' in caps and mod['key'] == 'report':
                return {'intent': 'ask_report_summary', 'slots': {}}
            if 'query' in caps and mod['key'] == 'mobile':
                return {'intent': 'ask_mobile_summary', 'slots': {}}
            if 'query' in caps and mod['key'] == 'performance':
                return {'intent': 'ask_performance_summary', 'slots': {}}
            if 'query' in caps and mod['key'] == 'contract':
                return {'intent': 'ask_contract_drift_summary', 'slots': QualityAssistantService._slot_time(raw)}
            if 'query' in caps and mod['key'] == 'inspection':
                return {'intent': 'ask_inspection_status', 'slots': QualityAssistantService._slot_time(raw)}
            return {'intent': 'navigate_module', 'slots': {'module_key': mod['key']}}

        return None

    @staticmethod
    def _slot_time(raw):
        if re.search(r'今天|今日', raw):
            return {'time_range': 'today'}
        if re.search(r'昨晚|昨天|近\s*24|24\s*小时', raw):
            return {'time_range': 'last_24h'}
        if re.search(r'近\s*7|一周|7\s*天', raw):
            return {'time_range': 'last_7d'}
        return {}

    # ── Dispatch / Tools ────────────────────────────────────────

    @staticmethod
    def _dispatch(db, intent, slots, message, user):
        handlers = {
            'ask_contract_breaking': QualityAssistantService._tool_contract_breaking,
            'ask_contract_drift_summary': QualityAssistantService._tool_contract_summary,
            'ask_inspection_failures': QualityAssistantService._tool_inspection_failures,
            'ask_inspection_status': QualityAssistantService._tool_inspection_status,
            'recommend_regression_pack': QualityAssistantService._tool_regression_pack,
            'precheck_release_or_test': QualityAssistantService._tool_precheck,
            'run_contract_suite': QualityAssistantService._tool_run_suite_suggest,
            'ask_bug_summary': QualityAssistantService._tool_bug_summary,
            'ask_plan_summary': QualityAssistantService._tool_plan_summary,
            'ask_case_summary': QualityAssistantService._tool_case_summary,
            'ask_ai_case_rewrite_rate': QualityAssistantService._tool_ai_case_rewrite_rate,
            'ask_failure_attribution': QualityAssistantService._tool_failure_attribution,
            'ask_report_summary': QualityAssistantService._tool_report_summary,
            'ask_mobile_summary': QualityAssistantService._tool_mobile_summary,
            'ask_performance_summary': QualityAssistantService._tool_performance_summary,
            'start_ai_case_gen': QualityAssistantService._tool_start_ai_case_gen,
            'navigate_module': QualityAssistantService._tool_navigate_module,
            'navigate': QualityAssistantService._tool_navigate,
            'platform_overview': QualityAssistantService._tool_platform_overview,
            'small_talk_or_help': QualityAssistantService._tool_help,
            'unsupported': QualityAssistantService._tool_unsupported,
        }
        handler = handlers.get(intent) or QualityAssistantService._tool_unsupported
        return handler(db, slots, message, user)

    @staticmethod
    def _time_window(slots):
        tr = (slots or {}).get('time_range') or 'last_24h'
        now = datetime.now()
        if tr == 'today':
            start = datetime(now.year, now.month, now.day)
        elif tr == 'last_7d':
            start = now - timedelta(days=7)
        else:
            start = now - timedelta(hours=24)
            tr = 'last_24h'
        return start, now, tr

    @staticmethod
    def _require_project(slots):
        pid = (slots or {}).get('project_id')
        if pid in (None, ''):
            return None, '请先选择项目上下文（product/project），再问质量问题。'
        return int(pid), ''

    @staticmethod
    def _tool_contract_breaking(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_contract_breaking', answer_text=err, confidence=0.4,
                suggestions=['选择项目后重试：今天哪些 breaking？'],
            ), [{'tool': 'list_contract_breaking', 'error': err}]

        start, end, tr = QualityAssistantService._time_window(slots)
        domain = (slots.get('domain_keyword') or '').strip()
        runs = db.query(ContractRun).filter(
            ContractRun.project_id == project_id,
            ContractRun.created_time >= start,
            ContractRun.created_time <= end,
            ContractRun.breaking_count > 0,
        ).order_by(ContractRun.id.desc()).limit(30).all()

        citations = []
        total_breaking = 0
        suite_names = []
        for run in runs:
            suite = ContractDao.get_suite(db, run.suite_id)
            suite_name = suite.name if suite else '套件#{}'.format(run.suite_id)
            if domain and domain not in suite_name and domain not in (run.run_no or ''):
                # also check findings paths later
                pass
            findings = db.query(ContractFinding).filter(
                ContractFinding.run_id == run.id,
                ContractFinding.severity == 'breaking',
            ).order_by(ContractFinding.id.asc()).limit(8).all()
            highlights = []
            for f in findings:
                if domain and domain not in suite_name and domain not in (f.json_path or '') and domain not in (f.message or ''):
                    continue
                highlights.append('{} {}'.format(f.json_path or '', f.drift_type or '').strip())
            if domain and not highlights and domain not in suite_name:
                continue
            if not findings and domain:
                continue
            total_breaking += int(run.breaking_count or 0)
            suite_names.append(suite_name)
            citations.append({
                'type': 'contract_run',
                'id': run.id,
                'title': '{} · {}'.format(suite_name, run.run_no),
                'route': '/contract/run/detail?id={}'.format(run.id),
                'highlights': highlights[:5] or ['breaking_count={}'.format(run.breaking_count)],
                'suite_id': run.suite_id,
                'breaking_count': run.breaking_count,
            })

        if domain:
            # recount only matching citations
            total_breaking = sum(int(c.get('breaking_count') or 0) for c in citations)

        if not citations:
            text = '近 {} 未查到契约 breaking{}。'.format(
                QualityAssistantService._tr_label(tr),
                '（关键词：{}）'.format(domain) if domain else '',
            )
            return QualityAssistantService._compose_text(
                intent='ask_contract_breaking',
                answer_text=text,
                confidence=0.9,
                suggestions=['契约最近稳不稳？', '昨晚巡检挂了什么？', '该跑哪包回归？'],
            ), [{'tool': 'list_contract_breaking', 'input': {'project_id': project_id, 'time_range': tr, 'domain': domain}, 'count': 0}]

        top = '、'.join(list(dict.fromkeys(suite_names))[:3])
        text = '近 {} 发现 {} 次执行含 breaking，合计 breaking 计数 {}，主要集中在 {}。'.format(
            QualityAssistantService._tr_label(tr), len(citations), total_breaking, top or '相关套件',
        )
        actions = []
        for c in citations[:3]:
            actions.append({'type': 'navigate', 'label': '查看 {}'.format(c['title'][:18]), 'route': c['route']})
            if c.get('suite_id'):
                actions.append({
                    'type': 'run_contract_suite',
                    'label': '重跑套件 #{}'.format(c['suite_id']),
                    'payload': {'suite_id': c['suite_id']},
                })
        return QualityAssistantService._compose_text(
            intent='ask_contract_breaking',
            answer_text=text,
            confidence=0.92,
            citations=citations[:10],
            actions=actions[:6],
            suggestions=['只看支付相关', '该跑哪包回归？', '提测前还缺什么？'],
        ), [{'tool': 'list_contract_breaking', 'input': {'project_id': project_id, 'time_range': tr}, 'count': len(citations)}]

    @staticmethod
    def _tool_contract_summary(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_contract_drift_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'summarize_contract_runs', 'error': err}]

        start, end, tr = QualityAssistantService._time_window(slots)
        rows = db.query(
            func.count(ContractRun.id),
            func.coalesce(func.sum(ContractRun.pass_count), 0),
            func.coalesce(func.sum(ContractRun.drift_count), 0),
            func.coalesce(func.sum(ContractRun.error_count), 0),
            func.coalesce(func.sum(ContractRun.breaking_count), 0),
        ).filter(
            ContractRun.project_id == project_id,
            ContractRun.created_time >= start,
            ContractRun.created_time <= end,
        ).one()
        run_count, pass_c, drift_c, err_c, br_c = [int(x or 0) for x in rows]

        top_suites = db.query(
            ContractSuite.name,
            func.sum(ContractRun.breaking_count).label('bc'),
            func.count(ContractRun.id).label('rc'),
        ).join(ContractRun, ContractRun.suite_id == ContractSuite.id).filter(
            ContractRun.project_id == project_id,
            ContractRun.created_time >= start,
            ContractRun.created_time <= end,
        ).group_by(ContractSuite.name).order_by(func.sum(ContractRun.breaking_count).desc()).limit(5).all()

        if run_count == 0:
            text = '近 {} 没有契约执行记录。'.format(QualityAssistantService._tr_label(tr))
        else:
            text = (
                '近 {} 共 {} 次契约执行：pass 项合计 {}，drift {}，error {}，breaking 计数 {}。'
            ).format(QualityAssistantService._tr_label(tr), run_count, pass_c, drift_c, err_c, br_c)
            if top_suites:
                tops = '；'.join(['{}(breaking={})'.format(n, int(bc or 0)) for n, bc, _ in top_suites[:3]])
                text += ' Top 套件：{}。'.format(tops)

        citations = [{
            'type': 'contract_summary',
            'id': project_id,
            'title': '契约执行汇总',
            'route': '/contract/runs?project_id={}'.format(project_id),
            'highlights': [
                'runs={}'.format(run_count),
                'breaking={}'.format(br_c),
            ],
        }]
        return QualityAssistantService._compose_text(
            intent='ask_contract_drift_summary',
            answer_text=text,
            confidence=0.9,
            citations=citations,
            actions=[{'type': 'navigate', 'label': '打开执行记录', 'route': '/contract/runs?project_id={}'.format(project_id)}],
            suggestions=['今天哪些 breaking？', '该跑哪包回归？'],
        ), [{'tool': 'summarize_contract_runs', 'input': {'project_id': project_id, 'time_range': tr}, 'stats': {
            'runs': run_count, 'breaking': br_c,
        }}]

    @staticmethod
    def _tool_inspection_failures(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_inspection_failures', answer_text=err, confidence=0.4,
            ), [{'tool': 'list_inspection_failures', 'error': err}]

        start, end, tr = QualityAssistantService._time_window(slots)
        # status: 3部分失败 4全部失败 5异常
        executions = db.query(InspectionExecution).filter(
            InspectionExecution.project_id == project_id,
            InspectionExecution.created_time >= start,
            InspectionExecution.created_time <= end,
            InspectionExecution.status.in_([3, 4, 5]),
        ).order_by(InspectionExecution.id.desc()).limit(20).all()

        citations = []
        for ex in executions:
            name = ''
            if ex.task_id:
                task = InspectionDao.get_task(db, ex.task_id)
                name = task.name if task else '任务#{}'.format(ex.task_id)
            elif ex.group_id:
                group = InspectionDao.get_group(db, ex.group_id)
                name = group.name if group else '组#{}'.format(ex.group_id)
            fail_items = InspectionDao.list_execution_items(db, ex.id)
            highlights = []
            for it in fail_items:
                if int(getattr(it, 'status', 0) or 0) in (3, 4):
                    result = it.result if isinstance(getattr(it, 'result', None), dict) else {}
                    label = result.get('name') or result.get('item_name') or '{}#{}'.format(it.item_type or 'item', it.id)
                    highlights.append(str(label)[:80])
                    ai_reason = result.get('ai_reason') or result.get('root_cause') or result.get('reason')
                    if ai_reason:
                        highlights.append('AI: {}'.format(str(ai_reason)[:80]))
                    elif it.error_message:
                        highlights.append(str(it.error_message)[:80])
            citations.append({
                'type': 'inspection_execution',
                'id': ex.id,
                'title': '{} · fail={}/error={}'.format(name, ex.fail_count or 0, ex.error_count or 0),
                'route': '/inspection/execution/detail?id={}'.format(ex.id),
                'highlights': highlights[:5],
            })

        if not citations:
            text = '近 {} 未查到失败/异常巡检执行。'.format(QualityAssistantService._tr_label(tr))
        else:
            text = '近 {} 有 {} 次巡检失败或异常。'.format(QualityAssistantService._tr_label(tr), len(citations))

        actions = [{'type': 'navigate', 'label': '查看 {}'.format(c['title'][:20]), 'route': c['route']} for c in citations[:4]]
        return QualityAssistantService._compose_text(
            intent='ask_inspection_failures',
            answer_text=text,
            confidence=0.9,
            citations=citations[:10],
            actions=actions,
            suggestions=['核心巡检都绿吗？', '该跑哪包回归？', '今天哪些 breaking？'],
        ), [{'tool': 'list_inspection_failures', 'input': {'project_id': project_id, 'time_range': tr}, 'count': len(citations)}]

    @staticmethod
    def _tool_inspection_status(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_inspection_status', answer_text=err, confidence=0.4,
            ), [{'tool': 'list_inspection_status', 'error': err}]

        start, end, tr = QualityAssistantService._time_window(slots)
        executions = db.query(InspectionExecution).filter(
            InspectionExecution.project_id == project_id,
            InspectionExecution.created_time >= start,
            InspectionExecution.created_time <= end,
            InspectionExecution.status.in_([2, 3, 4, 5]),
        ).order_by(InspectionExecution.id.desc()).limit(40).all()

        green = [e for e in executions if int(e.status) == 2]
        red = [e for e in executions if int(e.status) in (3, 4, 5)]
        text = '近 {} 巡检：通过 {} 次，失败/异常 {} 次。'.format(
            QualityAssistantService._tr_label(tr), len(green), len(red),
        )
        if not executions:
            text = '近 {} 暂无已完成的巡检执行。'.format(QualityAssistantService._tr_label(tr))

        citations = []
        for e in (red + green)[:8]:
            citations.append({
                'type': 'inspection_execution',
                'id': e.id,
                'title': 'execution#{} status={}'.format(e.id, e.status),
                'route': '/inspection/execution/detail?id={}'.format(e.id),
                'highlights': ['fail={}'.format(e.fail_count or 0)],
            })
        return QualityAssistantService._compose_text(
            intent='ask_inspection_status',
            answer_text=text,
            confidence=0.88,
            citations=citations,
            actions=[{'type': 'navigate', 'label': '打开巡检执行', 'route': '/inspection/executions'}],
            suggestions=['昨晚巡检挂了什么？', '提测前还缺什么？'],
        ), [{'tool': 'list_inspection_status', 'stats': {'green': len(green), 'red': len(red)}}]

    @staticmethod
    def _tool_regression_pack(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='recommend_regression_pack', answer_text=err, confidence=0.4,
            ), [{'tool': 'recommend_regression_pack', 'error': err}]

        start, end, tr = QualityAssistantService._time_window(slots)
        breaking_runs = db.query(ContractRun).filter(
            ContractRun.project_id == project_id,
            ContractRun.created_time >= start,
            ContractRun.breaking_count > 0,
        ).order_by(ContractRun.id.desc()).limit(20).all()

        suite_map = {}
        for run in breaking_runs:
            suite = ContractDao.get_suite(db, run.suite_id)
            if suite:
                suite_map[suite.id] = suite.name

        fail_ex = db.query(InspectionExecution).filter(
            InspectionExecution.project_id == project_id,
            InspectionExecution.created_time >= start,
            InspectionExecution.status.in_([3, 4, 5]),
        ).order_by(InspectionExecution.id.desc()).limit(15).all()

        plans = db.query(TestPlan).filter(
            TestPlan.project_id == project_id,
            TestPlan.is_delete == 0,
            or_(
                TestPlan.name.ilike('%回归%'),
                TestPlan.name.ilike('%冒烟%'),
                TestPlan.is_auto == 1,
            ),
        ).order_by(TestPlan.id.desc()).limit(10).all()

        min_items = []
        for sid, name in suite_map.items():
            min_items.append('契约套件：{} (#{})'.format(name, sid))
        for ex in fail_ex[:5]:
            min_items.append('巡检失败执行 #{}'.format(ex.id))
        if not min_items:
            min_items.append('近窗内无 breaking / 巡检红灯，建议跑项目默认冒烟计划（若有）')

        full_items = list(min_items)
        for p in plans:
            full_items.append('计划：{} (#{})'.format(p.name, p.id))
        if not plans:
            full_items.append('未找到名称含「回归/冒烟」的计划，请到计划页手工挑选完整回归集')

        text = (
            '基于近 {} 的契约 breaking 与巡检红灯，建议：\n'
            '【最小回归包】{}\n'
            '【完整回归包】{}'
        ).format(
            QualityAssistantService._tr_label(tr),
            '；'.join(min_items[:8]),
            '；'.join(full_items[:12]),
        )

        citations = []
        for sid, name in list(suite_map.items())[:5]:
            citations.append({
                'type': 'contract_suite',
                'id': sid,
                'title': name,
                'route': '/contract/suite/edit?id={}'.format(sid),
                'highlights': ['纳入最小回归包'],
            })
        for p in plans[:3]:
            citations.append({
                'type': 'test_plan',
                'id': p.id,
                'title': p.name,
                'route': '/test-platform/plan?projectId={}'.format(project_id),
                'highlights': ['完整回归候选'],
            })

        actions = [
            {'type': 'navigate', 'label': '打开契约套件', 'route': '/contract/suites'},
            {'type': 'navigate', 'label': '打开测试计划', 'route': '/test-platform/plan?projectId={}'.format(project_id)},
        ]
        for sid in list(suite_map.keys())[:2]:
            actions.append({
                'type': 'run_contract_suite',
                'label': '重跑套件 #{}'.format(sid),
                'payload': {'suite_id': sid},
            })

        return QualityAssistantService._compose_text(
            intent='recommend_regression_pack',
            answer_text=text,
            confidence=0.85,
            citations=citations,
            actions=actions,
            suggestions=['提测前还缺什么？', '今天哪些 breaking？'],
        ), [{'tool': 'recommend_regression_pack', 'min_count': len(min_items), 'full_count': len(full_items)}]

    @staticmethod
    def _tool_precheck(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='precheck_release_or_test', answer_text=err, confidence=0.4,
            ), [{'tool': 'precheck', 'error': err}]

        start, end, tr = QualityAssistantService._time_window(
            dict(slots, time_range=slots.get('time_range') or 'last_24h')
        )
        br = db.query(func.coalesce(func.sum(ContractRun.breaking_count), 0)).filter(
            ContractRun.project_id == project_id,
            ContractRun.created_time >= start,
            ContractRun.created_time <= end,
        ).scalar()
        br = int(br or 0)

        red = db.query(func.count(InspectionExecution.id)).filter(
            InspectionExecution.project_id == project_id,
            InspectionExecution.created_time >= start,
            InspectionExecution.status.in_([3, 4, 5]),
        ).scalar()
        red = int(red or 0)

        must_plans = db.query(TestPlan).filter(
            TestPlan.project_id == project_id,
            TestPlan.is_delete == 0,
            or_(TestPlan.name.ilike('%必跑%'), TestPlan.name.ilike('%冒烟%')),
        ).limit(5).all()

        blockers = []
        warnings = []
        passed = []

        if br > 0:
            blockers.append('契约 breaking 计数 {}（近 {}）'.format(br, QualityAssistantService._tr_label(tr)))
        else:
            passed.append('近 {} 无契约 breaking'.format(QualityAssistantService._tr_label(tr)))

        if red > 0:
            blockers.append('巡检失败/异常 {} 次'.format(red))
        else:
            passed.append('近 {} 无巡检失败/异常'.format(QualityAssistantService._tr_label(tr)))

        if must_plans:
            for p in must_plans:
                if int(p.status or 0) == 2:  # 失败? plan status: 0草稿1进行中2已完成3归档4通过 — 无法精确知最近执行，作警告
                    warnings.append('计划「{}」请确认最近一轮已通过'.format(p.name))
                else:
                    warnings.append('必跑/冒烟计划「{}」当前状态={}'.format(p.name, p.status))
        else:
            warnings.append('未配置名称含「必跑/冒烟」的计划，已跳过计划门禁')

        if blockers:
            text = '提测前检查：存在 {} 个阻塞项。'.format(len(blockers))
        elif warnings:
            text = '提测前检查：无硬性阻塞，但有 {} 个警告项需确认。'.format(len(warnings))
        else:
            text = '提测前检查：当前窗内门禁项均已通过。'

        lines = []
        for x in blockers:
            lines.append('阻塞：' + x)
        for x in warnings:
            lines.append('警告：' + x)
        for x in passed:
            lines.append('通过：' + x)
        text = text + '\n' + '\n'.join(lines)

        return QualityAssistantService._compose_text(
            intent='precheck_release_or_test',
            answer_text=text,
            confidence=0.87,
            citations=[{
                'type': 'precheck',
                'id': project_id,
                'title': '提测前门禁',
                'route': '/contract/runs?project_id={}'.format(project_id),
                'highlights': blockers[:3] or passed[:2],
            }],
            actions=[
                {'type': 'navigate', 'label': '查看契约执行', 'route': '/contract/runs?project_id={}'.format(project_id)},
                {'type': 'navigate', 'label': '查看巡检执行', 'route': '/inspection/executions'},
            ],
            suggestions=['今天哪些 breaking？', '该跑哪包回归？'],
        ), [{'tool': 'precheck', 'blockers': blockers, 'warnings': warnings, 'passed': passed}]

    @staticmethod
    def _tool_run_suite_suggest(db, slots, message, user):
        suite_id = slots.get('suite_id')
        if not suite_id:
            return QualityAssistantService._compose_text(
                intent='run_contract_suite',
                answer_text='请提供套件 id，或先查询 breaking 后点击「重跑该套件」。写操作需二次确认。',
                confidence=0.6,
                suggestions=['今天哪些 breaking？'],
            ), [{'tool': 'run_contract_suite', 'need_suite_id': True}]

        suite = ContractDao.get_suite(db, suite_id)
        if not suite:
            return QualityAssistantService._compose_text(
                intent='run_contract_suite',
                answer_text='套件 #{} 不存在。'.format(suite_id),
                confidence=0.9,
            ), [{'tool': 'run_contract_suite', 'error': 'not_found'}]

        return QualityAssistantService._compose_text(
            intent='run_contract_suite',
            answer_text='准备执行契约套件「{}」(#{})。请确认后点击下方按钮。'.format(suite.name, suite.id),
            confidence=0.9,
            actions=[{
                'type': 'run_contract_suite',
                'label': '确认执行 {}'.format(suite.name),
                'payload': {'suite_id': suite.id},
            }],
            suggestions=['执行后问：今天哪些 breaking？'],
        ), [{'tool': 'run_contract_suite', 'prepared': True, 'suite_id': suite.id}]

    @staticmethod
    def _tool_navigate(db, slots, message, user):
        run_id = slots.get('run_id')
        if run_id:
            route = '/contract/run/detail?id={}'.format(run_id)
            return QualityAssistantService._compose_text(
                intent='navigate',
                answer_text='可以打开契约执行 #{} 详情。'.format(run_id),
                actions=[{'type': 'navigate', 'label': '打开详情', 'route': route}],
                citations=[{'type': 'contract_run', 'id': run_id, 'title': 'run#{}'.format(run_id), 'route': route, 'highlights': []}],
            ), [{'tool': 'navigate', 'route': route}]
        return QualityAssistantService._tool_navigate_module(db, slots, message, user)

    @staticmethod
    def _tool_navigate_module(db, slots, message, user):
        key = (slots or {}).get('module_key')
        mod = None
        if key:
            for item in PLATFORM_MODULES:
                if item['key'] == key:
                    mod = item
                    break
        if not mod:
            mod = match_module(message or '')
        if not mod:
            return QualityAssistantService._tool_platform_overview(db, slots, message, user)

        route = module_route(mod, project_id=(slots or {}).get('project_id'), product_id=(slots or {}).get('product_id'))
        caps = mod.get('capability') or []
        cap_text = '、'.join([
            {'navigate': '跳转', 'query': '只读查询', 'action': '受限写操作'}.get(c, c) for c in caps
        ])
        return QualityAssistantService._compose_text(
            intent='navigate_module',
            answer_text='已定位到「{}」（{}）。当前能力：{}。'.format(mod['name'], mod.get('group') or '', cap_text or '跳转'),
            confidence=0.9,
            citations=[{
                'type': 'platform_module',
                'id': mod['key'],
                'title': mod['name'],
                'route': route,
                'highlights': caps,
            }],
            actions=[{'type': 'navigate', 'label': '打开{}'.format(mod['name']), 'route': route}],
            suggestions=['平台都能做什么？', '今天哪些 breaking？', '当前项目有多少未关闭 Bug？'],
        ), [{'tool': 'navigate_module', 'module': mod['key'], 'route': route}]

    @staticmethod
    def _tool_platform_overview(db, slots, message, user):
        groups = list_modules_by_group()
        lines = ['效能平台能力覆盖以下模块（可说「打开XX」或直接问状态）：']
        actions = []
        for group, mods in groups.items():
            names = '、'.join([m['name'] for m in mods])
            lines.append('· {}：{}'.format(group, names))
        for key in ('contract', 'inspection', 'bug', 'plan', 'case', 'ai_platform'):
            mod = next((m for m in PLATFORM_MODULES if m['key'] == key), None)
            if mod:
                actions.append({
                    'type': 'navigate',
                    'label': mod['name'],
                    'route': module_route(mod, project_id=(slots or {}).get('project_id')),
                })
        return QualityAssistantService._compose_text(
            intent='platform_overview',
            answer_text='\n'.join(lines),
            confidence=1.0,
            actions=actions[:6],
            suggestions=['打开精准测试', '当前项目有多少未关闭 Bug？', '今天哪些 breaking？'],
        ), [{'tool': 'platform_overview', 'module_count': len(PLATFORM_MODULES)}]

    @staticmethod
    def _tool_bug_summary(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_bug_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_bug_summary', 'error': err}]
        product_id = (slots or {}).get('product_id')
        stats = BugDao.get_stats(db, product_id=product_id, project_id=project_id)
        open_count = int(stats.get('new') or 0) + int(stats.get('pending') or 0) + int(stats.get('in_progress') or 0)
        text = (
            '当前项目 Bug 统计：共 {} 个；未关闭约 {} 个'
            '（新建 {} / 待处理 {} / 处理中 {}）；已解决 {}，已关闭 {}，已拒绝 {}。'
        ).format(
            stats.get('total') or 0,
            open_count,
            stats.get('new') or 0,
            stats.get('pending') or 0,
            stats.get('in_progress') or 0,
            stats.get('resolved') or 0,
            stats.get('closed') or 0,
            stats.get('rejected') or 0,
        )
        recent = db.query(Bug).filter(
            Bug.is_delete == 0, Bug.project_id == project_id,
        ).order_by(Bug.id.desc()).limit(5).all()
        citations = []
        for b in recent:
            citations.append({
                'type': 'bug',
                'id': b.id,
                'title': b.title or 'Bug#{}'.format(b.id),
                'route': '/bug/detail?id={}'.format(b.id),
                'highlights': ['status={}'.format(b.status)],
            })
        return QualityAssistantService._compose_text(
            intent='ask_bug_summary',
            answer_text=text,
            confidence=0.9,
            citations=citations,
            actions=[
                {'type': 'navigate', 'label': '打开 Bug 列表', 'route': '/bug/list?projectId={}'.format(project_id)},
                {'type': 'navigate', 'label': 'Bug 统计', 'route': '/bug/stats'},
            ],
            suggestions=['提测前还缺什么？', '打开测试计划', '今天哪些 breaking？'],
        ), [{'tool': 'ask_bug_summary', 'total': stats.get('total'), 'open': open_count}]

    @staticmethod
    def _tool_plan_summary(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_plan_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_plan_summary', 'error': err}]
        plans = db.query(TestPlan).filter(
            TestPlan.project_id == project_id, TestPlan.is_delete == 0,
        ).order_by(TestPlan.id.desc()).limit(20).all()
        status_map = {0: '草稿', 1: '进行中', 2: '已完成', 3: '已归档', 4: '已通过'}
        if not plans:
            text = '当前项目暂无测试计划。'
        else:
            buckets = {}
            for p in plans:
                buckets[p.status] = buckets.get(p.status, 0) + 1
            parts = ['{} {}'.format(status_map.get(k, k), v) for k, v in sorted(buckets.items())]
            text = '当前项目最近 {} 条计划：{}。'.format(len(plans), '，'.join(parts))
        citations = [{
            'type': 'test_plan',
            'id': p.id,
            'title': p.name,
            'route': '/test-platform/plan?projectId={}'.format(project_id),
            'highlights': [status_map.get(p.status, str(p.status))],
        } for p in plans[:8]]
        return QualityAssistantService._compose_text(
            intent='ask_plan_summary',
            answer_text=text,
            confidence=0.9,
            citations=citations,
            actions=[{'type': 'navigate', 'label': '打开测试计划', 'route': '/test-platform/plan?projectId={}'.format(project_id)}],
            suggestions=['该跑哪包回归？', '当前项目有多少未关闭 Bug？'],
        ), [{'tool': 'ask_plan_summary', 'count': len(plans)}]

    @staticmethod
    def _tool_case_summary(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_case_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_case_summary', 'error': err}]
        base = db.query(TestCase).filter(TestCase.project_id == project_id, TestCase.is_delete == 0)
        total = base.count()
        auto_n = base.filter(TestCase.is_auto == 1).count()
        ai_n = base.filter(TestCase.is_ai_generated == 1).count()
        text = '当前项目用例共 {} 条；其中已自动化 {}，AI 生成 {}。'.format(total, auto_n, ai_n)
        return QualityAssistantService._compose_text(
            intent='ask_case_summary',
            answer_text=text,
            confidence=0.9,
            citations=[{
                'type': 'case_summary',
                'id': project_id,
                'title': '用例汇总',
                'route': '/test-platform/case?projectId={}'.format(project_id),
                'highlights': ['total={}'.format(total), 'auto={}'.format(auto_n)],
            }],
            actions=[{'type': 'navigate', 'label': '打开用例管理', 'route': '/test-platform/case?projectId={}'.format(project_id)}],
            suggestions=['本项目 AI 用例改写率怎么样？', '打开测试计划'],
        ), [{'tool': 'ask_case_summary', 'total': total}]

    @staticmethod
    def _tool_ai_case_rewrite_rate(db, slots, message, user):
        from app.api.service.aiCaseQualityService import AiCaseQualityService
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_ai_case_rewrite_rate', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_ai_case_rewrite_rate', 'error': err}]
        data, serr = AiCaseQualityService.summary(db, project_id)
        if serr:
            return QualityAssistantService._compose_text(
                intent='ask_ai_case_rewrite_rate', answer_text=serr, confidence=0.4,
            ), [{'tool': 'ask_ai_case_rewrite_rate', 'error': serr}]
        tracked = data.get('trackedCount') or 0
        if not tracked:
            text = (
                '当前项目尚无「带入库原貌」的 AI 用例，改写率自本版本起算。'
                '请先走 AI 生成并确认导入，再编辑几条后回来看改写率。'
            )
            if data.get('legacyAiCount'):
                text += '（存量 AI 用例 {} 条未纳入改写率分母）'.format(data.get('legacyAiCount'))
        else:
            def _pct(v):
                return '{}%'.format(int(round(float(v) * 100))) if v is not None else '—'
            text = (
                '本项目 AI 用例质量（有原貌样本 {} 条）：改写率 {}，废稿率 {}，直通率 {}。'
                '改写 {} / 废稿 {} / 未改 {}。'
            ).format(
                tracked,
                _pct(data.get('rewriteRate')),
                _pct(data.get('abandonRate')),
                _pct(data.get('passThroughRate')),
                data.get('rewrittenCount') or 0,
                data.get('abandonedCount') or 0,
                data.get('intactCount') or 0,
            )
            if data.get('legacyNote'):
                text += ' {}'.format(data.get('legacyNote'))
        route = '/test-platform/case?projectId={}&tab=ai-case-import&aiQuality=1'.format(project_id)
        return QualityAssistantService._compose_text(
            intent='ask_ai_case_rewrite_rate',
            answer_text=text,
            confidence=0.92,
            citations=[{
                'type': 'ai_case_quality',
                'id': project_id,
                'title': 'AI 用例改写率',
                'route': route,
                'highlights': [
                    'rewriteRate={}'.format(data.get('rewriteRate')),
                    'tracked={}'.format(tracked),
                ],
            }],
            actions=[{'type': 'navigate', 'label': '打开 AI 质量面板', 'route': route}],
            suggestions=['昨晚失败主要像环境还是用例？', '帮我用最新代码PRD全自动生成用例'],
        ), [{'tool': 'ask_ai_case_rewrite_rate', 'tracked': tracked, 'rewriteRate': data.get('rewriteRate')}]

    @staticmethod
    def _tool_failure_attribution(db, slots, message, user):
        from app.api.service.failureAttributionService import FailureAttributionService
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_failure_attribution', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_failure_attribution', 'error': err}]
        hours = 24
        if slots.get('hours'):
            try:
                hours = int(slots.get('hours'))
            except (TypeError, ValueError):
                hours = 24
        data, serr = FailureAttributionService.summary(db, project_id, hours=hours)
        if serr:
            return QualityAssistantService._compose_text(
                intent='ask_failure_attribution', answer_text=serr, confidence=0.4,
            ), [{'tool': 'ask_failure_attribution', 'error': serr}]
        total = data.get('totalFailures') or 0
        if not total:
            text = '近 {} 小时内未发现自动化/巡检失败样本。'.format(hours)
        else:
            parts = [
                '{} {} 条({}%)'.format(
                    item.get('failureClass'),
                    item.get('count'),
                    int(round(float(item.get('ratio') or 0) * 100)),
                )
                for item in (data.get('distribution') or [])
            ]
            text = (
                '近 {} 小时共 {} 次失败；主因偏向「{}」。分布：{}。'
                '（规则优先归因，unknown 需人工复核）'
            ).format(hours, total, data.get('topClassLabel') or data.get('topClass'), '；'.join(parts))
        return QualityAssistantService._compose_text(
            intent='ask_failure_attribution',
            answer_text=text,
            confidence=0.88,
            citations=[{
                'type': 'failure_attribution',
                'id': project_id,
                'title': '失败归因摘要',
                'route': '/test-platform/case?projectId={}'.format(project_id),
                'highlights': [data.get('topClassLabel') or ''],
            }],
            actions=[{
                'type': 'navigate',
                'label': '打开用例管理',
                'route': '/test-platform/case?projectId={}'.format(project_id),
            }],
            suggestions=['本项目 AI 用例改写率怎么样？', '昨晚巡检挂了什么？'],
        ), [{'tool': 'ask_failure_attribution', 'total': total, 'topClass': data.get('topClass')}]

    @staticmethod
    def _tool_report_summary(db, slots, message, user):
        from app.api.model.reportModel import Report
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_report_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_report_summary', 'error': err}]
        rows = db.query(Report).filter(Report.project_id == project_id).order_by(Report.id.desc()).limit(8).all()
        text = '当前项目最近 {} 份测试报告。'.format(len(rows)) if rows else '当前项目暂无测试报告。'
        citations = [{
            'type': 'report',
            'id': r.id,
            'title': r.name,
            'route': '/test-platform/report/viewer?id={}'.format(r.id),
            'highlights': [],
        } for r in rows]
        return QualityAssistantService._compose_text(
            intent='ask_report_summary',
            answer_text=text,
            confidence=0.88,
            citations=citations,
            actions=[{'type': 'navigate', 'label': '打开测试报告', 'route': '/test-platform/report?projectId={}'.format(project_id)}],
            suggestions=['打开测试计划', '提测前还缺什么？'],
        ), [{'tool': 'ask_report_summary', 'count': len(rows)}]

    @staticmethod
    def _tool_mobile_summary(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_mobile_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_mobile_summary', 'error': err}]
        items, total = MobileAutomationDao.list_executions(db, project_id=project_id, page_no=1, page_size=10)
        text = '当前项目移动自动化执行共 {} 次（展示最近 {} 条）。'.format(total, len(items))
        if not items:
            text = '当前项目暂无移动自动化执行记录。'
        citations = [{
            'type': 'mobile_execution',
            'id': e.id,
            'title': '执行#{}'.format(e.id),
            'route': '/mobile-automation/execution/detail?id={}'.format(e.id),
            'highlights': ['status={}'.format(getattr(e, 'status', ''))],
        } for e in items[:8]]
        return QualityAssistantService._compose_text(
            intent='ask_mobile_summary',
            answer_text=text,
            confidence=0.88,
            citations=citations,
            actions=[
                {'type': 'navigate', 'label': '打开移动执行', 'route': '/mobile-automation/executions'},
                {'type': 'navigate', 'label': '打开设备', 'route': '/mobile-automation/devices'},
            ],
            suggestions=['打开性能测试', '平台都能做什么？'],
        ), [{'tool': 'ask_mobile_summary', 'total': total}]

    @staticmethod
    def _tool_performance_summary(db, slots, message, user):
        from app.api.model.performanceModel import PerformanceScenario, PerformanceExecutionRun
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='ask_performance_summary', answer_text=err, confidence=0.4,
            ), [{'tool': 'ask_performance_summary', 'error': err}]
        scenarios = db.query(PerformanceScenario).filter(
            PerformanceScenario.is_delete == 0,
            PerformanceScenario.project_id == project_id,
        ).order_by(PerformanceScenario.id.desc()).limit(20).all()
        scenario_ids = [s.id for s in scenarios]
        runs = []
        if scenario_ids:
            runs = db.query(PerformanceExecutionRun).filter(
                PerformanceExecutionRun.scenario_id.in_(scenario_ids),
            ).order_by(PerformanceExecutionRun.id.desc()).limit(8).all()
        text = '当前项目性能场景 {} 个，最近执行 {} 次。'.format(len(scenarios), len(runs))
        if not scenarios:
            text = '当前项目暂无性能测试场景。'
        citations = [{
            'type': 'performance_run',
            'id': r.id,
            'title': r.run_no or 'run#{}'.format(r.id),
            'route': '/performance/runs',
            'highlights': ['status={}'.format(r.status)],
        } for r in runs]
        return QualityAssistantService._compose_text(
            intent='ask_performance_summary',
            answer_text=text,
            confidence=0.86,
            citations=citations,
            actions=[
                {'type': 'navigate', 'label': '打开性能场景', 'route': '/performance/scenarios'},
                {'type': 'navigate', 'label': '打开性能执行', 'route': '/performance/runs'},
            ],
            suggestions=['打开精准测试', '打开移动自动化'],
        ), [{'tool': 'ask_performance_summary', 'scenarios': len(scenarios), 'runs': len(runs)}]

    @staticmethod
    def _tool_help(db, slots, message, user):
        text = (
            '我是效能平台质量助手，覆盖全平台模块导航，并对质量事实提供可核验回答：\n'
            '· 契约 / 巡检 / 计划 / Bug / 用例 / 报告 / 性能 / 移动：可查询汇总\n'
            '· AI 中枢、评审、工作量、精准测试、Mock、造数、系统管理：可一键跳转\n'
            '· 写操作目前支持：触发契约套件执行（需确认）\n'
            '可问「平台都能做什么？」查看完整清单，或直接说「打开XX」。'
        )
        return QualityAssistantService._compose_text(
            intent='small_talk_or_help',
            answer_text=text,
            confidence=1.0,
            suggestions=[e['text'] for e in EXAMPLES],
            actions=[
                {'type': 'navigate', 'label': '契约套件', 'route': '/contract/suites'},
                {'type': 'navigate', 'label': 'AI 测试中枢', 'route': '/test-platform/ai-platform'},
                {'type': 'navigate', 'label': '精准测试', 'route': '/precise/analysis'},
            ],
        ), [{'tool': 'help'}]

    @staticmethod
    def _tool_unsupported(db, slots, message, user):
        mod = match_module(message or '')
        if mod:
            return QualityAssistantService._tool_navigate_module(
                db, dict(slots or {}, module_key=mod['key']), message, user,
            )
        return QualityAssistantService._compose_text(
            intent='unsupported',
            answer_text=(
                '这个问题我还不能直接给业务结论，但可以帮你跳到对应模块。'
                '试试「打开XX」或「平台都能做什么？」；质量类可问契约 / 巡检 / Bug / 计划等。'
            ),
            confidence=0.7,
            suggestions=[e['text'] for e in EXAMPLES[:5]],
            actions=[
                {'type': 'navigate', 'label': '首页', 'route': '/effekt'},
                {'type': 'navigate', 'label': '契约套件', 'route': '/contract/suites'},
                {'type': 'navigate', 'label': 'AI 测试中枢', 'route': '/test-platform/ai-platform'},
            ],
        ), [{'tool': 'unsupported'}]

    # ── AI case generation orchestration ────────────────────────

    @staticmethod
    def _slot_case_gen(raw):
        slots = {}
        if re.search(r'全自动|自动(跑|执行|生成)|不要确认|免确认', raw, re.I):
            slots['run_mode'] = 'auto'
        elif re.search(r'逐步确认|每步确认|先确认|手动确认|confirm', raw, re.I):
            slots['run_mode'] = 'confirm'
        if re.search(r'代码\s*PRD|代码转PRD|同步.*PRD|最新.*PRD', raw, re.I):
            slots['prefer_code_prd'] = True
        # 粗提取引号或「用XXX文档」
        m = re.search(r'[「『"“](.{2,40}?)[」』"”]', raw)
        if m:
            slots['doc_keyword'] = m.group(1).strip()
        else:
            m2 = re.search(r'用(.{2,30}?)(文档|PRD|需求)', raw)
            if m2 and '最新' not in m2.group(1) and '代码' not in m2.group(1):
                slots['doc_keyword'] = m2.group(1).strip()
        return slots

    @staticmethod
    def _case_gen_ctx(slots):
        ctx = slots.get('case_gen') if isinstance(slots.get('case_gen'), dict) else {}
        return dict(ctx or {})

    @staticmethod
    def _doc_display_name(doc):
        source = (getattr(doc, 'source', None) or '').strip()
        if source:
            name = source.replace('\\', '/').rstrip('/').split('/')[-1]
            if name.lower().endswith('.md'):
                name = name[:-3]
            if name:
                return name
        return '文档#{}'.format(getattr(doc, 'id', ''))

    @staticmethod
    def _list_case_gen_assets(db, project_id, product_id=None, doc_keyword=None, prefer_code_prd=False):
        from app.api.model.documentSourceModel import DocumentSource
        from app.api.dao.skillDao import SkillDao

        docs = db.query(DocumentSource).filter(
            DocumentSource.project_id == int(project_id),
            DocumentSource.is_delete == 0,
        ).order_by(DocumentSource.updated_time.desc(), DocumentSource.id.desc()).limit(80).all()

        keyword = (doc_keyword or '').strip().lower()
        scored = []
        for doc in docs:
            name = QualityAssistantService._doc_display_name(doc)
            ai_model = (getattr(doc, 'ai_model', None) or '').strip()
            source = (getattr(doc, 'source', None) or '')
            is_code_prd = ai_model == 'code-prd' or 'code-prd' in source
            score = 0
            if prefer_code_prd and is_code_prd:
                score += 100
            if keyword and keyword in name.lower():
                score += 50
            if keyword and keyword in (source or '').lower():
                score += 20
            if is_code_prd:
                score += 5
            scored.append((score, doc, name, is_code_prd))
        scored.sort(key=lambda x: (-x[0], -int(getattr(x[1], 'id', 0) or 0)))

        selected_docs = []
        if scored:
            if prefer_code_prd:
                code_docs = [x for x in scored if x[3]]
                selected_docs = code_docs[:1] or scored[:1]
            elif keyword:
                hits = [x for x in scored if x[0] >= 50]
                selected_docs = hits[:3] or scored[:1]
            else:
                # 默认优先代码PRD，否则最新一条
                code_docs = [x for x in scored if x[3]]
                selected_docs = code_docs[:1] or scored[:1]

        skills = SkillDao.list_skills_by_project(db, project_id, status=1) or []
        rules = SkillDao.list_business_rules_by_project(db, project_id, status=1) or []

        doc_items = [{
            'id': int(item[1].id),
            'title': item[2],
            'isCodePrd': bool(item[3]),
            'aiModel': getattr(item[1], 'ai_model', None) or '',
        } for item in selected_docs]
        # 候选列表（供用户改选提示）
        candidates = [{
            'id': int(item[1].id),
            'title': item[2],
            'isCodePrd': bool(item[3]),
        } for item in scored[:8]]

        skill_items = [{'id': int(s.id), 'name': s.name or 'Skill#{}'.format(s.id)} for s in skills[:20]]
        rule_items = [{'id': int(r.id), 'name': r.name or 'Rule#{}'.format(r.id)} for r in rules[:20]]
        return {
            'documents': doc_items,
            'documentCandidates': candidates,
            'skills': skill_items,
            'rules': rule_items,
            'productId': int(product_id) if product_id not in (None, '') else None,
            'projectId': int(project_id),
        }

    @staticmethod
    def _tool_start_ai_case_gen(db, slots, message, user):
        project_id, err = QualityAssistantService._require_project(slots)
        if err:
            return QualityAssistantService._compose_text(
                intent='start_ai_case_gen',
                answer_text=err,
                confidence=0.4,
                suggestions=['先在上方选择产品/项目，再说：帮我用最新代码PRD全自动生成用例'],
            ), [{'tool': 'propose_case_gen', 'error': err}]

        product_id = slots.get('product_id')
        prefer_code_prd = bool(slots.get('prefer_code_prd'))
        doc_keyword = (slots.get('doc_keyword') or '').strip() or None
        # 消息里若再次提到代码PRD
        if re.search(r'代码\s*PRD|代码转PRD|最新.*PRD', message or '', re.I):
            prefer_code_prd = True

        assets = QualityAssistantService._list_case_gen_assets(
            db, project_id, product_id=product_id,
            doc_keyword=doc_keyword, prefer_code_prd=prefer_code_prd,
        )
        case_gen = QualityAssistantService._case_gen_ctx(slots)
        doc_ids = [d['id'] for d in assets['documents']]
        # 默认不强制勾选全部 Skill/规则，避免过长 prompt；用户可自然语言再要求
        skill_ids = case_gen.get('skillIds') or []
        rule_ids = case_gen.get('ruleIds') or []
        run_mode = (slots.get('run_mode') or case_gen.get('runMode') or '').strip().lower()
        if run_mode not in ('auto', 'confirm'):
            run_mode = ''

        case_gen.update({
            'step': 'propose',
            'documentIds': doc_ids,
            'skillIds': [int(x) for x in skill_ids if str(x).isdigit() or isinstance(x, int)],
            'ruleIds': [int(x) for x in rule_ids if str(x).isdigit() or isinstance(x, int)],
            'runMode': run_mode or case_gen.get('runMode') or '',
            'preferCodePrd': prefer_code_prd,
        })
        slots['case_gen'] = case_gen

        if not doc_ids:
            actions = [{
                'type': 'sync_code_prd',
                'label': '同步最新代码PRD',
                'payload': {
                    'project_id': project_id,
                    'product_id': product_id,
                },
            }, {
                'type': 'navigate',
                'label': '打开用例管理选文档',
                'route': '/test-platform/case?productId={}&projectId={}&tab=ai-case-import'.format(
                    product_id or '', project_id
                ),
            }]
            return QualityAssistantService._compose_text(
                intent='start_ai_case_gen',
                answer_text=(
                    '当前项目还没有可用文档源。可先同步最新代码PRD，或到用例管理导入/勾选文档后再说一次。'
                ),
                confidence=0.7,
                actions=actions,
                suggestions=['同步最新代码PRD后再生成用例', '帮我用最新代码PRD全自动生成用例'],
            ), [{'tool': 'list_case_gen_assets', 'ok': True, 'documents': 0}]

        doc_lines = '、'.join(['「{}」(#{}{})'.format(
            d['title'], d['id'], '·代码PRD' if d.get('isCodePrd') else ''
        ) for d in assets['documents']])
        skill_line = '未勾选（可后续在向导页补充）' if not skill_ids else '、'.join([
            s['name'] for s in assets['skills'] if s['id'] in set(case_gen['skillIds'])
        ]) or '{} 个'.format(len(case_gen['skillIds']))
        rule_line = '未勾选（可后续在向导页补充）' if not rule_ids else '{} 个'.format(len(case_gen['ruleIds']))

        mode_label = {'auto': '全自动', 'confirm': '逐步确认'}.get(run_mode, '未选择（请先选权限模式）')
        answer_text = (
            '已为 AI 生成用例准备选型：\n'
            '- 文档：{}\n'
            '- Skills：{}\n'
            '- 业务规则：{}\n'
            '- 运行模式：{}\n\n'
            '请选择权限模式后打开向导。全自动将依次：大纲→精写预览→确认导入；'
            '逐步确认则只预填资源，由你在用例页逐步点选。'
        ).format(doc_lines, skill_line, rule_line, mode_label)

        actions = []
        if run_mode != 'auto':
            actions.append({
                'type': 'set_ai_case_run_mode',
                'label': '设为全自动',
                'payload': {'run_mode': 'auto'},
            })
        if run_mode != 'confirm':
            actions.append({
                'type': 'set_ai_case_run_mode',
                'label': '设为逐步确认',
                'payload': {'run_mode': 'confirm'},
            })
        if prefer_code_prd or any(d.get('isCodePrd') for d in assets['documents']):
            actions.append({
                'type': 'sync_code_prd',
                'label': '重新同步代码PRD',
                'payload': {'project_id': project_id, 'product_id': product_id},
            })
        open_payload = {
            'product_id': product_id,
            'project_id': project_id,
            'document_ids': doc_ids,
            'skill_ids': case_gen.get('skillIds') or [],
            'rule_ids': case_gen.get('ruleIds') or [],
            'run_mode': run_mode or 'confirm',
        }
        actions.append({
            'type': 'open_ai_case_wizard',
            'label': '确认并打开向导' if run_mode else '打开向导（默认逐步确认）',
            'payload': open_payload,
        })

        return QualityAssistantService._compose_text(
            intent='start_ai_case_gen',
            answer_text=answer_text,
            confidence=0.85,
            citations=[{
                'type': 'document',
                'id': d['id'],
                'title': d['title'],
                'route': '/test-platform/case?productId={}&projectId={}&tab=ai-case-import'.format(
                    product_id or '', project_id
                ),
                'highlights': ['代码PRD'] if d.get('isCodePrd') else [],
            } for d in assets['documents']],
            actions=actions,
            suggestions=[
                '帮我用最新代码PRD全自动生成用例',
                '改成逐步确认再打开向导',
            ],
        ), [{
            'tool': 'propose_case_gen',
            'ok': True,
            'documents': doc_ids,
            'run_mode': run_mode or '',
            'candidates': len(assets.get('documentCandidates') or []),
        }]

    @staticmethod
    def _get_session_for_user(db, session_id, user_id):
        if session_id in (None, '') or user_id in (None, ''):
            return None
        return QualityAssistantDao.get_session(db, session_id=int(session_id), user_id=int(user_id))

    @staticmethod
    def _merge_case_gen_on_session(db, sess, patch):
        ctx = dict(sess.context or {})
        case_gen = dict(ctx.get('case_gen') or {})
        case_gen.update(patch or {})
        ctx['case_gen'] = case_gen
        QualityAssistantDao.update_session(db, sess.id, {
            'context': ctx,
            'updated_time': datetime.now(),
        })
        return case_gen

    @staticmethod
    def _action_set_ai_case_run_mode(db, body, payload, user):
        user_id = user.get('user_id')
        session_id = body.get('session_id')
        run_mode = (payload.get('run_mode') or payload.get('runMode') or '').strip().lower()
        if run_mode not in ('auto', 'confirm'):
            return None, 'run_mode 必须是 auto 或 confirm'
        sess = QualityAssistantService._get_session_for_user(db, session_id, user_id)
        if not sess:
            return None, '会话不存在或无权访问'
        case_gen = QualityAssistantService._merge_case_gen_on_session(db, sess, {
            'runMode': run_mode,
            'step': 'mode_set',
        })
        label = '全自动' if run_mode == 'auto' else '逐步确认'
        open_payload = {
            'product_id': sess.product_id or case_gen.get('productId'),
            'project_id': sess.project_id or case_gen.get('projectId'),
            'document_ids': case_gen.get('documentIds') or [],
            'skill_ids': case_gen.get('skillIds') or [],
            'rule_ids': case_gen.get('ruleIds') or [],
            'run_mode': run_mode,
        }
        answer = QualityAssistantService._compose_text(
            intent='start_ai_case_gen',
            answer_text='已将运行模式设为「{}」。可继续打开向导。'.format(label),
            actions=[{
                'type': 'open_ai_case_wizard',
                'label': '确认并打开向导',
                'payload': open_payload,
            }, {
                'type': 'set_ai_case_run_mode',
                'label': '改成{}'.format('逐步确认' if run_mode == 'auto' else '全自动'),
                'payload': {'run_mode': 'confirm' if run_mode == 'auto' else 'auto'},
            }],
            suggestions=['确认并打开向导'],
        )
        QualityAssistantDao.create_message(db, {
            'session_id': int(sess.id),
            'role': 'assistant',
            'content': answer['answer_text'],
            'intent': 'start_ai_case_gen',
            'tool_trace': [{'tool': 'set_ai_case_run_mode', 'input': {'run_mode': run_mode}, 'ok': True}],
            'answer_payload': answer,
        })
        db.commit()
        return {'action_type': 'set_ai_case_run_mode', 'run_mode': run_mode, 'answer': answer}, ''

    @staticmethod
    def _build_case_wizard_route(product_id, project_id, session_id, run_mode, document_ids, skill_ids, rule_ids):
        from urllib.parse import urlencode
        query = {
            'productId': product_id or '',
            'projectId': project_id or '',
            'tab': 'ai-case-import',
            'qaSessionId': session_id or '',
            'runMode': run_mode or 'confirm',
            'documentIds': ','.join([str(int(x)) for x in (document_ids or []) if str(x).strip()]),
            'skillIds': ','.join([str(int(x)) for x in (skill_ids or []) if str(x).strip()]),
            'ruleIds': ','.join([str(int(x)) for x in (rule_ids or []) if str(x).strip()]),
        }
        return '/test-platform/case?' + urlencode(query)

    @staticmethod
    def _action_open_ai_case_wizard(db, body, payload, user):
        user_id = user.get('user_id')
        session_id = body.get('session_id')
        codes = user.get('permission_codes') or []
        # 空列表视为未启用细粒度权限（兼容本地）
        if codes and 'document:generate' not in codes:
            return None, '无文档生成权限（document:generate），无法打开 AI 生成用例向导'

        sess = QualityAssistantService._get_session_for_user(db, session_id, user_id)
        if not sess:
            return None, '会话不存在或无权访问'

        case_gen = QualityAssistantService._case_gen_ctx(sess.context or {})
        product_id = payload.get('product_id') or payload.get('productId') or sess.product_id
        project_id = payload.get('project_id') or payload.get('projectId') or sess.project_id
        document_ids = payload.get('document_ids') or payload.get('documentIds') or case_gen.get('documentIds') or []
        skill_ids = payload.get('skill_ids') or payload.get('skillIds') or case_gen.get('skillIds') or []
        rule_ids = payload.get('rule_ids') or payload.get('ruleIds') or case_gen.get('ruleIds') or []
        run_mode = (payload.get('run_mode') or payload.get('runMode') or case_gen.get('runMode') or 'confirm')
        run_mode = str(run_mode).strip().lower()
        if run_mode not in ('auto', 'confirm'):
            run_mode = 'confirm'

        document_ids = [int(x) for x in document_ids if str(x).strip().isdigit() or isinstance(x, int)]
        skill_ids = [int(x) for x in skill_ids if str(x).strip().isdigit() or isinstance(x, int)]
        rule_ids = [int(x) for x in rule_ids if str(x).strip().isdigit() or isinstance(x, int)]
        if not project_id:
            return None, '缺少项目上下文，请先选择项目'
        if not document_ids:
            return None, '请先选择至少一个文档（PRD）'

        route = QualityAssistantService._build_case_wizard_route(
            product_id, project_id, sess.id, run_mode, document_ids, skill_ids, rule_ids,
        )
        QualityAssistantService._merge_case_gen_on_session(db, sess, {
            'step': 'wizard_opened',
            'runMode': run_mode,
            'documentIds': document_ids,
            'skillIds': skill_ids,
            'ruleIds': rule_ids,
            'productId': int(product_id) if product_id not in (None, '') else None,
            'projectId': int(project_id),
            'lastSummary': '已打开向导',
        })
        mode_label = '全自动' if run_mode == 'auto' else '逐步确认'
        answer = QualityAssistantService._compose_text(
            intent='start_ai_case_gen',
            answer_text=(
                '已打开用例管理「AI生成用例」向导（模式：{}）。'
                '文档ID={}；Skills={}；规则={}。'
                '请在用例页查看进度；关键步骤会回写到本对话留痕。'
            ).format(mode_label, document_ids, skill_ids or '无', rule_ids or '无'),
            actions=[{
                'type': 'navigate',
                'label': '再次打开向导页',
                'route': route,
            }],
            suggestions=['覆盖报告怎么样了？', '今天哪些 breaking？'],
        )
        QualityAssistantDao.create_message(db, {
            'session_id': int(sess.id),
            'role': 'assistant',
            'content': answer['answer_text'],
            'intent': 'start_ai_case_gen',
            'tool_trace': [{
                'tool': 'open_ai_case_wizard',
                'input': {
                    'run_mode': run_mode,
                    'document_ids': document_ids,
                    'skill_ids': skill_ids,
                    'rule_ids': rule_ids,
                },
                'ok': True,
            }],
            'answer_payload': answer,
        })
        db.commit()
        return {
            'action_type': 'open_ai_case_wizard',
            'route': route,
            'run_mode': run_mode,
            'answer': answer,
        }, ''

    @staticmethod
    def _action_sync_code_prd(db, body, payload, user):
        user_id = user.get('user_id')
        session_id = body.get('session_id')
        project_id = payload.get('project_id') or payload.get('projectId')
        product_id = payload.get('product_id') or payload.get('productId')
        if project_id in (None, ''):
            return None, '缺少 project_id'
        from app.api.service.documentSourceService import DocumentSourceService
        from app.api.model.projectModel import Project
        if product_id in (None, ''):
            proj = db.query(Project).filter(Project.id == int(project_id)).first()
            product_id = getattr(proj, 'product_id', None) if proj else None
        ret, err = DocumentSourceService.sync_from_latest_code_prd(
            db, int(project_id), user_id=user_id,
        )
        if err:
            return None, err
        doc_obj = (ret or {}).get('document')
        doc_id = (ret or {}).get('documentId') or getattr(doc_obj, 'id', None)
        title = (ret or {}).get('title') or '代码PRD'
        sess = QualityAssistantService._get_session_for_user(db, session_id, user_id)
        if sess and doc_id:
            QualityAssistantService._merge_case_gen_on_session(db, sess, {
                'documentIds': [int(doc_id)],
                'preferCodePrd': True,
                'step': 'docs_synced',
                'lastSummary': '已同步代码PRD #{}'.format(doc_id),
            })
        answer = QualityAssistantService._compose_text(
            intent='start_ai_case_gen',
            answer_text='已同步最新代码PRD「{}」(#{})。可继续选择运行模式并打开向导。'.format(title, doc_id or '-'),
            actions=[{
                'type': 'set_ai_case_run_mode',
                'label': '设为全自动',
                'payload': {'run_mode': 'auto'},
            }, {
                'type': 'set_ai_case_run_mode',
                'label': '设为逐步确认',
                'payload': {'run_mode': 'confirm'},
            }, {
                'type': 'open_ai_case_wizard',
                'label': '确认并打开向导',
                'payload': {
                    'product_id': product_id,
                    'project_id': project_id,
                    'document_ids': [int(doc_id)] if doc_id else [],
                    'run_mode': 'confirm',
                },
            }],
            suggestions=['帮我用最新代码PRD全自动生成用例'],
        )
        if sess:
            QualityAssistantDao.create_message(db, {
                'session_id': int(sess.id),
                'role': 'assistant',
                'content': answer['answer_text'],
                'intent': 'start_ai_case_gen',
                'tool_trace': [{'tool': 'sync_code_prd', 'input': {'project_id': project_id}, 'ok': True, 'document_id': doc_id}],
                'answer_payload': answer,
            })
            db.commit()
        else:
            db.commit()
        return {'action_type': 'sync_code_prd', 'result': ret, 'answer': answer}, ''

    @staticmethod
    def append_workflow_event(db, body, user):
        """用例页向导回写进度到质量助手会话。"""
        body = body or {}
        user_id = user.get('user_id')
        session_id = body.get('session_id') or body.get('sessionId')
        event = (body.get('event') or '').strip()
        summary = (body.get('summary') or '').strip()
        plan_id = body.get('plan_id') or body.get('planId')
        metrics = body.get('metrics') if isinstance(body.get('metrics'), dict) else {}

        if not session_id:
            return None, '缺少 session_id'
        if event not in CASE_GEN_WORKFLOW_EVENTS:
            return None, '不支持的 event：{}'.format(event or '-')
        if not summary:
            return None, '缺少 summary'

        sess = QualityAssistantService._get_session_for_user(db, session_id, user_id)
        if not sess:
            return None, '会话不存在或无权访问'

        patch = {
            'step': event,
            'lastSummary': summary,
        }
        if plan_id not in (None, ''):
            try:
                patch['planId'] = int(plan_id)
            except (TypeError, ValueError):
                pass
        if metrics:
            patch['lastMetrics'] = metrics
        QualityAssistantService._merge_case_gen_on_session(db, sess, patch)

        answer = QualityAssistantService._compose_text(
            intent='start_ai_case_gen',
            answer_text=summary,
            confidence=0.9,
            citations=[{
                'type': 'generation_plan',
                'id': int(plan_id),
                'title': '生成计划 #{}'.format(plan_id),
                'route': '/test-platform/case?projectId={}&tab=ai-case-import'.format(sess.project_id or ''),
                'highlights': [event],
            }] if plan_id not in (None, '') else [],
            suggestions=['打开用例管理', '今天哪些 breaking？'],
        )
        QualityAssistantDao.create_message(db, {
            'session_id': int(sess.id),
            'role': 'assistant',
            'content': summary,
            'intent': 'start_ai_case_gen',
            'tool_trace': [{'tool': 'workflow_event', 'event': event, 'plan_id': plan_id, 'metrics': metrics, 'ok': True}],
            'answer_payload': answer,
        })
        db.commit()
        return {
            'session_id': sess.id,
            'event': event,
            'answer': answer,
        }, ''

    # ── Composer ────────────────────────────────────────────────

    @staticmethod
    def _compose_text(intent, answer_text, confidence=0.8, citations=None, actions=None, suggestions=None):
        return {
            'answer_text': answer_text,
            'confidence': confidence,
            'intent': intent,
            'citations': citations or [],
            'actions': actions or [],
            'suggestions': suggestions or [],
        }

    @staticmethod
    def _tr_label(tr):
        return {
            'today': '今天',
            'last_24h': '24 小时',
            'last_7d': '7 天',
        }.get(tr, tr or '近期')
