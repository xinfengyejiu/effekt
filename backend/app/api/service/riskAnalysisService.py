# encoding: UTF-8
import json

from .aiService import AIService


class RiskAnalysisService(object):
    @staticmethod
    def analyze_requirement(req_data):
        source_payload = req_data.get('sourcePayload') or req_data.get('source_payload') or {}
        content = source_payload.get('content') or req_data.get('content') or ''
        if not content:
            return {}, 'content 或 sourcePayload.content 为必传参数'
        prompt = f'''你是资深测试架构师，请基于以下需求/PR/变更内容输出测试风险分析JSON，不要输出额外文字。

输入内容：
{content}

必须输出如下JSON结构：
{{
  "risk_level": "P0/P1/P2/P3/Info",
  "risk_reasons": ["风险原因"],
  "affected_modules": ["影响模块"],
  "recommended_test_types": ["functional", "api", "ui", "regression", "security", "performance"],
  "recommended_tests": [{{"name": "测试建议", "priority": "P0/P1/P2/P3", "reason": "原因"}}],
  "block_suggestion": "是否建议阻断及原因"
}}
'''
        result, err_msg = AIService.request_json(prompt, 'AI风险分析')
        if err_msg:
            return {}, err_msg
        if not isinstance(result, dict):
            return {}, 'AI风险分析结果格式错误'
        result.setdefault('risk_level', 'Info')
        result.setdefault('recommended_tests', [])
        return result, ''
