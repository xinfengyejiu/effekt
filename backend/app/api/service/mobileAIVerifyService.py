# encoding: UTF-8
"""
AI 执行验证服务 - 利用 AI 分析 UI 快照判断移动端测试用例执行结果
"""
import json
import logging

logger = logging.getLogger(__name__)

# AI 验证结果
VERDICT_PASS = 'pass'
VERDICT_FAIL = 'fail'
VERDICT_UNCERTAIN = 'uncertain'


class MobileAIVerifyService(object):

    @staticmethod
    def _build_verify_prompt(case_title, case_steps, page_snapshot, exit_code, error_message):
        """构造 AI 验证提示词。

        Args:
            case_title: 用例标题
            case_steps: 用例步骤（文本或列表）
            page_snapshot: 页面 UI 快照（已解析的元素列表）
            exit_code: pytest 退出码
            error_message: pytest 错误信息
        """
        # 提取关键 UI 元素（过滤空文本和无意义的元素）
        elements = page_snapshot.get('elements', []) if isinstance(page_snapshot, dict) else []
        meaningful_elements = [
            {
                'text': e.get('text', ''),
                'content_desc': e.get('content_desc', ''),
                'resource_id': e.get('resource_id', ''),
                'class_name': e.get('class_name', ''),
                'clickable': e.get('clickable', False),
                'bounds': e.get('bounds', []),
            }
            for e in elements
            if e.get('text') or e.get('content_desc') or e.get('resource_id')
        ][:50]  # 限制元素数量，避免 prompt 过长

        # 格式化步骤
        if isinstance(case_steps, list):
            steps_text = '\n'.join(
                '{0}. {1}'.format(i + 1, s.get('content', s.get('description', str(s))) if isinstance(s, dict) else str(s))
                for i, s in enumerate(case_steps)
            )
        else:
            steps_text = str(case_steps or '无详细步骤')

        # 截取元素为简洁的文本表示
        elements_text = json.dumps(meaningful_elements, ensure_ascii=False, indent=2)

        prompt = '''你是一个移动端自动化测试验证专家。你的任务是根据测试执行后的页面状态，判断测试用例是否真正执行成功。

## 用例信息
标题：{case_title}
步骤：
{steps_text}

## 执行结果
pytest 退出码：{exit_code}
错误信息：{error_message}

## 执行后页面 UI 元素列表（Android UI Automator 快照）
```json
{elements_text}
```

## 判断要求
请根据以上信息，严格判断该用例是否执行成功。判断逻辑如下：

1. 如果 exit_code != 0，且 error_message 不为空，说明脚本执行出错，大概率失败
2. 即使 exit_code == 0，也需要验证页面状态是否符合预期：
   - 根据用例步骤推断期望看到的页面元素（如：登录成功后应看到"首页"、"我的"等元素）
   - 检查当前 UI 元素列表中是否包含预期元素
   - 检查是否有异常弹窗、错误提示等阻断元素
3. 如果 UI 元素信息不足以判断，请标记为 uncertain

## 输出格式
必须输出严格可解析的 JSON，格式如下：
{{"verdict": "pass|fail|uncertain", "confidence": 0-100的整数, "reason": "判断理由，100字以内"}}

其中：
- verdict: pass=通过, fail=失败, uncertain=不确定需人工确认
- confidence: 判断置信度，0-100
- reason: 简明扼要的判断理由

只输出 JSON，不要输出其他内容。'''.format(
            case_title=case_title or '未知用例',
            steps_text=steps_text,
            exit_code=exit_code,
            error_message=error_message or '无',
            elements_text=elements_text,
        )
        return prompt

    @staticmethod
    def verify(case_title, case_steps, page_snapshot, exit_code, error_message=None):
        """调用 AI 验证用例执行结果。

        Returns:
            dict: {"verdict": str, "confidence": int, "reason": str}
        """
        try:
            from app.api.service.aiService import AIService

            prompt = MobileAIVerifyService._build_verify_prompt(
                case_title, case_steps, page_snapshot, exit_code, error_message
            )

            system_prompt = '你是一个专业的移动端测试验证专家。你必须只输出合法的 JSON 对象。'

            result, error = AIService.request_json(
                prompt,
                error_prefix='AI执行验证',
                system_prompt=system_prompt,
                max_tokens=512,
                temperature=0.1,  # 低温度确保判断稳定性
            )

            if error:
                logger.warning('AI验证失败: %s', error)
                return {
                    'verdict': VERDICT_UNCERTAIN,
                    'confidence': 0,
                    'reason': 'AI验证服务异常：{0}'.format(error[:200]),
                    'ai_available': False,
                }

            # 校验返回格式
            verdict = result.get('verdict', '')
            if verdict not in (VERDICT_PASS, VERDICT_FAIL, VERDICT_UNCERTAIN):
                logger.warning('AI验证返回非法verdict: %s, 完整结果: %s', verdict, result)
                return {
                    'verdict': VERDICT_UNCERTAIN,
                    'confidence': 0,
                    'reason': 'AI返回格式异常：verdict={0}'.format(verdict),
                    'ai_available': False,
                }

            return {
                'verdict': verdict,
                'confidence': int(result.get('confidence', 50)),
                'reason': str(result.get('reason', '')),
                'ai_available': True,
            }

        except Exception as exc:
            logger.exception('AI验证异常: %s', exc)
            return {
                'verdict': VERDICT_UNCERTAIN,
                'confidence': 0,
                'reason': 'AI验证异常：{0}'.format(str(exc)[:200]),
                'ai_available': False,
            }

    @staticmethod
    def decide_case_status(verdict, exit_code):
        """根据 AI 验证结果和 pytest 退出码，综合判定用例最终状态。

        Returns:
            int: 用例状态码 (2=通过, 3=失败, 4=阻塞)
        """
        if verdict == VERDICT_PASS:
            return 2  # 通过
        elif verdict == VERDICT_FAIL:
            return 3  # 失败
        elif verdict == VERDICT_UNCERTAIN:
            return 4  # 阻塞，需人工确认
        else:
            # AI 不可用时，回退到 pytest 退出码判定
            return 2 if exit_code == 0 else 3
