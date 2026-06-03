# encoding: UTF-8
"""
AI服务类 - 用于调用大模型生成测试用例、测试 Skill 和业务规则
"""
import json
import re
import time
import traceback
from pathlib import Path
from flask import current_app, has_app_context


class AIService:
    """AI服务类"""

    @staticmethod
    def generate_test_cases(document_content, template=None):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            key_source = AIConfig.get_api_key_source()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return [], '未配置API密钥，请在.env中配置METEOR_API_KEY'

            is_plan_key = provider == 'custom' and api_key.startswith('plan-')
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            current_app.logger.info(f'AI配置: provider={provider}, base={request_base}, model={model}, key_source={key_source}, key_prefix={api_key[:8]}, plan_key={is_plan_key}')
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)

            skill_content = AIService._load_skill_content()
            chunks = AIService._split_document_content(document_content)
            all_cases = []
            for chunk_index, chunk in enumerate(chunks, 1):
                prompt = AIService._build_prompt(chunk['content'], template, skill_content, chunk_index, len(chunks), chunk['title'])
                result = AIService._request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx)
                try:
                    parsed_result = json.loads(AIService._extract_json_text(result))
                    all_cases.extend(AIService._normalize_cases(parsed_result, template, chunk['title']))
                except json.JSONDecodeError:
                    return [], f'第{chunk_index}段解析结果失败: {result[:200]}'
            return AIService._deduplicate_cases(all_cases), ''
        except Exception as e:
            current_app.logger.error(f'AI生成测试用例失败: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return [], f'AI生成失败: {str(e)}'

    @staticmethod
    def get_embedding(text, model_setting=None):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            text = (text or '').strip()
            if not text:
                return [], ''
            model_setting = model_setting or {}
            api_key = AIConfig.get_api_key()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return AIService._hash_embedding(text), 'local-hash-128'
            provider = model_setting.get('provider') or AIConfig.MODEL_PROVIDER
            api_base = model_setting.get('apiBase') or model_setting.get('api_base') or AIConfig.get_api_base()
            embedding_model = model_setting.get('embeddingModel') or model_setting.get('embedding_model') or 'text-embedding-3-small'
            is_plan_key = provider == 'custom' and api_key.startswith('plan-')
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            client = OpenAI(api_key=api_key, base_url=request_base, http_client=httpx.Client(timeout=timeout, trust_env=False))
            response = client.embeddings.create(model=embedding_model, input=text[:6000])
            embedding = response.data[0].embedding if response.data else []
            if embedding:
                return embedding, embedding_model
            return AIService._hash_embedding(text), 'local-hash-128'
        except Exception as e:
            if has_app_context():
                current_app.logger.warning(f'Embedding模型调用失败，使用本地向量兜底: {str(e)}')
            return AIService._hash_embedding(text), 'local-hash-128'

    @staticmethod
    def _hash_embedding(text, dimensions=128):
        import hashlib
        import math
        vector = [0.0] * dimensions
        tokens = re.findall(r'[0-9A-Za-z_]+', text or '')
        for cn_text in re.findall(r'[\u4e00-\u9fa5]{2,}', text or ''):
            tokens.append(cn_text)
            for size in (2, 3, 4):
                for index in range(0, max(0, len(cn_text) - size + 1)):
                    tokens.append(cn_text[index:index + size])
        if not tokens:
            tokens = [text or 'empty']
        for token in tokens:
            digest = hashlib.md5(token.encode('utf-8')).digest()
            index = int.from_bytes(digest[:4], 'big') % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 8) / 8.0
            vector[index] += sign * weight
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [round(item / norm, 6) for item in vector]

    @staticmethod
    def chat_with_context(query, evidences=None, model_setting=None):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            evidences = evidences or []
            model_setting = model_setting or {}
            api_key = AIConfig.get_api_key()
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return '', '未配置API密钥，请在.env中配置METEOR_API_KEY'
            provider = model_setting.get('provider') or AIConfig.MODEL_PROVIDER
            api_base = model_setting.get('apiBase') or model_setting.get('api_base') or AIConfig.get_api_base()
            model = model_setting.get('model') or AIConfig.get_model()
            temperature = float(model_setting.get('temperature') if model_setting.get('temperature') is not None else AIConfig.OPENAI_TEMPERATURE)
            max_tokens = int(model_setting.get('maxTokens') or model_setting.get('max_tokens') or AIConfig.OPENAI_MAX_TOKENS)
            is_plan_key = provider == 'custom' and api_key.startswith('plan-')
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            prompt = AIService._build_rag_prompt(query, evidences)
            if is_plan_key:
                return AIService._create_plan_message(api_key, request_base, model, prompt, timeout), ''
            client = OpenAI(api_key=api_key, base_url=request_base, http_client=httpx.Client(timeout=timeout, trust_env=False))
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是测试平台的需求问答助手。只要 evidence-list 非空，必须优先依据证据内容回答，并按引用编号标注；不能在已有证据时笼统回答‘未找到充分依据’。证据确实没有覆盖问题时，再说明不足项。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content, ''
        except Exception as e:
            current_app.logger.error(f'知识库问答失败: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return '', f'模型调用失败: {str(e)}'

    @staticmethod
    def _build_rag_prompt(query, evidences):
        if evidences:
            parts = []
            for index, item in enumerate(evidences, 1):
                parts.append(f'[{index}] 文档ID：{item.get("documentId")}；分片：{item.get("chunkNo")}；相关度：{item.get("score")}\n标题：{item.get("title") or ""}\n内容：{item.get("snippet") or ""}')
            evidence_text = '\n\n'.join(parts)
        else:
            evidence_text = '无本地知识库证据。'
        return f'''
你是测试平台的需求问答助手。你只能基于给定需求文档证据回答。若 evidence-list 中存在证据，请先从证据中归纳直接答案，并标注引用；不要因为证据不完整就直接否定命中。只有 evidence-list 为“无本地知识库证据”或证据完全无关时，才说明“当前知识库未找到充分依据”，并列出需要补充的信息。

<evidence-list>
{evidence_text}
</evidence-list>

用户问题：{query}

请严格按以下 Markdown 结构输出，便于前端用“业务名称”作为脑图中心节点，并只截取“直接答案”生成脑图：

## 直接答案
业务名称：用不超过16个字概括当前回答对应的业务/模块/功能名称
- 一级要点名称：一句话说明
  - 二级要点：简短说明
  - 二级要点：简短说明
- 一级要点名称：一句话说明
  - 二级要点：简短说明

## 依据引用
- 按 [1]/[2] 标注对应依据。

## 测试关注点/风险点
- 如适用，列出测试关注点或风险点。

## 信息不足项
- 如有，列出仍需补充的信息；没有则写“无”。
'''.strip()

    @staticmethod
    def request_json(prompt, error_prefix='AI生成JSON'):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return {}, '未配置API密钥，请在.env中配置METEOR_API_KEY'
            is_plan_key = provider == 'custom' and api_key.startswith('plan-')
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            result = AIService._request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx)
            parsed_result = json.loads(AIService._extract_json_text(result))
            if not isinstance(parsed_result, (dict, list)):
                return {}, f'{error_prefix}格式错误'
            return parsed_result, ''
        except json.JSONDecodeError:
            return {}, f'{error_prefix}不是合法 JSON'
        except Exception as e:
            current_app.logger.error(f'{error_prefix}失败: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return {}, f'{error_prefix}失败: {str(e)}'

    @staticmethod
    def _request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx):
        max_retries = AIConfig.MAX_RETRIES
        retry_delay = AIConfig.RETRY_DELAY
        for attempt in range(max_retries):
            try:
                if is_plan_key:
                    return AIService._create_plan_message(api_key, request_base, model, prompt, timeout)
                client = OpenAI(api_key=api_key, base_url=request_base, http_client=httpx.Client(timeout=timeout, trust_env=False))
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的测试知识资产生成助手。必须最终只输出可解析JSON。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=AIConfig.OPENAI_MAX_TOKENS,
                    temperature=AIConfig.OPENAI_TEMPERATURE
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f'AI请求第{attempt + 1}次失败，{retry_delay}秒后重试: {str(e)}')
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    raise

    @staticmethod
    def _normalize_api_base(api_base):
        if not api_base:
            return 'https://api.routin.ai/v1'
        return api_base.rstrip('/').replace('/chat/completions', '')

    @staticmethod
    def _normalize_plan_api_base(api_base):
        if not api_base:
            return 'https://api.routin.ai/plan/v1'
        normalized = api_base.rstrip('/').replace('/chat/completions', '')
        if '/plan/v1' in normalized:
            return normalized
        return normalized.replace('/v1', '/plan/v1')

    @staticmethod
    def _create_plan_message(api_key, api_base, model, prompt, timeout):
        import httpx
        response = httpx.post(
            f'{api_base}/messages',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 4096, 'temperature': 0.7},
            timeout=timeout,
            trust_env=False
        )
        response.raise_for_status()
        return AIService._extract_message_text(response.json())

    @staticmethod
    def _extract_message_text(data):
        if isinstance(data, dict):
            content = data.get('content')
            if isinstance(content, list):
                texts = [part['text'] for part in content if isinstance(part, dict) and part.get('text')]
                if texts:
                    return ''.join(texts)
            if isinstance(content, str):
                return content
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _extract_json_text(result):
        text = result.strip()
        fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if fence_match:
            text = fence_match.group(1).strip()
        if text.startswith('{') or text.startswith('['):
            return text
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if json_match:
            return json_match.group(1).strip()
        return text

    @staticmethod
    def generate_skill_content(req_data):
        return AIService._generate_asset_content(
            req_data=req_data,
            prompt=AIService._build_skill_create_prompt(req_data),
            markdown_key='skill_md',
            normalizer=AIService._normalize_skill_markdown,
            error_prefix='AI生成 Skill 内容'
        )

    @staticmethod
    def generate_business_rule_content(req_data):
        return AIService._generate_asset_content(
            req_data=req_data,
            prompt=AIService._build_business_rule_create_prompt(req_data),
            markdown_key='rule_md',
            normalizer=AIService._normalize_rule_markdown,
            error_prefix='AI生成业务规则内容'
        )

    @staticmethod
    def _generate_asset_content(req_data, prompt, markdown_key, normalizer, error_prefix):
        try:
            from openai import OpenAI
            from config.ai_config import AIConfig
            import httpx

            api_key = AIConfig.get_api_key()
            api_base = AIConfig.get_api_base()
            model = AIConfig.get_model()
            provider = AIConfig.MODEL_PROVIDER
            if not api_key or api_key == '请替换为你的Meteor API Key':
                return {}, '未配置API密钥，请在.env中配置METEOR_API_KEY'
            is_plan_key = provider == 'custom' and api_key.startswith('plan-')
            request_base = AIService._normalize_plan_api_base(api_base) if is_plan_key else AIService._normalize_api_base(api_base)
            timeout = httpx.Timeout(connect=AIConfig.CONNECT_TIMEOUT, read=AIConfig.READ_TIMEOUT, write=AIConfig.READ_TIMEOUT, pool=AIConfig.CONNECT_TIMEOUT)
            result = AIService._request_model(OpenAI, AIConfig, api_key, request_base, model, is_plan_key, prompt, timeout, httpx)
            parsed_result = json.loads(AIService._extract_json_text(result))
            if not isinstance(parsed_result, dict):
                return {}, f'{error_prefix}格式错误'
            md = parsed_result.get(markdown_key) or parsed_result.get(markdown_key.replace('_', ''))
            if not md or not isinstance(md, str):
                return {}, f'{error_prefix}缺少 {markdown_key}'
            parsed_result[markdown_key] = normalizer(md, req_data)
            return parsed_result, ''
        except json.JSONDecodeError:
            return {}, f'{error_prefix}不是合法 JSON'
        except Exception as e:
            current_app.logger.error(f'{error_prefix}失败: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return {}, f'{error_prefix}失败: {str(e)}'

    @staticmethod
    def _normalize_skill_markdown(skill_md, req_data):
        return AIService._normalize_markdown(skill_md, req_data, 'generated-skill')

    @staticmethod
    def _normalize_rule_markdown(rule_md, req_data):
        return AIService._normalize_markdown(rule_md, req_data, 'generated-rule')

    @staticmethod
    def _normalize_markdown(markdown, req_data, fallback_name):
        content = markdown.strip()
        content = re.sub(r'^```(?:markdown|md)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content).strip()
        if content.startswith('---'):
            return content
        raw_name = str(req_data.get('name') or fallback_name).strip()
        frontmatter_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', raw_name.lower()).strip('-') or fallback_name
        description = str(req_data.get('description') or raw_name).strip()
        return f'---\nname: {frontmatter_name}\ndescription: {description}\n---\n\n{content}'

    @staticmethod
    def get_default_case_generation_trigger_condition():
        return '当用户基于 PRD、需求文档、用户故事、功能说明、接口说明、UI 交互说明或业务规则生成、补充、优化、评审测试用例时触发。'

    @staticmethod
    def get_default_case_generation_output_spec():
        return '''输出必须兼容当前 AI 生成用例入库结构：最终只输出 JSON 对象，不输出 Markdown、解释文本或代码块。JSON 对象结构为 {"cases": [{"title": "用例名称/测试点名称", "module_name": "父模块/子模块/叶子模块", "precondition": "前置条件", "steps": "步骤1\\n步骤2", "expected_result": "预期结果1\\n预期结果2", "priority": 2, "case_type": 1, "tags": ["AI生成"]}]}。每条用例 title 需要细化到具体场景，steps 和 expected_result 每一行带数字编号，信息不足时标记“待确认”，不能编造需求。'''

    @staticmethod
    def _load_skill_creator_content():
        skill_path = Path(__file__).resolve().parents[3] / 'config' / 'skills' / 'skill-creator' / 'SKILL.md'
        if not skill_path.exists():
            raise FileNotFoundError(f'Skill创建规则不存在: {skill_path}')
        return skill_path.read_text(encoding='utf-8')

    @staticmethod
    def _load_skill_content():
        skill_path = Path(__file__).resolve().parents[3] / 'config' / 'skills' / 'test-case-generator' / 'SKILL.md'
        if not skill_path.exists():
            raise FileNotFoundError(f'测试用例生成技能不存在: {skill_path}')
        return skill_path.read_text(encoding='utf-8')

    @staticmethod
    def _build_skill_create_prompt(req_data):
        skill_creator_content = AIService._load_skill_creator_content()
        default_trigger_condition = AIService.get_default_case_generation_trigger_condition()
        default_output_spec = AIService.get_default_case_generation_output_spec()
        return f'''
你现在要严格按照下面 skill-creator 的 SKILL.md 规范，为测试平台创建一个新的 Skill 文件。

<skill-creator-skill-md>
{skill_creator_content}
</skill-creator-skill-md>

<new-skill-input>
Skill 名称：{req_data.get('name') or ''}
用户补充描述：{req_data.get('description') or ''}
标签：{req_data.get('tags') or []}
Skill 类型枚举值：{req_data.get('skillType') or req_data.get('skill_type') or 1}
风险等级枚举值：{req_data.get('riskLevel') or req_data.get('risk_level') or 2}
</new-skill-input>

<platform-contract>
这个 Skill 的目标是增强当前平台“AI 根据 PRD/需求生成测试用例”的能力。
触发条件固定理解为：{default_trigger_condition}
输出规范固定理解为：{default_output_spec}
</platform-contract>

请只输出 JSON 对象：
{{
  "description": "适合列表展示的 Skill 简介，80字以内",
  "reasoning_path": "面向测试用例生成的推理路径摘要，简洁步骤描述",
  "tags": ["标签1", "标签2"],
  "skill_type": 1,
  "risk_level": 2,
  "skill_md": "完整的 SKILL.md 文件内容，包含 YAML frontmatter 和 Markdown body"
}}

约束：skill_md 必须包含 YAML frontmatter，至少包含 name 和 description；body 必须是面向测试用例生成的 Markdown 指令；不要复制 skill-creator 原文；不要输出代码块或额外说明。
'''.strip()

    @staticmethod
    def _build_business_rule_create_prompt(req_data):
        input_rule_content = req_data.get('ruleContent') or req_data.get('rule_content') or req_data.get('description') or ''
        return f'''
请为测试平台创建一条“业务规则”知识资产，用于增强 AI 根据 PRD/需求生成测试用例时对确定性业务约束、校验条件、状态流转、边界条件和异常处理的理解。

<business-rule-input>
规则名称：{req_data.get('name') or ''}
用户输入的规则原文：{input_rule_content}
用户补充描述：{req_data.get('description') or ''}
标签：{req_data.get('tags') or []}
优先级枚举值：{req_data.get('priority') or 2}
</business-rule-input>

硬性约束：
1. 不要随机生成、替换或改变“用户输入的规则原文”的业务含义。
2. 返回 JSON 中的 rule_content 必须逐字等于“用户输入的规则原文”。
3. 你只能基于用户输入补充 applicable_scene、example、tags、priority，并生成用于测试用例生成的 RULE.md。
4. RULE.md 的“## Rule”章节必须逐字包含“用户输入的规则原文”，不能改写成另一条规则。

请只输出 JSON 对象：
{{
  "rule_content": "逐字返回用户输入的规则原文",
  "applicable_scene": "该规则适用的业务场景",
  "example": "输入/场景/预期的示例",
  "tags": ["标签1", "标签2"],
  "priority": 2,
  "rule_md": "完整的 RULE.md 文件内容，包含 YAML frontmatter 和 Markdown body"
}}

RULE.md 要求：必须包含 YAML frontmatter，至少包含 name 和 description；body 建议包含规则说明、适用场景、测试关注点、正反例、生成用例时的约束；内容必须面向测试用例生成；priority 只能是 0、1、2、3；tags 最多 8 个；不要输出代码块或额外说明。
'''.strip()

    @staticmethod
    def _split_document_content(document_content, max_chars=8000):
        content = (document_content or '').strip()
        if not content:
            return []
        sections = AIService._split_by_headings(content)
        chunks = []
        current_parts = []
        current_len = 0
        current_title = '文档内容'
        for section in sections:
            section_text = section['content'].strip()
            if not section_text:
                continue
            if len(section_text) > max_chars:
                if current_parts:
                    chunks.append({'title': current_title, 'content': '\n\n'.join(current_parts)})
                    current_parts = []
                    current_len = 0
                chunks.extend(AIService._split_large_section(section['title'], section_text, max_chars))
                continue
            if current_parts and current_len + len(section_text) > max_chars:
                chunks.append({'title': current_title, 'content': '\n\n'.join(current_parts)})
                current_parts = []
                current_len = 0
            if not current_parts:
                current_title = section['title']
            current_parts.append(section_text)
            current_len += len(section_text)
        if current_parts:
            chunks.append({'title': current_title, 'content': '\n\n'.join(current_parts)})
        return chunks or [{'title': '文档内容', 'content': content}]

    @staticmethod
    def _split_by_headings(content):
        heading_pattern = re.compile(r'(?m)^(#{1,6}\s+.+|第[一二三四五六七八九十百千万\d]+[章节部分篇].*|\d+(?:\.\d+)*[、.．]\s*.+)$')
        matches = list(heading_pattern.finditer(content))
        if not matches:
            return [{'title': '文档内容', 'content': content}]
        sections = []
        if matches[0].start() > 0:
            sections.append({'title': '文档开头', 'content': content[:matches[0].start()].strip()})
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            title = match.group(0).strip().lstrip('#').strip()
            sections.append({'title': title[:80] or '文档内容', 'content': content[start:end].strip()})
        return sections

    @staticmethod
    def _split_large_section(title, section_text, max_chars):
        paragraphs = re.split(r'\n\s*\n', section_text)
        chunks = []
        current_parts = []
        current_len = 0
        part_index = 1
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            while len(paragraph) > max_chars:
                if current_parts:
                    chunks.append({'title': f'{title}（第{part_index}部分）', 'content': '\n\n'.join(current_parts)})
                    part_index += 1
                    current_parts = []
                    current_len = 0
                chunks.append({'title': f'{title}（第{part_index}部分）', 'content': paragraph[:max_chars]})
                part_index += 1
                paragraph = paragraph[max_chars:]
            if current_parts and current_len + len(paragraph) > max_chars:
                chunks.append({'title': f'{title}（第{part_index}部分）', 'content': '\n\n'.join(current_parts)})
                part_index += 1
                current_parts = []
                current_len = 0
            current_parts.append(paragraph)
            current_len += len(paragraph)
        if current_parts:
            chunks.append({'title': f'{title}（第{part_index}部分）', 'content': '\n\n'.join(current_parts)})
        return chunks

    @staticmethod
    def _deduplicate_cases(cases):
        seen = {}
        deduplicated = []
        for case in cases:
            key = f"{case.get('module_name', '')}::{case.get('title', '')}".strip().lower()
            if not key or key in seen:
                continue
            seen[key] = True
            deduplicated.append(case)
        return deduplicated

    @staticmethod
    def _normalize_cases(parsed_result, template=None, chunk_title=''):
        template = template or {}
        raw_cases = AIService._collect_case_items(parsed_result)
        normalized = []
        for index, item in enumerate(raw_cases, 1):
            if not isinstance(item, dict):
                continue
            tags = item.get('tags') or item.get('标签') or template.get('tags', ['AI生成'])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in re.split(r'[,，]', tags) if tag.strip()]
            normalized.append({
                'selected': item.get('selected', True),
                'module_name': AIService._normalize_module_name(item.get('module_name') or item.get('所属模块') or item.get('module') or '未分类'),
                'title': item.get('title') or item.get('用例名称') or item.get('case_name') or item.get('name') or f'AI生成用例{index}',
                'precondition': item.get('precondition') or item.get('前置条件') or '',
                'steps': AIService._number_lines(item.get('steps') or item.get('步骤描述') or item.get('操作步骤') or ''),
                'expected_result': AIService._number_lines(item.get('expected_result') or item.get('expected_results') or item.get('预期结果') or item.get('期望结果') or ''),
                'priority': AIService._normalize_priority(item.get('priority') or item.get('用例等级'), template.get('priority', 2)),
                'case_type': AIService._normalize_case_type(item.get('case_type') or item.get('类型') or item.get('标签'), template.get('case_type', 1)),
                'tags': tags or ['AI生成']
            })
        return normalized

    @staticmethod
    def _collect_case_items(value):
        if isinstance(value, list):
            items = []
            for item in value:
                items.extend(AIService._collect_case_items(item))
            return items
        if not isinstance(value, dict):
            return []
        case_keys = {'title', '用例名称', 'case_name', 'name', 'steps', '步骤描述', '操作步骤', 'expected_result', '预期结果', '期望结果'}
        if any(key in value for key in case_keys):
            return [value]
        items = []
        for nested_value in value.values():
            items.extend(AIService._collect_case_items(nested_value))
        return items

    @staticmethod
    def _normalize_module_name(module_name):
        parts = [part.strip() for part in re.split(r'[/\\>＞｜|]', str(module_name or '')) if part.strip()]
        return '/'.join(parts[:3]) if parts else '未分类'

    @staticmethod
    def _number_lines(value):
        if isinstance(value, list):
            lines = [str(item).strip() for item in value if str(item).strip()]
        else:
            lines = [line.strip() for line in re.split(r'\n+', str(value or '')) if line.strip()]
        normalized = []
        for index, line in enumerate(lines, 1):
            cleaned_line = re.sub(r'^(?:步骤|预期结果)?\s*\d+\s*[.、．]\s*', '', line).strip()
            normalized.append(f'{index}. {cleaned_line}')
        return '\n'.join(normalized)

    @staticmethod
    def _normalize_priority(value, default=2):
        if isinstance(value, int):
            return value
        return {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 3, 'P5': 3}.get(str(value).upper(), default)

    @staticmethod
    def _normalize_case_type(value, default=1):
        if isinstance(value, int):
            return value
        text = str(value or '')
        if '性能' in text:
            return 2
        if '安全' in text:
            return 3
        if '接口' in text or 'API' in text.upper():
            return 4
        return default

    @staticmethod
    def _build_generation_context(template):
        template = template or {}
        skill_contexts = template.get('skill_contexts') or []
        rule_contexts = template.get('rule_contexts') or []
        if not skill_contexts and not rule_contexts:
            return ''
        parts = ['<selected-generation-context>']
        if skill_contexts:
            parts.append('请在生成测试用例时结合以下用户指定 Skill：')
            for item in skill_contexts:
                parts.append(f'''<selected-skill id="{item.get('id')}" name="{item.get('name')}">
{item.get('content') or ''}
</selected-skill>''')
        if rule_contexts:
            parts.append('请在生成测试用例时严格覆盖以下用户指定业务规则：')
            for item in rule_contexts:
                parts.append(f'''<selected-rule id="{item.get('id')}" name="{item.get('name')}">
{item.get('content') or ''}
</selected-rule>''')
        parts.append('</selected-generation-context>')
        return '\n\n'.join(parts)

    @staticmethod
    def _build_prompt(document_content, template=None, skill_content='', chunk_index=1, total_chunks=1, chunk_title='文档内容'): 
        template = template or {'priority': 2, 'case_type': 1, 'tags': ['AI生成']}
        generation_context = AIService._build_generation_context(template)
        return f'''
请使用下面的 test-case-generator skill 对需求文档分段进行深度测试用例设计。最终只输出 JSON。

<test-case-generator-skill>
{skill_content}
</test-case-generator-skill>

{generation_context}

<document-chunk-info>
当前分段：{chunk_index}/{total_chunks}
分段标题：{chunk_title}
</document-chunk-info>

<requirement-document-chunk>
{document_content}
</requirement-document-chunk>

平台入库配置：
- 默认优先级(priority): {template['priority']}
- 默认用例类型(case_type): {template['case_type']}
- 默认标签(tags): {template['tags']}

输出 JSON 结构：
{{"cases":[{{"title":"用例名称/测试点名称","module_name":"父模块/子模块/叶子模块","precondition":"前置条件","steps":"步骤1\\n步骤2","expected_result":"预期结果1\\n预期结果2","priority":2,"case_type":1,"tags":["AI生成"]}}]}}
'''.strip()

    @staticmethod
    def parse_pdf_and_generate_cases(pdf_path, template=None):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            content = ''
            for page in reader.pages:
                page_content = page.extract_text()
                if page_content:
                    content += page_content + '\n'
            if not content.strip():
                return [], 'PDF文件内容为空'
            return AIService.generate_test_cases(content, template)
        except Exception as e:
            current_app.logger.error(f'解析PDF并生成用例失败: {str(e)}')
            return [], f'解析PDF失败: {str(e)}'
