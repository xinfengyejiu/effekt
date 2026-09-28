# encoding: UTF-8
"""契约 AI：设计期生成契约 + 执行后漂移分析。复用 AIService。"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

_DESIGN_SYSTEM = (
    '你是接口契约设计助手。根据用户描述或样例 JSON，产出可执行的响应 JSON Schema。'
    '必须只输出可解析 JSON，不要输出其它文字。'
)

_ANALYZE_SYSTEM = (
    '你是接口契约漂移分析助手。根据 Schema Diff findings，给出根因、影响与修复建议。'
    '判定以 findings 为准，不要否认已检出的 breaking。'
    '必须只输出可解析 JSON，不要输出其它文字。'
)

_VALID_ACTIONS = ('fix_backend', 'update_schema', 'ignore_compatible', 'check_env')
_VALID_CATEGORIES = (
    'backend_breaking_change',
    'schema_outdated',
    'env_mismatch',
    'test_data',
    'compatible_extension',
    'http_error',
    'unknown',
)


class ContractAiService(object):

    @staticmethod
    def _trim(value, max_chars=6000):
        try:
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            text = str(value)
        if len(text) > max_chars:
            return text[:max_chars] + '...(truncated)'
        return text

    @staticmethod
    def _normalize_path(path):
        path = (path or '').strip()
        if not path:
            return '/api/v1/resource'
        if path.startswith('http://') or path.startswith('https://'):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(path)
                path = parsed.path or '/'
            except Exception:
                path = '/'
        if '?' in path:
            path = path.split('?', 1)[0]
        if not path.startswith('/'):
            path = '/' + path
        return path[:512]

    @staticmethod
    def infer_schema_from_value(value, depth=0):
        """从样例 JSON 本地推断 Schema，不依赖 LLM。"""
        if depth > 12:
            return {}
        if value is None:
            return {'type': 'null'}
        if isinstance(value, bool):
            return {'type': 'boolean'}
        if isinstance(value, int) and not isinstance(value, bool):
            return {'type': 'integer'}
        if isinstance(value, float):
            return {'type': 'number'}
        if isinstance(value, str):
            return {'type': 'string'}
        if isinstance(value, list):
            if not value:
                return {'type': 'array', 'items': {}}
            return {
                'type': 'array',
                'items': ContractAiService.infer_schema_from_value(value[0], depth + 1),
            }
        if isinstance(value, dict):
            props = {}
            for k, v in value.items():
                props[str(k)] = ContractAiService.infer_schema_from_value(v, depth + 1)
            return {
                'type': 'object',
                'properties': props,
                'required': list(props.keys()),
            }
        return {'type': 'string'}

    @staticmethod
    def design_from_sample(sample_json, hints=None):
        hints = hints or {}
        method = str(hints.get('method') or 'GET').upper()
        if method not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
            method = 'GET'
        path = ContractAiService._normalize_path(hints.get('path'))
        name = str(hints.get('name') or '').strip() or '从样例推断的接口'
        schema = ContractAiService.infer_schema_from_value(sample_json)
        return {
            'name': name[:255],
            'method': method,
            'path': path,
            'response_schema': schema,
            'confidence': 0.72,
            'notes': ['由样例 JSON 本地推断生成，请核对 required / enum 是否过宽'],
            'breaking_watch': [],
            'source': 'sample_infer',
        }

    @staticmethod
    def design_interface(payload):
        """
        AI 辅助设计接口契约。
        payload: mode(nl|sample_json|refine), text, sample_json, current_schema, hints
        Returns: (draft_dict, error_msg)
        """
        from app.api.service.aiService import AIService

        payload = payload or {}
        mode = (payload.get('mode') or 'nl').strip()
        text = (payload.get('text') or '').strip()
        sample_json = payload.get('sample_json')
        current_schema = payload.get('current_schema')
        hints = dict(payload.get('hints') or {})
        if hints.get('path'):
            hints['path'] = ContractAiService._normalize_path(hints.get('path'))

        if mode == 'nl' and not text:
            return None, '请输入自然语言接口描述'
        if mode == 'sample_json' and sample_json in (None, '', {}):
            return None, '请提供样例 JSON'
        if mode == 'refine' and not current_schema:
            return None, '请提供待补全的当前 Schema'

        # 样例 JSON：本地推断即时返回（不依赖 LLM，避免超时/失败导致“一直不成功”）
        if mode == 'sample_json':
            return ContractAiService.design_from_sample(sample_json, hints), ''

        prompt = (
            '请设计或补全接口响应契约。\n\n'
            '## 模式\n{mode}\n\n'
            '## 业务/接口描述\n{text}\n\n'
            '## 提示信息(JSON)\n{hints}\n\n'
            '## 样例响应(JSON)\n{sample}\n\n'
            '## 当前 Schema(JSON)\n{schema}\n\n'
            '## 输出要求\n'
            '只输出 JSON 对象，字段如下：\n'
            '{{\n'
            '  "name": "接口中文名",\n'
            '  "method": "GET|POST|PUT|DELETE|PATCH",\n'
            '  "path": "/api/v1/...",\n'
            '  "response_schema": {{ JSON Schema 对象，含 type/properties/required/enum }},\n'
            '  "confidence": 0到1小数,\n'
            '  "notes": ["需人工确认的点"],\n'
            '  "breaking_watch": ["需要重点守护的 json_path"]\n'
            '}}\n'
            '规则：response_schema 必须是合法 JSON Schema；不要编造无法从输入推断的业务枚举，'
            '不确定时写进 notes；path 使用 RESTful 风格。'
        ).format(
            mode=mode,
            text=text or '（无）',
            hints=ContractAiService._trim(hints, 1500),
            sample=ContractAiService._trim(sample_json if sample_json is not None else '（无）', 4000),
            schema=ContractAiService._trim(current_schema if current_schema is not None else '（无）', 4000),
        )

        parsed, err = AIService.request_json(
            prompt,
            error_prefix='契约AI设计',
            read_timeout=60,
            max_retries=1,
            max_tokens=2000,
            temperature=0.2,
            system_prompt=_DESIGN_SYSTEM,
        )
        if err:
            return None, err
        if not isinstance(parsed, dict):
            return None, '契约AI设计返回格式错误'
        if not isinstance(parsed.get('response_schema'), dict):
            return None, 'AI 未返回有效 response_schema'
        return ContractAiService._normalize_design(parsed, hints, source='ai_draft'), ''

    @staticmethod
    def _normalize_design(parsed, hints, source='ai_draft'):
        hints = hints or {}
        notes = parsed.get('notes') or []
        if not isinstance(notes, list):
            notes = [str(notes)]
        watch = parsed.get('breaking_watch') or []
        if not isinstance(watch, list):
            watch = [str(watch)]
        confidence = parsed.get('confidence', 0.6)
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except Exception:
            confidence = 0.6
        method = str(parsed.get('method') or hints.get('method') or 'GET').upper()
        if method not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
            method = 'GET'
        path = ContractAiService._normalize_path(parsed.get('path') or hints.get('path'))
        return {
            'name': str(parsed.get('name') or hints.get('name') or '未命名接口')[:255],
            'method': method,
            'path': path,
            'response_schema': parsed.get('response_schema') or {},
            'confidence': confidence,
            'notes': [str(x)[:200] for x in notes[:8]],
            'breaking_watch': [str(x)[:200] for x in watch[:10]],
            'source': source,
        }

    @staticmethod
    def analyze_drift(payload):
        """
        对单接口 Diff 结果做 AI 分析。
        payload: name, method, path, result_status, max_severity, findings, response_schema, response_excerpt, error_message
        Returns: (analysis_dict, error_msg)
        """
        from app.api.service.aiService import AIService

        payload = payload or {}
        findings = payload.get('findings') or []
        if not isinstance(findings, list):
            findings = []
        # 优先 breaking，上限 30
        findings_sorted = sorted(
            findings,
            key=lambda f: 0 if (f or {}).get('severity') == 'breaking' else 1,
        )[:30]

        prompt = (
            '接口契约比对出现漂移或错误，请做自动分析。\n\n'
            '## 接口\n{method} {path} ({name})\n'
            '## 结果状态\n{status} / max_severity={sev}\n'
            '## 错误信息\n{error}\n\n'
            '## Findings(JSON)\n{findings}\n\n'
            '## 契约 Schema 摘要(JSON)\n{schema}\n\n'
            '## 响应摘录\n{excerpt}\n\n'
            '## 输出要求\n'
            '只输出 JSON 对象，字段如下：\n'
            '{{\n'
            '  "summary": "一句话结论",\n'
            '  "category": "backend_breaking_change|schema_outdated|env_mismatch|test_data|compatible_extension|http_error|unknown",\n'
            '  "root_cause": "根因说明",\n'
            '  "impact": "对前端/联调/发布的影响",\n'
            '  "suggestions": ["建议1", "建议2"],\n'
            '  "action": "fix_backend|update_schema|ignore_compatible|check_env",\n'
            '  "confidence": 0到1小数\n'
            '}}\n'
        ).format(
            method=payload.get('method') or 'GET',
            path=payload.get('path') or '/',
            name=payload.get('name') or '',
            status=payload.get('result_status') or 'drift',
            sev=payload.get('max_severity') or '-',
            error=(payload.get('error_message') or '')[:800] or '（无）',
            findings=ContractAiService._trim(findings_sorted, 5000),
            schema=ContractAiService._trim(payload.get('response_schema') or {}, 2500),
            excerpt=ContractAiService._trim(payload.get('response_excerpt') or '（无）', 2500),
        )

        parsed, err = AIService.request_json(
            prompt,
            error_prefix='契约AI分析',
            read_timeout=60,
            max_retries=2,
            max_tokens=900,
            temperature=0.2,
            system_prompt=_ANALYZE_SYSTEM,
        )
        if err:
            return None, err
        if not isinstance(parsed, dict):
            return None, '契约AI分析返回格式错误'

        return ContractAiService._normalize_analysis(parsed), ''

    @staticmethod
    def _normalize_analysis(parsed):
        suggestions = parsed.get('suggestions') or []
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]
        category = str(parsed.get('category') or 'unknown')
        if category not in _VALID_CATEGORIES:
            category = 'unknown'
        action = str(parsed.get('action') or 'unknown')
        if action not in _VALID_ACTIONS:
            # 温和兜底
            if category == 'compatible_extension':
                action = 'ignore_compatible'
            elif category == 'schema_outdated':
                action = 'update_schema'
            elif category == 'env_mismatch':
                action = 'check_env'
            else:
                action = 'fix_backend'
        confidence = parsed.get('confidence', 0.6)
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except Exception:
            confidence = 0.6
        return {
            'summary': str(parsed.get('summary') or '')[:300],
            'category': category,
            'root_cause': str(parsed.get('root_cause') or '')[:400],
            'impact': str(parsed.get('impact') or '')[:400],
            'suggestions': [str(x)[:200] for x in suggestions[:5]],
            'action': action,
            'confidence': confidence,
        }

    @staticmethod
    def build_stub_analysis(findings, result_status='drift', max_severity=None, error_message=None):
        """无 LLM 时的演示/兜底分析（种子数据与 AI 失败回退）。"""
        findings = findings or []
        breaking = [f for f in findings if (f or {}).get('severity') == 'breaking']
        compatible = [f for f in findings if (f or {}).get('severity') == 'compatible']
        if result_status == 'error' or error_message:
            return {
                'summary': '接口请求失败，未能完成契约比对',
                'category': 'http_error',
                'root_cause': (error_message or 'HTTP/网络错误')[:400],
                'impact': '本次无法确认字段契约是否稳定，需先恢复接口可用性',
                'suggestions': ['检查环境 Base URL 与鉴权', '确认服务是否存活', '重试执行'],
                'action': 'check_env',
                'confidence': 0.7,
                'source': 'stub',
            }
        if breaking:
            top = breaking[0]
            drift = top.get('drift_type') or ''
            if drift == 'type_mismatch':
                cat, action, cause = 'backend_breaking_change', 'fix_backend', '字段类型与契约不一致，常见于后端改动未同步文档'
            elif drift == 'missing_field':
                cat, action, cause = 'backend_breaking_change', 'fix_backend', '契约必填字段缺失，可能破坏消费方解析'
            elif drift == 'enum_violation':
                cat, action, cause = 'backend_breaking_change', 'fix_backend', '返回枚举超出契约范围'
            else:
                cat, action, cause = 'unknown', 'fix_backend', top.get('message') or '存在 breaking 漂移'
            return {
                'summary': '检出 {} 条 breaking，优先处理 {}'.format(len(breaking), top.get('json_path') or ''),
                'category': cat,
                'root_cause': cause,
                'impact': '联调/前端可能出现类型错误、空值或分支失效',
                'suggestions': [
                    '核对实现是否应改回契约类型/字段',
                    '若属有意变更：更新契约并通知消费方',
                    '对路径 {} 做回归验证'.format(top.get('json_path') or ''),
                ],
                'action': action,
                'confidence': 0.75,
                'source': 'stub',
            }
        if compatible:
            return {
                'summary': '仅存在兼容扩展字段，短期可不阻断发布',
                'category': 'compatible_extension',
                'root_cause': '实际响应多出契约未声明字段',
                'impact': '通常不影响现有消费方；长期建议补进契约以免文档漂移',
                'suggestions': ['评估是否将新字段写入契约', '确认并非调试字段泄漏到生产'],
                'action': 'ignore_compatible',
                'confidence': 0.8,
                'source': 'stub',
            }
        return {
            'summary': '存在漂移但未识别到明确 breaking',
            'category': 'unknown',
            'root_cause': '请结合 findings 明细人工确认',
            'impact': '需人工复核',
            'suggestions': ['打开 findings 表逐条核对'],
            'action': 'update_schema',
            'confidence': 0.5,
            'source': 'stub',
        }
