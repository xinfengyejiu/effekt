# encoding: UTF-8
"""用户个人中心：AI 模型偏好（支持自定义供应商 / Key / URL）。"""
from __future__ import unicode_literals

from datetime import datetime

from config.ai_config import AIConfig
from logger import logger
from ..model.userAiPreferenceModel import UserAiPreference

PASSWORD_MASK = '******'

DEFAULT_MODEL_OPTIONS = [
    {'value': 'gpt-4o', 'label': 'GPT-4o'},
    {'value': 'gpt-4.1', 'label': 'GPT-4.1'},
    {'value': 'gpt-4.1-mini', 'label': 'GPT-4.1 Mini'},
    {'value': 'gpt-5.5', 'label': 'GPT-5.5'},
    {'value': 'claude-sonnet-4', 'label': 'Claude Sonnet 4'},
    {'value': 'claude-3-5-sonnet', 'label': 'Claude 3.5 Sonnet'},
    {'value': 'deepseek-chat', 'label': 'DeepSeek Chat'},
    {'value': 'doubao-pro', 'label': '豆包 Pro'},
]

PROVIDER_PRESETS = [
    {
        'value': 'platform',
        'label': '平台默认',
        'apiBase': '',
        'hint': '使用平台统一密钥与地址，仅自选模型名',
    },
    {
        'value': 'openai',
        'label': 'OpenAI',
        'apiBase': 'https://api.openai.com/v1',
        'hint': '官方 OpenAI',
    },
    {
        'value': 'custom',
        'label': '自定义 / 兼容 OpenAI',
        'apiBase': 'https://api.routin.ai/v1',
        'hint': 'Meteor / Routin / OneAPI / 自建网关等',
    },
    {
        'value': 'deepseek',
        'label': 'DeepSeek',
        'apiBase': 'https://api.deepseek.com/v1',
        'hint': 'DeepSeek OpenAI 兼容接口',
    },
]


class UserAiPreferenceService(object):

    @staticmethod
    def list_model_options():
        import os
        raw = (os.getenv('AI_MODEL_OPTIONS') or '').strip()
        options = []
        if raw:
            for item in raw.split(','):
                value = item.strip()
                if value:
                    options.append({'value': value, 'label': value})
        else:
            options = [dict(x) for x in DEFAULT_MODEL_OPTIONS]
        current = AIConfig.get_model()
        if current and not any(x.get('value') == current for x in options):
            options.insert(0, {'value': current, 'label': '{}（系统默认）'.format(current)})
        return {
            'list': options,
            'providers': [dict(x) for x in PROVIDER_PRESETS],
            'defaultModel': current or '',
            'provider': AIConfig.MODEL_PROVIDER or '',
            'apiBase': AIConfig.get_api_base() or '',
        }, ''

    @staticmethod
    def _get_row(session, user_id):
        return session.query(UserAiPreference).filter(
            UserAiPreference.user_id == int(user_id),
            UserAiPreference.is_delete == 0,
        ).first()

    @staticmethod
    def get_preference(session, user_id):
        if user_id in (None, ''):
            return {}, '未登录'
        row = UserAiPreferenceService._get_row(session, user_id)
        default_model = AIConfig.get_model() or ''
        data = {
            'userId': int(user_id),
            'provider': 'platform',
            'model': default_model,
            'apiBase': '',
            'apiKey': '',
            'hasApiKey': False,
            'useCustom': False,
            'temperature': None,
            'maxTokens': None,
            'usingDefault': True,
            'systemDefaultModel': default_model,
            'systemApiBase': AIConfig.get_api_base() or '',
        }
        if not row:
            return data, ''
        use_custom = int(getattr(row, 'use_custom', 0) or 0) == 1
        has_key = bool((getattr(row, 'api_key', None) or '').strip())
        model = (row.model or '').strip() or default_model
        provider = (row.provider or '').strip() or ('custom' if use_custom else 'platform')
        data.update({
            'provider': provider,
            'model': model,
            'apiBase': (getattr(row, 'api_base', None) or '').strip(),
            'apiKey': PASSWORD_MASK if has_key else '',
            'hasApiKey': has_key,
            'useCustom': use_custom,
            'temperature': float(row.temperature) if row.temperature is not None else None,
            'maxTokens': int(row.max_tokens) if row.max_tokens is not None else None,
            'usingDefault': (not use_custom) and (not model or model == default_model) and not has_key,
        })
        return data, ''

    @staticmethod
    def save_preference(session, user_id, req_data):
        if user_id in (None, ''):
            return {}, '未登录'
        model = (req_data.get('model') or '').strip()
        if not model:
            return {}, '请选择模型'
        if len(model) > 128:
            return {}, '模型名称过长'
        provider = (req_data.get('provider') or 'platform').strip()[:64]
        api_base = (req_data.get('apiBase') or req_data.get('api_base') or '').strip()[:512]
        api_key = req_data.get('apiKey') if 'apiKey' in req_data else req_data.get('api_key')
        use_custom_raw = req_data.get('useCustom')
        if use_custom_raw is None:
            use_custom_raw = req_data.get('use_custom')
        if use_custom_raw is None:
            use_custom = 1 if provider and provider != 'platform' else 0
        else:
            use_custom = 1 if use_custom_raw in (True, 1, '1', 'true', 'True') else 0
        if provider == 'platform':
            use_custom = 0
            api_base = ''
        if use_custom and not api_base:
            # 用预设补全
            for item in PROVIDER_PRESETS:
                if item['value'] == provider and item.get('apiBase'):
                    api_base = item['apiBase']
                    break
        if use_custom and not api_base:
            return {}, '自定义供应商需填写 API Base URL'

        temperature = req_data.get('temperature')
        max_tokens = req_data.get('maxTokens') or req_data.get('max_tokens')
        try:
            temperature_val = float(temperature) if temperature not in (None, '') else None
        except (TypeError, ValueError):
            return {}, 'temperature 无效'
        try:
            max_tokens_val = int(max_tokens) if max_tokens not in (None, '') else None
        except (TypeError, ValueError):
            return {}, 'maxTokens 无效'

        row = UserAiPreferenceService._get_row(session, user_id)
        values = {
            'user_id': int(user_id),
            'provider': provider,
            'model': model,
            'api_base': api_base if use_custom else '',
            'use_custom': use_custom,
            'temperature': temperature_val,
            'max_tokens': max_tokens_val,
            'is_delete': 0,
            'updated_time': datetime.now(),
        }
        # 密码：空或 ****** 表示不改
        if api_key not in (None, '', PASSWORD_MASK):
            values['api_key'] = str(api_key)[:512]
        elif not use_custom:
            values['api_key'] = ''
        elif row is None and use_custom:
            return {}, '自定义供应商请填写 API Key'

        if row:
            for key, val in values.items():
                setattr(row, key, val)
            if not use_custom:
                row.api_key = ''
                row.api_base = ''
        else:
            if 'api_key' not in values:
                values['api_key'] = ''
            row = UserAiPreference(**values)
            session.add(row)
        err = session.done(close=False)
        if err:
            logger.warning('save user_ai_preference failed: %s', err)
            return {}, '保存失败：{}'.format(err)
        return UserAiPreferenceService.get_preference(session, user_id)[0], ''

    @staticmethod
    def clear_preference(session, user_id):
        if user_id in (None, ''):
            return {}, '未登录'
        row = UserAiPreferenceService._get_row(session, user_id)
        if row:
            row.is_delete = 1
            row.updated_time = datetime.now()
            err = session.done(close=False)
            if err:
                return {}, '清除失败：{}'.format(err)
        return UserAiPreferenceService.get_preference(session, user_id)[0], ''

    @staticmethod
    def fetch_remote_models(session, user_id, req_data=None):
        """用用户填写的（或已保存的）Base+Key 调用 OpenAI 兼容 /models。"""
        req_data = req_data or {}
        api_base = (req_data.get('apiBase') or req_data.get('api_base') or '').strip()
        api_key = req_data.get('apiKey') if 'apiKey' in req_data else req_data.get('api_key')
        if api_key in (None, '', PASSWORD_MASK):
            api_key = ''
            if user_id not in (None, ''):
                row = UserAiPreferenceService._get_row(session, user_id)
                if row:
                    if not api_base:
                        api_base = (row.api_base or '').strip()
                    api_key = (row.api_key or '').strip()
        if not api_base:
            api_base = AIConfig.get_api_base() or ''
        if not api_key:
            api_key = AIConfig.get_api_key() or ''
        if not api_base:
            return {}, '请填写 API Base URL'
        if not api_key or api_key == '请替换为你的Meteor API Key':
            return {}, '请填写 API Key'

        try:
            import httpx
            from app.api.service.aiService import AIService
            base = AIService._normalize_api_base(api_base)
            url = base.rstrip('/') + '/models'
            timeout = httpx.Timeout(connect=15.0, read=30.0, write=30.0, pool=15.0)
            headers = {
                'Authorization': 'Bearer {}'.format(api_key),
                'Content-Type': 'application/json',
            }
            with httpx.Client(timeout=timeout, trust_env=False) as client:
                resp = client.get(url, headers=headers)
            if resp.status_code >= 400:
                return {}, '获取模型失败：HTTP {} {}'.format(resp.status_code, (resp.text or '')[:200])
            payload = resp.json() if resp.content else {}
            data = payload.get('data') if isinstance(payload, dict) else None
            ids = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('id'):
                        ids.append(str(item['id']))
                    elif isinstance(item, str):
                        ids.append(item)
            elif isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict) and item.get('id'):
                        ids.append(str(item['id']))
            ids = sorted(set(ids))
            options = [{'value': mid, 'label': mid} for mid in ids]
            return {'list': options, 'total': len(options)}, ''
        except Exception as exc:
            logger.warning('fetch_remote_models failed: %s', exc)
            return {}, '获取模型失败：{}'.format(exc)

    @staticmethod
    def to_model_setting(session, user_id):
        """供 AIService 合并：含明文 apiKey（仅服务端内部使用）。"""
        if user_id in (None, ''):
            return {}
        try:
            row = UserAiPreferenceService._get_row(session, user_id)
            if not row:
                return {}
            setting = {}
            model = (row.model or '').strip()
            if model:
                setting['model'] = model
            provider = (row.provider or '').strip()
            if provider and provider != 'platform':
                setting['provider'] = provider
            use_custom = int(getattr(row, 'use_custom', 0) or 0) == 1
            if use_custom:
                api_base = (getattr(row, 'api_base', None) or '').strip()
                api_key = (getattr(row, 'api_key', None) or '').strip()
                if api_base:
                    setting['apiBase'] = api_base
                if api_key:
                    setting['apiKey'] = api_key
            if row.temperature is not None:
                setting['temperature'] = float(row.temperature)
            if row.max_tokens is not None:
                setting['maxTokens'] = int(row.max_tokens)
            return setting
        except Exception as exc:
            logger.warning('load user model setting failed user_id=%s err=%s', user_id, exc)
            return {}
