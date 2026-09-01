# encoding: UTF-8
"""
AI 脚本自动调试服务 - 生成脚本后自动执行、AI修复、循环直到通过
"""
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

from app.core.config import (
    MOBILE_AUTOMATION_ROOT,
    MOBILE_AUTOMATION_PYTHON,
    MOBILE_AUTOMATION_TIMEOUT_SECONDS,
    MOBILE_AUTOMATION_APPIUM_URL,
)

logger = logging.getLogger(__name__)


class MobileScriptDebugService(object):

    @staticmethod
    def debug_and_fix(project_id, case_ids, session, device_serial, mobile_app_id, max_retries=3):
        """生成脚本并自动调试修复。

        注意：不在整个调试过程中持有 session，避免数据库连接超时断开。
        每次需要查数据时使用 get_db_context() 创建短 session。

        Returns:
            tuple: (result_dict, error_string)
            result_dict = {
                'passed': bool,
                'attempts': int,
                'code': str,          # 最终代码
                'file_path': str,     # 脚本文件绝对路径
                'project_dir': str,   # 相对目录
                'scripts': [...],     # 用例-文件映射
                'logs': [             # 每轮调试日志
                    {'round': int, 'exit_code': int, 'output': str, 'ai_fix': str, 'passed': bool},
                    ...
                ]
            }
        """
        from app.api.model.mobileAutomationModel import MobileApp
        from app.api.model.caseModel import TestCase
        from app.api.service.mobileScriptGenService import MobileScriptGenService
        from app.core.database import get_db_context

        # 用短 session 查询应用配置，查询完立即关闭
        with get_db_context() as short_session:
            app = short_session.query(MobileApp).filter(
                MobileApp.id == int(mobile_app_id), MobileApp.enabled == 1
            ).first()
            if not app:
                return None, '应用配置不存在或已禁用'
            app_package = app.package_name or ''
            launch_activity = app.launch_activity or ''

        # 第 1 步：生成初始脚本（使用新的短 session）
        with get_db_context() as gen_session:
            gen_result, gen_error = MobileScriptGenService.generate_scripts(
                project_id, case_ids, gen_session
            )
        if gen_error:
            return None, '脚本生成失败: {0}'.format(gen_error)

        script_file = gen_result['file_path']
        script_selector = gen_result['scripts'][0]['file_path'].replace('\\', '/')
        py_path = script_selector.replace('.py', '')
        func_name = py_path.rsplit('/', 1)[-1] if '/' in py_path else py_path.rsplit('\\', 1)[-1]
        pytest_selector = '{0}::{1}'.format(script_selector, func_name)

        # 查询用例步骤信息（短 session）
        with get_db_context() as case_session:
            cases = case_session.query(TestCase).filter(
                TestCase.id.in_([int(cid) for cid in case_ids]),
                TestCase.is_delete == 0,
            ).all()
            case_steps_list = [
                {
                    'case_key': getattr(c, 'case_key', ''),
                    'title': getattr(c, 'title', ''),
                    'steps': getattr(c, 'steps', '') or '',
                }
                for c in cases
            ]

        # 读取初始代码
        current_code = Path(script_file).read_text(encoding='utf-8') if Path(script_file).exists() else ''

        logs = []
        passed = False
        attempts = 0

        for attempt in range(1, max_retries + 1):
            attempts = attempt
            logger.info('[AI调试] 第 %d/%d 轮执行: %s', attempt, max_retries, pytest_selector)

            # 执行 pytest
            exec_result = MobileScriptDebugService._run_pytest_once(
                pytest_selector, device_serial, app_package, launch_activity,
                MOBILE_AUTOMATION_TIMEOUT_SECONDS,
            )

            exit_code = exec_result['exit_code']
            output = exec_result['output']
            round_passed = (exit_code == 0)

            log_entry = {
                'round': attempt,
                'exit_code': exit_code,
                'output': output[-2000:] if len(output) > 2000 else output,  # 截断避免过长
                'passed': round_passed,
                'ai_fix': '',
            }

            if round_passed:
                passed = True
                logs.append(log_entry)
                logger.info('[AI调试] 第 %d 轮执行通过', attempt)
                break

            # 执行失败，AI 修复
            if attempt < max_retries:
                logger.info('[AI调试] 第 %d 轮失败，AI 修复中...', attempt)
                fixed_code, fix_reason = MobileScriptDebugService._ai_fix_script(
                    current_code, output, case_steps_list, app_package, launch_activity,
                )

                if fixed_code and fixed_code != current_code:
                    # 写入修复后的代码
                    Path(script_file).write_text(fixed_code, encoding='utf-8')
                    current_code = fixed_code
                    log_entry['ai_fix'] = fix_reason or 'AI 已修复代码'
                    logger.info('[AI调试] AI 修复完成: %s', fix_reason)
                else:
                    log_entry['ai_fix'] = 'AI 未能生成有效修复代码'
                    logger.warning('[AI调试] AI 未能生成有效修复代码')

            logs.append(log_entry)

        # 读取最终代码
        final_code = Path(script_file).read_text(encoding='utf-8') if Path(script_file).exists() else current_code

        result = {
            'passed': passed,
            'attempts': attempts,
            'code': final_code,
            'file_path': gen_result['file_path'],
            'project_dir': gen_result['project_dir'],
            'scripts': gen_result['scripts'],
            'logs': logs,
        }
        return result, ''

    @staticmethod
    def _run_pytest_once(selector, device_serial, app_package, launch_activity, timeout):
        """轻量级执行一次 pytest，返回 {exit_code, output}。"""
        # 创建临时目录用于 allure 结果（调试模式不需要保留）
        temp_allure = tempfile.mkdtemp(prefix='mobile_debug_')

        command = [
            MOBILE_AUTOMATION_PYTHON, '-m', 'pytest', selector,
            '--alluredir', temp_allure,
            '-v', '--tb=short',
        ]

        env = os.environ.copy()
        env.update({
            'MOBILE_DEVICE_SERIAL': device_serial or '',
            'MOBILE_APP_PACKAGE': app_package or '',
            'MOBILE_ARTIFACT_DIR': temp_allure,
            'MOBILE_RUNTIME_STEPS_FILE': '',
            'MOBILE_APPIUM_URL': MOBILE_AUTOMATION_APPIUM_URL,
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONUTF8': '1',
        })

        try:
            process = subprocess.Popen(
                command,
                cwd=MOBILE_AUTOMATION_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            try:
                raw_output, _ = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except Exception:
                    process.kill()
                return {
                    'exit_code': -1,
                    'output': '执行超时（{0} 秒）'.format(timeout),
                }

            output = raw_output.decode('utf-8', errors='replace') if raw_output else ''
            return {
                'exit_code': process.returncode,
                'output': output,
            }

        except Exception as exc:
            logger.exception('[AI调试] pytest 执行异常: %s', exc)
            return {
                'exit_code': -1,
                'output': '执行异常: {0}'.format(str(exc)[:500]),
            }

    @staticmethod
    def _ai_fix_script(original_code, error_output, case_steps_list, app_package, launch_activity):
        """调用 AI 分析错误并修复脚本代码。

        Returns:
            tuple: (fixed_code, fix_reason)
        """
        try:
            from app.api.service.aiService import AIService
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return None, '未配置API密钥'

            prompt = MobileScriptDebugService._build_debug_prompt(
                original_code, error_output, case_steps_list, app_package, launch_activity,
            )

            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(
                connect=AIConfig.CONNECT_TIMEOUT,
                read=max(AIConfig.READ_TIMEOUT, 120),
                write=max(AIConfig.READ_TIMEOUT, 120),
                pool=AIConfig.CONNECT_TIMEOUT,
            )

            code = AIService._request_model(
                OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                max_retries=AIConfig.MAX_RETRIES,
                max_tokens=8192,
                temperature=0.2,
                system_prompt='你是一个专业的移动端自动化测试工程师。你必须只输出修复后的完整 Python 代码，不要输出任何解释文字。',
            )

            # 提取代码块
            fence_match = re.search(r'```python\s*([\s\S]*?)\s*```', code)
            if fence_match:
                fixed_code = fence_match.group(1).strip()
            else:
                fixed_code = code.strip()

            # 提取修复说明（AI 返回的 code 中可能附带说明，取第一个代码块前的文字）
            fix_reason = ''
            before_code = code[:fence_match.start()].strip() if fence_match else ''
            if before_code:
                fix_reason = before_code[-200:]  # 取最后 200 字符作为修复说明

            return fixed_code, fix_reason

        except Exception as exc:
            logger.exception('[AI调试] AI修复失败: %s', exc)
            return None, 'AI修复异常: {0}'.format(str(exc)[:300])

    @staticmethod
    def _build_debug_prompt(original_code, error_output, case_steps_list, app_package, launch_activity):
        """构建 AI 脚本修复 prompt。"""
        # 构造用例步骤描述
        cases_desc = []
        for i, item in enumerate(case_steps_list, 1):
            steps = item.get('steps', '')
            if isinstance(steps, str):
                try:
                    steps_data = __import__('json').loads(steps)
                except Exception:
                    steps_data = steps
            else:
                steps_data = steps
            if isinstance(steps_data, list):
                steps_text = '\n'.join(
                    '  {0}. {1}'.format(
                        j + 1,
                        s.get('content', s.get('description', str(s))) if isinstance(s, dict) else str(s)
                    )
                    for j, s in enumerate(steps_data)
                )
            else:
                steps_text = '  {0}'.format(steps_data)

            cases_desc.append('### 用例{0}\n- 编号: {1}\n- 标题: {2}\n- 步骤:\n{3}'.format(
                i, item.get('case_key', ''), item.get('title', ''), steps_text,
            ))
        cases_text = '\n\n'.join(cases_desc)

        prompt = '''你是一个专业的移动端自动化测试工程师。以下 pytest + uiautomator2 脚本在设备上执行失败，请分析错误原因并修复代码。

## 项目信息
- 应用包名：{app_package}
- 启动 Activity：{launch_activity}

## 测试用例步骤
{cases_text}

## 当前脚本代码
```python
{original_code}
```

## 执行失败输出
```
{error_output}
```

## 修复要求
1. 仔细分析上面的错误输出，找出失败的根本原因
2. 常见失败原因包括：
   - 元素定位失败（resource-id/text 不正确）→ 尝试用其他定位方式（xpath/content-desc/class_name）
   - 等待时间不足 → 增加适当的等待或使用 uiautomator2 的隐式等待
   - 断言条件不对 → 根据实际 UI 调整断言
   - 页面跳转未完成 → 增加等待或检查页面状态
   - **脚本必须包含清数据后启动和登录流程**：如果脚本缺少 `clear_data_and_launch()` 或 `login_joyhub()` 调用，必须添加
3. **必须使用 common 模块的通用方法**（init_device / clear_data_and_launch / login_joyhub），不要自己重写这些逻辑
4. 只修改必要的部分，不要重写整个脚本
5. 保留原有的 import 语句（特别是 sys.path.insert 和 common 模块的 import）
6. 输出完整的修复后代码（用 ```python 代码块包裹）
7. 在代码块前面用一两句话说明你做了什么修改

请输出修复后的完整代码。'''.format(
            app_package=app_package or '',
            launch_activity=launch_activity or '',
            cases_text=cases_text,
            original_code=original_code,
            error_output=error_output[-3000:] if len(error_output) > 3000 else error_output,
        )
        return prompt
