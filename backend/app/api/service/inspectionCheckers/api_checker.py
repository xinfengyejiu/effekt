# encoding: UTF-8
"""HTTP 接口巡检引擎。"""
import json
import logging
import time
import traceback
import requests

logger = logging.getLogger(__name__)


class ApiChecker(object):
    """执行 HTTP 接口巡检并校验断言。"""

    def execute(self, config, timeout=30):
        """
        执行接口巡检。
        Args:
            config: dict — 包含 url, method, headers, body, body_type, timeout, assertions
            timeout: int — 全局超时秒数
        Returns:
            dict: {status, result, error_message, duration_ms}
                status: 'pass' | 'fail' | 'error'
                result: dict — 执行结果详情
                error_message: str — 异常时的错误信息
                duration_ms: int — 耗时毫秒
        """
        url = config.get('url', '')
        method = config.get('method', 'GET').upper()
        headers = config.get('headers', {})
        body = config.get('body')
        body_type = config.get('body_type', 'json')
        req_timeout = min(config.get('timeout', 5000) / 1000.0, timeout)
        assertions = config.get('assertions', [])

        start = time.time()
        try:
            # 构建请求
            kwargs = {'headers': headers, 'timeout': req_timeout}
            if body and method in ('POST', 'PUT', 'PATCH'):
                if body_type == 'json':
                    if isinstance(body, str):
                        kwargs['data'] = body.encode('utf-8')
                        if 'Content-Type' not in headers:
                            headers['Content-Type'] = 'application/json'
                        kwargs['headers'] = headers
                    else:
                        kwargs['json'] = body
                elif body_type == 'form':
                    kwargs['data'] = body
                else:
                    kwargs['data'] = body

            resp = requests.request(method, url, **kwargs)
            duration_ms = int((time.time() - start) * 1000)

            # 解析响应
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = None

            result = {
                'status_code': resp.status_code,
                'response_time': duration_ms,
                'response_body': resp.text[:2000] if resp.text else '',
                'response_json': resp_json,
                'assertion_results': [],
            }

            # 执行断言
            all_passed = True
            for assertion in assertions:
                a_result = self._check_assertion(assertion, resp, resp_json, duration_ms)
                result['assertion_results'].append(a_result)
                if not a_result.get('passed'):
                    all_passed = False

            status = 'pass' if all_passed else 'fail'
            return {
                'status': status,
                'result': result,
                'error_message': '' if all_passed else '断言校验失败',
                'duration_ms': duration_ms,
            }

        except requests.exceptions.Timeout:
            duration_ms = int((time.time() - start) * 1000)
            return {'status': 'error', 'result': {}, 'error_message': '请求超时', 'duration_ms': duration_ms}
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.warning('接口巡检异常: %s %s -> %s', method, url, str(e))
            return {'status': 'error', 'result': {}, 'error_message': str(e), 'duration_ms': duration_ms}

    def _check_assertion(self, assertion, resp, resp_json, response_time):
        """校验单个断言。"""
        a_type = assertion.get('type', '')
        operator = assertion.get('operator', 'eq')
        expected = assertion.get('expected')
        a_result = {'type': a_type, 'expected': expected, 'operator': operator, 'passed': False}

        try:
            if a_type == 'status_code':
                actual = resp.status_code
                a_result['actual'] = actual
                a_result['passed'] = self._compare(actual, operator, expected)

            elif a_type == 'response_time':
                actual = response_time
                a_result['actual'] = actual
                a_result['expected'] = '{} {}'.format(operator, expected)
                a_result['passed'] = self._compare(actual, operator, expected)

            elif a_type == 'json_path':
                path = assertion.get('path', '')
                actual = self._extract_json_path(resp_json, path)
                a_result['path'] = path
                a_result['actual'] = actual
                a_result['passed'] = self._compare(actual, operator, expected)

            elif a_type == 'header':
                header_name = assertion.get('header', '')
                actual = resp.headers.get(header_name, '')
                a_result['header'] = header_name
                a_result['actual'] = actual
                a_result['passed'] = self._compare(actual, operator, expected)

            elif a_type == 'body_contains':
                actual = expected in resp.text
                a_result['actual'] = actual
                a_result['passed'] = actual is True

            elif a_type == 'body_not_contains':
                actual = expected not in resp.text
                a_result['actual'] = actual
                a_result['passed'] = actual is True

        except Exception as e:
            a_result['error'] = str(e)
            a_result['passed'] = False

        return a_result

    @staticmethod
    def _compare(actual, operator, expected):
        if operator == 'eq':
            return actual == expected
        elif operator == 'ne':
            return actual != expected
        elif operator == 'gt':
            return actual > expected
        elif operator == 'gte':
            return actual >= expected
        elif operator == 'lt':
            return actual < expected
        elif operator == 'lte':
            return actual <= expected
        elif operator == 'contains':
            return str(expected) in str(actual)
        elif operator == 'not_empty':
            return actual is not None and actual != '' and actual != []
        elif operator == 'is_null':
            return actual is None or actual == '' or actual == []
        return False

    @staticmethod
    def _extract_json_path(data, path):
        """简单的 JSONPath 提取（支持 $.a.b.c 和 $.a[0].b 格式）。"""
        if data is None or not path:
            return None
        parts = path.strip().split('.')
        if parts and parts[0] == '$':
            parts = parts[1:]
        current = data
        for part in parts:
            if current is None:
                return None
            # 处理数组索引 a[0]
            if '[' in part and part.endswith(']'):
                key, idx_str = part.split('[', 1)
                idx = int(idx_str.rstrip(']'))
                if key:
                    current = current.get(key) if isinstance(current, dict) else None
                if isinstance(current, list) and len(current) > idx:
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
