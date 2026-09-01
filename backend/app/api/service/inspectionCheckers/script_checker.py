# encoding: UTF-8
"""自定义脚本巡检引擎。"""
import logging
import os
import subprocess
import tempfile
import time

logger = logging.getLogger(__name__)


class ScriptChecker(object):
    """执行自定义脚本并校验结果断言。"""

    def execute(self, config, timeout=30):
        """
        执行脚本巡检。
        config 包含:
            language: str — python / shell
            script: str — 脚本内容
            timeout: int — 超时秒数
            env_vars: dict — 环境变量
            assertions: list — 断言规则
        """
        language = config.get('language', 'python')
        script = config.get('script', '')
        req_timeout = min(config.get('timeout', 30), timeout)
        env_vars = config.get('env_vars', {})
        assertions = config.get('assertions', [])

        if not script:
            return {'status': 'error', 'result': {}, 'error_message': '脚本内容为空', 'duration_ms': 0}

        start = time.time()
        try:
            # 将脚本写入临时文件
            if language == 'python':
                suffix = '.py'
                cmd_prefix = ['python']
            elif language in ('shell', 'bash'):
                suffix = '.sh'
                cmd_prefix = ['bash']
            else:
                return {'status': 'error', 'result': {},
                        'error_message': '不支持的语言: {}'.format(language), 'duration_ms': 0}

            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
                f.write(script)
                script_path = f.name

            try:
                # 构建环境变量
                env = os.environ.copy()
                for k, v in env_vars.items():
                    env[k] = str(v)

                # 执行脚本
                proc = subprocess.run(
                    cmd_prefix + [script_path],
                    capture_output=True,
                    text=True,
                    timeout=req_timeout,
                    env=env,
                    cwd=tempfile.gettempdir(),
                )

                duration_ms = int((time.time() - start) * 1000)
                exit_code = proc.returncode
                stdout = proc.stdout[:5000] if proc.stdout else ''
                stderr = proc.stderr[:2000] if proc.stderr else ''

                result = {
                    'exit_code': exit_code,
                    'stdout': stdout,
                    'stderr': stderr,
                    'duration': duration_ms,
                    'assertion_results': [],
                }

                # 如果没有自定义断言，默认退出码 0 为通过
                if not assertions:
                    all_passed = (exit_code == 0)
                else:
                    all_passed = True
                    for assertion in assertions:
                        a_result = self._check_assertion(assertion, exit_code, stdout, stderr)
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

            finally:
                try:
                    os.unlink(script_path)
                except OSError:
                    pass

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start) * 1000)
            return {'status': 'error', 'result': {}, 'error_message': '脚本执行超时 ({}s)'.format(req_timeout),
                    'duration_ms': duration_ms}
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.warning('脚本巡检异常: %s', str(e))
            return {'status': 'error', 'result': {}, 'error_message': str(e), 'duration_ms': duration_ms}

    @staticmethod
    def _check_assertion(assertion, exit_code, stdout, stderr):
        a_type = assertion.get('type', '')
        expected = assertion.get('expected')
        operator = assertion.get('operator', 'eq')
        a_result = {'type': a_type, 'expected': expected, 'passed': False}

        try:
            if a_type == 'exit_code':
                a_result['actual'] = exit_code
                a_result['passed'] = exit_code == expected

            elif a_type == 'stdout_contains':
                a_result['actual'] = expected in stdout
                a_result['passed'] = a_result['actual']

            elif a_type == 'stdout_not_contains':
                a_result['actual'] = expected not in stdout
                a_result['passed'] = a_result['actual']

            elif a_type == 'stderr_contains':
                a_result['actual'] = expected in stderr
                a_result['passed'] = a_result['actual']

            elif a_type == 'stderr_empty':
                a_result['actual'] = len(stderr.strip()) == 0
                a_result['passed'] = a_result['actual']

            elif a_type == 'stdout_matches':
                import re
                a_result['actual'] = bool(re.search(expected, stdout))
                a_result['passed'] = a_result['actual']

        except Exception as e:
            a_result['error'] = str(e)
            a_result['passed'] = False

        return a_result
