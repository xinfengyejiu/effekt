# encoding: UTF-8
"""契约 Schema Diff 引擎（简化 JSON Schema）。"""
from __future__ import annotations

import json
from typing import Any, List


SEVERITY_RANK = {'info': 1, 'compatible': 2, 'breaking': 3}


class ContractDiffService(object):
    """对比 response_schema 与实际 JSON 值，产出 findings。"""

    ARRAY_COMPARE_LIMIT = 50

    @staticmethod
    def compare(schema, actual_value, path='$'):
        findings = []
        ContractDiffService._walk(schema or {}, actual_value, path or '$', findings)
        return findings

    @staticmethod
    def max_severity(findings):
        if not findings:
            return None
        best = None
        best_rank = 0
        for f in findings:
            sev = f.get('severity') or 'info'
            rank = SEVERITY_RANK.get(sev, 0)
            if rank > best_rank:
                best_rank = rank
                best = sev
        return best

    @staticmethod
    def _walk(schema, actual, path, findings, depth=0):
        if depth > 40:
            findings.append(ContractDiffService._finding(
                path, 'info', 'depth_limit', 'schema depth', str(type(actual).__name__),
                '嵌套过深，已跳过继续比对'
            ))
            return

        if not isinstance(schema, dict) or not schema:
            return

        # oneOf/allOf 第一期跳过深比
        if schema.get('oneOf') or schema.get('allOf') or schema.get('anyOf'):
            findings.append(ContractDiffService._finding(
                path, 'info', 'complex_schema', 'oneOf/allOf/anyOf', '',
                '复杂组合 Schema 暂不深比'
            ))
            return

        expected_type = schema.get('type')
        if expected_type:
            actual_type = ContractDiffService._json_type(actual)
            if actual is None:
                # 允许缺省由 required 在父级处理；本层记 missing
                findings.append(ContractDiffService._finding(
                    path, 'breaking', 'missing_field', expected_type, 'null',
                    '字段缺失或为 null'
                ))
                return
            if not ContractDiffService._type_compatible(expected_type, actual_type):
                findings.append(ContractDiffService._finding(
                    path, 'breaking', 'type_mismatch', expected_type, actual_type,
                    '类型不兼容：期望 {}，实际 {}'.format(expected_type, actual_type)
                ))
                return

        enum_vals = schema.get('enum')
        if enum_vals and actual is not None and actual not in enum_vals:
            findings.append(ContractDiffService._finding(
                path, 'breaking', 'enum_violation',
                json.dumps(enum_vals, ensure_ascii=False),
                ContractDiffService._short(actual),
                '枚举值不在契约范围内'
            ))

        if (expected_type == 'object' or schema.get('properties')) and isinstance(actual, dict):
            props = schema.get('properties') or {}
            required = schema.get('required') or []
            # 简化 schema：无 required 时，properties 键视为应存在（可选：仅检查存在于 schema 的）
            # 按 OpenAPI 习惯：required 列表为准；若无 required，不强制缺失为 breaking
            for key in required:
                child_path = '{}.{}'.format(path, key) if path != '$' else '$.{}'.format(key)
                if key not in actual:
                    child_schema = props.get(key) or {}
                    findings.append(ContractDiffService._finding(
                        child_path, 'breaking', 'missing_field',
                        ContractDiffService._expected_desc(child_schema, required=True),
                        'absent',
                        '必填字段缺失: {}'.format(key)
                    ))
                else:
                    child_schema = props.get(key) or {}
                    ContractDiffService._walk(child_schema, actual.get(key), child_path, findings, depth + 1)

            for key, child_schema in props.items():
                if key in required:
                    continue
                child_path = '{}.{}'.format(path, key) if path != '$' else '$.{}'.format(key)
                if key not in actual:
                    continue
                ContractDiffService._walk(child_schema or {}, actual.get(key), child_path, findings, depth + 1)

            for key in actual.keys():
                if key not in props:
                    child_path = '{}.{}'.format(path, key) if path != '$' else '$.{}'.format(key)
                    findings.append(ContractDiffService._finding(
                        child_path, 'compatible', 'extra_field',
                        '契约未声明（兼容扩展）', ContractDiffService._short(actual.get(key)),
                        '返回了契约未声明字段: {}'.format(key)
                    ))

        if expected_type == 'array' and isinstance(actual, list):
            items_schema = schema.get('items') or {}
            limit = min(len(actual), ContractDiffService.ARRAY_COMPARE_LIMIT)
            for i in range(limit):
                child_path = '{}[{}]'.format(path, i)
                ContractDiffService._walk(items_schema, actual[i], child_path, findings, depth + 1)
            if len(actual) > ContractDiffService.ARRAY_COMPARE_LIMIT:
                findings.append(ContractDiffService._finding(
                    path, 'info', 'array_truncated',
                    'compare_all', 'truncated_{}'.format(ContractDiffService.ARRAY_COMPARE_LIMIT),
                    '数组过长，仅比对前 {} 项'.format(ContractDiffService.ARRAY_COMPARE_LIMIT)
                ))

    @staticmethod
    def _json_type(value):
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'boolean'
        if isinstance(value, int) and not isinstance(value, bool):
            return 'integer'
        if isinstance(value, float):
            return 'number'
        if isinstance(value, str):
            return 'string'
        if isinstance(value, list):
            return 'array'
        if isinstance(value, dict):
            return 'object'
        return type(value).__name__

    @staticmethod
    def _type_compatible(expected, actual):
        if expected == actual:
            return True
        # JSON Schema number 包含 integer
        if expected == 'number' and actual == 'integer':
            return True
        # 部分文档写 number 实际返回 float/int 已覆盖；string vs number 不兼容
        if expected == 'integer' and actual == 'number':
            # 浮点不完全兼容 → breaking
            return False
        return False

    @staticmethod
    def _short(value, limit=200):
        try:
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        except Exception:
            text = str(value)
        if len(text) > limit:
            return text[:limit] + '...'
        return text

    @staticmethod
    def _expected_desc(schema, required=False):
        """把 Schema 片段转成可读期望说明。"""
        schema = schema or {}
        parts = []
        t = schema.get('type')
        if t:
            parts.append(str(t))
        enum_vals = schema.get('enum')
        if enum_vals:
            parts.append('enum={}'.format(json.dumps(enum_vals, ensure_ascii=False)))
        if required:
            parts.append('必填')
        if not parts:
            return '必填字段'
        return ' · '.join(parts)

    @staticmethod
    def _finding(json_path, severity, drift_type, expected, actual, message):
        return {
            'json_path': json_path,
            'severity': severity,
            'drift_type': drift_type,
            'expected': expected if isinstance(expected, str) else ContractDiffService._short(expected),
            'actual': actual if isinstance(actual, str) else ContractDiffService._short(actual),
            'message': message,
        }
