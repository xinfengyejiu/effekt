# encoding: UTF-8
"""contractDiffService 单测。"""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.api.service.contractDiffService import ContractDiffService


class TestContractDiffService(unittest.TestCase):

    def test_type_mismatch_breaking(self):
        schema = {'type': 'object', 'properties': {'id': {'type': 'number'}}, 'required': ['id']}
        actual = {'id': '10001'}
        findings = ContractDiffService.compare(schema, actual)
        types = {(f['drift_type'], f['severity']) for f in findings}
        self.assertIn(('type_mismatch', 'breaking'), types)

    def test_missing_required_breaking(self):
        schema = {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']}
        findings = ContractDiffService.compare(schema, {})
        self.assertTrue(any(f['drift_type'] == 'missing_field' and f['severity'] == 'breaking' for f in findings))

    def test_extra_field_compatible(self):
        schema = {'type': 'object', 'properties': {'a': {'type': 'string'}}, 'required': ['a']}
        findings = ContractDiffService.compare(schema, {'a': 'x', 'b': 1})
        extra = [f for f in findings if f['drift_type'] == 'extra_field']
        self.assertTrue(extra)
        self.assertEqual(extra[0]['severity'], 'compatible')
        self.assertIn('未声明', extra[0]['expected'])

    def test_missing_expected_has_type(self):
        schema = {
            'type': 'object',
            'properties': {'userId': {'type': 'integer'}},
            'required': ['userId'],
        }
        findings = ContractDiffService.compare(schema, {})
        miss = [f for f in findings if f['drift_type'] == 'missing_field'][0]
        self.assertIn('integer', miss['expected'])
        self.assertIn('必填', miss['expected'])
    def test_enum_violation(self):
        schema = {'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ok', 'fail']}}, 'required': ['status']}
        findings = ContractDiffService.compare(schema, {'status': 'unknown'})
        self.assertTrue(any(f['drift_type'] == 'enum_violation' for f in findings))

    def test_pass_clean(self):
        schema = {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'items': {'type': 'array', 'items': {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']}},
            },
            'required': ['id', 'items'],
        }
        actual = {'id': 1, 'items': [{'name': 'a'}]}
        findings = ContractDiffService.compare(schema, actual)
        breaking = [f for f in findings if f['severity'] == 'breaking']
        self.assertEqual(breaking, [])
        self.assertEqual(ContractDiffService.max_severity(findings), None)

    def test_number_accepts_integer(self):
        schema = {'type': 'object', 'properties': {'score': {'type': 'number'}}, 'required': ['score']}
        findings = ContractDiffService.compare(schema, {'score': 3})
        self.assertFalse(any(f['drift_type'] == 'type_mismatch' for f in findings))


if __name__ == '__main__':
    unittest.main()
