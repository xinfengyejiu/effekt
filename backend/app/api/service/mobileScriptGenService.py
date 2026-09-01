# encoding: UTF-8
"""
AI 脚本生成服务 - 根据测试用例步骤自动生成 pytest + uiautomator2 脚本
"""
import json
import logging
import os
from pathlib import Path

from app.core.config import MOBILE_AUTOMATION_ROOT

logger = logging.getLogger(__name__)


class MobileScriptGenService(object):

    @staticmethod
    def _build_script_prompt(project_name, app_package, launch_activity, case_items):
        """构造 AI 脚本生成提示词。"""
        cases_desc = []
        for i, item in enumerate(case_items, 1):
            case_key = item.get('case_key', '')
            title = item.get('title', '')
            steps = item.get('steps', '')
            # 解析步骤
            if isinstance(steps, str):
                try:
                    steps_data = json.loads(steps)
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

            cases_desc.append('''### 用例{0}
- 编号: {case_key}
- 标题: {title}
- 步骤:
{steps_text}'''.format(i, case_key=case_key, title=title, steps_text=steps_text))

        cases_text = '\n\n'.join(cases_desc)

        # 项目名转安全目录名
        safe_project_name = ''.join(c if c.isalnum() or c in ('_', '-', ' ') else '_' for c in project_name).strip()
        if not safe_project_name:
            safe_project_name = 'default'

        prompt = '''你是一个专业的移动端自动化测试工程师，擅长使用 Python + pytest + uiautomator2 编写 Android 自动化测试脚本。

## 项目信息
- 项目名称：{project_name}
- 应用包名：{app_package}
- 启动 Activity：{launch_activity}

## 需要生成脚本的测试用例
{cases_text}

## 技术要求
1. 使用 pytest 作为测试框架，每个用例生成一个 test 函数
2. 使用 uiautomator2 进行设备操作
3. 每个步骤都要有断言验证
4. 截图保存在 MOBILE_ARTIFACT_DIR 环境变量指定的目录中
5. 每步操作通过 JSONL 文件上报进度（文件路径在 MOBILE_RUNTIME_STEPS_FILE 环境变量中）

## 通用方法（必须使用）

项目已提供通用方法模块，**必须 import 并复用**，不要重复实现以下功能：

```python
import sys, os
# 将 mobile-autotest 根目录加入 sys.path（脚本在 tests/项目名/模块/ 下）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tests.{safe_project_name}.common import (
    init_device,          # 初始化设备（连接、亮屏、解锁）
    clear_data_and_launch, # 清数据 + 预授权 + 启动应用
    login_joyhub,          # 完整登录流程（引导页→登录页→填表单→校验首页）
    dismiss_permission_dialogs,  # 关闭权限弹窗
    _screenshot,           # 截图
    _report_step,          # 上报步骤（如果 mobile_steps 不可用时使用此函数）
    finish_step,           # 完成步骤上报
    PACKAGE_NAME,          # 应用包名常量
)
```

**每个测试函数的标准流程：**
1. 调用 `init_device()` 初始化设备
2. 调用 `clear_data_and_launch(device)` 清除数据并启动应用
3. 调用 `login_joyhub(device)` 完成登录（如果需要登录态）
4. 执行测试用例的具体步骤
5. 断言验证结果

## 代码模板

请严格按照以下模板生成代码：

```python
# -*- coding: utf-8 -*-
import sys
import os
import time
import pytest

# ── 将 mobile-autotest 根目录加入路径 ──
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tests.{safe_project_name}.common import (
    init_device,
    clear_data_and_launch,
    login_joyhub,
    dismiss_permission_dialogs,
    _screenshot,
    _report_step,
    finish_step,
    PACKAGE_NAME,
)


@pytest.fixture(scope='module')
def device():
    """初始化设备并登录。"""
    dev = init_device()
    clear_data_and_launch(dev)
    login_joyhub(dev)
    yield dev


def test_{{用例编号或关键词}}(device):
    """用例标题描述。"""
    # 具体测试步骤
    finish_step('步骤描述', action_type='ui')
    _screenshot(device, 'step_name')
    # 断言验证
    assert ...
```

## 输出要求
1. 为每个用例生成一个独立的 test 函数
2. 函数命名格式：test_{{用例编号或关键词}}（纯英文+下划线）
3. **必须 import 并使用 common 模块中的通用方法**，不要重复实现登录、清数据、设备初始化等逻辑
4. 每个步骤调用 _report_step() 或 finish_step() 上报进度
5. 关键操作后调用 _screenshot() 截图
6. 用 assert 进行断言验证
7. 所有中文注释保留
8. 只输出 Python 代码，不要输出解释文字

请为以上所有用例生成完整的测试脚本文件。'''.format(
            project_name=project_name or '未知项目',
            app_package=app_package or '',
            launch_activity=launch_activity or '',
            cases_text=cases_text,
            safe_project_name=safe_project_name,
        )
        return prompt, safe_project_name

    @staticmethod
    def generate_scripts(project_id, case_ids, session=None):
        """根据用例生成 pytest 脚本。

        如果 session 为 None，内部自动创建短 session 查询数据。
        查询完成后立即关闭 session，不持有 DB 连接进行 AI 调用。

        Args:
            project_id: 项目 ID
            case_ids: 用例 ID 列表
            session: 数据库会话（可选，为 None 时自动创建）

        Returns:
            dict: {"scripts": [{"case_id": int, "file_path": str, "code": str}], "project_dir": str}
        """
        from app.api.model.projectModel import Project
        from app.api.model.caseModel import TestCase, Module
        from app.api.model.mobileAutomationModel import MobileApp
        from app.api.service.aiService import AIService

        # 使用短 session 查询数据，查询完立即关闭
        if session is not None:
            sess = session
            own_session = False
        else:
            from app.core.database import get_db_context
            ctx = get_db_context()
            sess = ctx.__enter__()
            own_session = True

        try:
            # 查询项目
            project = sess.query(Project).filter(
                Project.id == int(project_id), Project.is_delete == 0
            ).first()
            if not project:
                return None, '项目不存在'
            project_name = project.name

            # 查询用例
            cases = sess.query(TestCase).filter(
                TestCase.id.in_([int(cid) for cid in case_ids]),
                TestCase.is_delete == 0,
            ).all()
            if not cases:
                return None, '未找到有效用例'

            # 查询模块，构建 module_id -> 模块路径的映射
            all_modules = sess.query(Module).filter(
                Module.project_id == int(project_id), Module.is_delete == 0
            ).all()
            module_map = {m.id: m for m in all_modules}

            def _build_module_path(module_id):
                """从 module_id 向上追溯，返回如 '一级/二级' 的模块路径。"""
                if not module_id or module_id not in module_map:
                    return ''
                parts = []
                cur = module_map[module_id]
                while cur:
                    parts.append(cur.name)
                    if cur.parent_id and cur.parent_id in module_map and cur.parent_id != cur.id:
                        cur = module_map[cur.parent_id]
                    else:
                        break
                parts.reverse()
                return '/'.join(parts)

            # 构造用例描述
            case_items = [
                {
                    'case_key': getattr(c, 'case_key', '') or '',
                    'title': getattr(c, 'title', '') or '',
                    'steps': getattr(c, 'steps', '') or '',
                }
                for c in cases
            ]

            # 获取第一个关联 app 的包名
            app = sess.query(MobileApp).filter(
                MobileApp.project_id == int(project_id), MobileApp.enabled == 1
            ).first()
            app_package = app.package_name if app else ''
            launch_activity = app.launch_activity if app else ''
        finally:
            # 查询完成，如果是我们自己创建的 session，立即关闭
            if own_session:
                try:
                    sess.commit()
                except Exception:
                    sess.rollback()
                finally:
                    sess.close()

        # 项目名转安全目录名
        safe_project_name = ''.join(c if c.isalnum() or c in ('_', '-', ' ') else '_' for c in project_name).strip()
        if not safe_project_name:
            safe_project_name = 'default'

        prompt, safe_project_name = MobileScriptGenService._build_script_prompt(
            project_name, app_package, launch_activity, case_items
        )

        system_prompt = '你是一个专业的移动端自动化测试工程师。你必须只输出合法的 Python 代码。'

        # 调用 AI 生成脚本
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return None, '未配置API密钥，请在.env中配置METEOR_API_KEY'

            is_plan_key = '/plan/' in api_base
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)

            code = AIService._request_model(
                OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx,
                max_retries=AIConfig.MAX_RETRIES,
                max_tokens=8192,
                temperature=0.2,
                system_prompt=system_prompt,
            )

            # 提取代码块
            import re as _re
            generated_code = code
            fence_match = _re.search(r'```python\s*([\s\S]*?)\s*```', code)
            if fence_match:
                generated_code = fence_match.group(1).strip()

        except Exception as exc:
            logger.exception('AI脚本生成失败: %s', exc)
            return None, 'AI脚本生成失败: {0}'.format(str(exc)[:300])

        # 写入文件：按项目名 + 模块路径创建子目录
        first_case = cases[0]
        module_path = _build_module_path(getattr(first_case, 'module_id', None))

        scripts_root = Path(MOBILE_AUTOMATION_ROOT) / 'tests' / safe_project_name
        if module_path:
            # 模块名转安全目录名
            safe_module_path = ''.join(c if c.isalnum() or c in ('_', '-', ' ') else '_' for c in module_path).strip()
            if safe_module_path:
                scripts_root = scripts_root / safe_module_path
        scripts_root.mkdir(parents=True, exist_ok=True)

        # 按用例拆分：如果 AI 返回了多个 test 函数，按函数边界拆分文件
        # 简单策略：一个项目生成一个文件，文件名取第一个用例的关键词
        first_case_key = case_items[0].get('case_key', '') or 'test'
        safe_filename = ''.join(c if c.isalnum() or c == '_' else '_' for c in first_case_key).strip('_').lower()
        if not safe_filename:
            safe_filename = 'test_script'
        file_name = 'test_{0}.py'.format(safe_filename[:50])
        file_path = scripts_root / file_name
        file_path.write_text(generated_code, encoding='utf-8')

        result = {
            'project_dir': str(scripts_root.relative_to(MOBILE_AUTOMATION_ROOT)),
            'scripts': [
                {
                    'case_id': int(c.id),
                    'case_key': case_items[i].get('case_key', ''),
                    'file_path': str(file_path.relative_to(MOBILE_AUTOMATION_ROOT)),
                }
                for i, c in enumerate(cases)
            ],
            'code': generated_code,
            'file_path': str(file_path),
        }
        return result, ''
