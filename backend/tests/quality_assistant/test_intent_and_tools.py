# encoding: utf-8
"""质量助手意图规则与回答协议基础单测（不依赖 DB）。"""
import unittest

from app.api.service.qualityAssistantService import QualityAssistantService


class TestQualityAssistantIntent(unittest.TestCase):

    def test_rule_breaking(self):
        parsed = QualityAssistantService._rule_intent('今天哪些 breaking？')
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['intent'], 'ask_contract_breaking')
        self.assertEqual(parsed.get('slots', {}).get('time_range'), 'today')

    def test_rule_inspection(self):
        parsed = QualityAssistantService._rule_intent('昨晚巡检挂了什么？')
        self.assertEqual(parsed['intent'], 'ask_inspection_failures')

    def test_rule_regression(self):
        parsed = QualityAssistantService._rule_intent('该跑哪包回归？')
        self.assertEqual(parsed['intent'], 'recommend_regression_pack')

    def test_rule_precheck(self):
        parsed = QualityAssistantService._rule_intent('提测前还缺什么？')
        self.assertEqual(parsed['intent'], 'precheck_release_or_test')

    def test_compose_protocol(self):
        ans = QualityAssistantService._compose_text(
            intent='ask_contract_breaking',
            answer_text='ok',
            citations=[{'type': 'contract_run', 'id': 1, 'title': 't', 'route': '/x', 'highlights': []}],
            actions=[{'type': 'navigate', 'label': 'go', 'route': '/x'}],
        )
        self.assertEqual(ans['intent'], 'ask_contract_breaking')
        self.assertEqual(len(ans['citations']), 1)
        self.assertEqual(ans['actions'][0]['type'], 'navigate')


if __name__ == '__main__':
    unittest.main()
