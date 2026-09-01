# encoding: UTF-8
"""巡检 AI 判定与失败自动分析（以自然语言期望为主）。"""
import json
import logging

logger = logging.getLogger(__name__)

_JUDGE_SYSTEM = (
    '你是质量巡检判定助手。根据采集证据与自然语言期望，判断是否通过。'
    '必须只输出可解析 JSON，不要输出其它文字。'
)

_ANALYZE_SYSTEM = (
    '你是质量巡检失败分析助手。根据期望、采集证据与错误信息，给出根因与建议。'
    '必须只输出可解析 JSON，不要输出其它文字。'
)


class InspectionAiJudge(object):
    """自然语言判定 + 失败自动分析。"""

    @staticmethod
    def _trim_evidence(evidence, max_chars=6000):
        try:
            text = json.dumps(evidence, ensure_ascii=False, default=str)
        except Exception:
            text = str(evidence)
        if len(text) > max_chars:
            return text[:max_chars] + '...(truncated)'
        return text

    @staticmethod
    def judge(expectation, evidence, item_type=''):
        """
        用自然语言期望判定是否通过。
        Returns:
            (verdict_dict, error_msg)
            verdict_dict: {passed, confidence, reason, evidence_highlights}
        """
        expectation = (expectation or '').strip()
        if not expectation:
            return None, '未配置自然语言期望'

        from app.api.service.aiService import AIService

        prompt = (
            '请判定以下巡检是否满足自然语言期望。\n\n'
            '## 检查类型\n{item_type}\n\n'
            '## 自然语言期望\n{expectation}\n\n'
            '## 采集证据(JSON)\n{evidence}\n\n'
            '## 输出要求\n'
            '只输出 JSON 对象，字段如下：\n'
            '{{\n'
            '  "passed": true/false,\n'
            '  "confidence": 0到1的小数,\n'
            '  "reason": "一句话判定理由",\n'
            '  "evidence_highlights": ["关键证据摘要1", "关键证据摘要2"]\n'
            '}}\n'
            '规则：证据不足以支持期望成立时 passed=false；'
            '不要臆造证据中不存在的字段或数值。'
        ).format(
            item_type=item_type or 'unknown',
            expectation=expectation,
            evidence=InspectionAiJudge._trim_evidence(evidence),
        )

        parsed, err = AIService.request_json(
            prompt,
            error_prefix='巡检AI判定',
            read_timeout=60,
            max_retries=2,
            max_tokens=800,
            temperature=0.1,
            system_prompt=_JUDGE_SYSTEM,
        )
        if err:
            return None, err
        if not isinstance(parsed, dict):
            return None, '巡检AI判定返回格式错误'

        passed = bool(parsed.get('passed'))
        confidence = parsed.get('confidence', 0.5)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))

        highlights = parsed.get('evidence_highlights') or []
        if not isinstance(highlights, list):
            highlights = [str(highlights)]
        highlights = [str(x)[:200] for x in highlights[:5]]

        return {
            'passed': passed,
            'confidence': confidence,
            'reason': str(parsed.get('reason') or '')[:500],
            'evidence_highlights': highlights,
        }, ''

    @staticmethod
    def analyze_failure(expectation, evidence, error_message='', item_type='', status='fail'):
        """
        失败/异常自动分析。
        Returns:
            (analysis_dict, error_msg)
            analysis_dict: {root_cause, category, impact, suggestions}
        """
        from app.api.service.aiService import AIService

        prompt = (
            '巡检项未通过，请做失败自动分析。\n\n'
            '## 检查类型\n{item_type}\n'
            '## 结果状态\n{status}\n'
            '## 自然语言期望\n{expectation}\n'
            '## 错误信息\n{error}\n\n'
            '## 采集证据(JSON)\n{evidence}\n\n'
            '## 输出要求\n'
            '只输出 JSON 对象，字段如下：\n'
            '{{\n'
            '  "root_cause": "根因一句话",\n'
            '  "category": "业务异常|接口故障|数据异常|环境问题|配置错误|超时|未知",\n'
            '  "impact": "影响说明",\n'
            '  "suggestions": ["建议1", "建议2"]\n'
            '}}\n'
        ).format(
            item_type=item_type or 'unknown',
            status=status or 'fail',
            expectation=(expectation or '').strip() or '（未配置自然语言期望）',
            error=(error_message or '')[:800] or '（无）',
            evidence=InspectionAiJudge._trim_evidence(evidence),
        )

        parsed, err = AIService.request_json(
            prompt,
            error_prefix='巡检失败分析',
            read_timeout=60,
            max_retries=2,
            max_tokens=800,
            temperature=0.2,
            system_prompt=_ANALYZE_SYSTEM,
        )
        if err:
            return None, err
        if not isinstance(parsed, dict):
            return None, '巡检失败分析返回格式错误'

        suggestions = parsed.get('suggestions') or []
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]
        suggestions = [str(x)[:200] for x in suggestions[:5]]

        return {
            'root_cause': str(parsed.get('root_cause') or '')[:400],
            'category': str(parsed.get('category') or '未知')[:40],
            'impact': str(parsed.get('impact') or '')[:400],
            'suggestions': suggestions,
        }, ''

    @staticmethod
    def apply_ai_to_checker_result(checker_result, config, item_type=''):
        """
        在 checker 采数/硬断言结果之上，叠加 AI 主判定与失败分析。
        返回更新后的 result dict（含 status/result/error_message/duration_ms）。
        """
        config = config or {}
        expectation = (config.get('expectation') or '').strip()
        assertions = config.get('assertions') or []
        base = dict(checker_result or {})
        payload = dict(base.get('result') or {})
        status = base.get('status', 'error')
        error_message = base.get('error_message') or ''

        # 采集阶段已 error：直接失败分析
        if status == 'error':
            analysis, aerr = InspectionAiJudge.analyze_failure(
                expectation, payload, error_message, item_type=item_type, status='error'
            )
            if analysis:
                payload['ai_analysis'] = analysis
            elif aerr:
                payload['ai_analysis_error'] = aerr
            base['result'] = payload
            return base

        # 高级硬断言失败：保留 fail，再做失败分析
        if status == 'fail' and assertions:
            analysis, aerr = InspectionAiJudge.analyze_failure(
                expectation, payload, error_message or '硬断言失败',
                item_type=item_type, status='fail'
            )
            if analysis:
                payload['ai_analysis'] = analysis
            elif aerr:
                payload['ai_analysis_error'] = aerr
            if expectation:
                # 仍尝试给 AI 判定结论，便于对照
                verdict, jerr = InspectionAiJudge.judge(expectation, payload, item_type=item_type)
                if verdict:
                    payload['ai_verdict'] = verdict
                elif jerr:
                    payload['ai_verdict_error'] = jerr
            base['result'] = payload
            return base

        # 以 AI 为主：需要自然语言期望
        if not expectation:
            if assertions and status == 'pass':
                # 仅硬断言通过且无期望：兼容旧配置
                base['result'] = payload
                return base
            base['status'] = 'error'
            base['error_message'] = '未配置自然语言期望，请在检查项中填写 expectation'
            base['result'] = payload
            return base

        verdict, jerr = InspectionAiJudge.judge(expectation, payload, item_type=item_type)
        if jerr or not verdict:
            base['status'] = 'error'
            base['error_message'] = jerr or 'AI判定失败'
            payload['ai_verdict_error'] = base['error_message']
            analysis, aerr = InspectionAiJudge.analyze_failure(
                expectation, payload, base['error_message'],
                item_type=item_type, status='error'
            )
            if analysis:
                payload['ai_analysis'] = analysis
            elif aerr:
                payload['ai_analysis_error'] = aerr
            base['result'] = payload
            return base

        payload['ai_verdict'] = verdict
        if verdict.get('passed'):
            base['status'] = 'pass'
            base['error_message'] = ''
        else:
            base['status'] = 'fail'
            base['error_message'] = verdict.get('reason') or 'AI判定未通过'
            analysis, aerr = InspectionAiJudge.analyze_failure(
                expectation, payload, base['error_message'],
                item_type=item_type, status='fail'
            )
            if analysis:
                payload['ai_analysis'] = analysis
            elif aerr:
                payload['ai_analysis_error'] = aerr

        base['result'] = payload
        return base
