# encoding: UTF-8
"""契约漂移 Webhook 通知。"""
import logging
import requests

logger = logging.getLogger(__name__)


class ContractNotifyService(object):

    @staticmethod
    def send_breaking_summary(notify_type, webhook_url, payload):
        if not webhook_url:
            return False, 'webhook 未配置'
        channels = [c.strip() for c in (notify_type or 'feishu').split(',') if c.strip()]
        if not channels:
            channels = ['feishu']

        title = payload.get('suite_name') or '契约套件'
        run_no = payload.get('run_no') or ''
        breaking = payload.get('breaking_count') or 0
        drift = payload.get('drift_count') or 0
        errors = payload.get('error_count') or 0
        top = payload.get('top_findings') or []
        lines = [
            '【契约漂移告警】{}'.format(title),
            '执行号: {}'.format(run_no),
            'breaking: {} | drift接口: {} | error: {}'.format(breaking, drift, errors),
        ]
        for idx, item in enumerate(top[:3], 1):
            lines.append('{}. [{}] {} — {}'.format(
                idx, item.get('severity'), item.get('json_path'), item.get('message')
            ))
        text = '\n'.join(lines)

        ok = True
        for channel in channels:
            try:
                if channel == 'wechat_work':
                    requests.post(webhook_url, json={'msgtype': 'text', 'text': {'content': text}}, timeout=10)
                elif channel == 'dingtalk':
                    requests.post(webhook_url, json={'msgtype': 'text', 'text': {'content': text}}, timeout=10)
                else:
                    # feishu default
                    requests.post(webhook_url, json={
                        'msg_type': 'text',
                        'content': {'text': text},
                    }, timeout=10)
            except Exception as e:
                logger.error('契约通知失败 [%s]: %s', channel, str(e))
                ok = False
        return ok, '' if ok else '通知发送失败'
