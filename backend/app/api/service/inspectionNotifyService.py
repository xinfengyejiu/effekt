# encoding: UTF-8
"""巡检通知推送服务（企业微信/钉钉/飞书）。"""
import json
import logging
import requests

logger = logging.getLogger(__name__)


class InspectionNotifyService(object):

    @staticmethod
    def send_notification(notify_type, webhook_url, execution_data, notify_config=None):
        """
        发送巡检通知。
        Args:
            notify_type: str — 逗号分隔的渠道：wechat_work,dingtalk,feishu
            webhook_url: str — webhook 地址
            execution_data: dict — 执行记录数据
            notify_config: dict — 额外配置（@人、关键词等）
        """
        if not webhook_url:
            return False, 'webhook 未配置'

        channels = [c.strip() for c in (notify_type or '').split(',') if c.strip()]
        if not channels:
            return False, '未配置通知渠道'

        all_success = True
        for channel in channels:
            try:
                if channel == 'wechat_work':
                    InspectionNotifyService._send_wechat(webhook_url, execution_data, notify_config)
                elif channel == 'dingtalk':
                    InspectionNotifyService._send_dingtalk(webhook_url, execution_data, notify_config)
                elif channel == 'feishu':
                    InspectionNotifyService._send_feishu(webhook_url, execution_data, notify_config)
                else:
                    logger.warning('未知的通知渠道: %s', channel)
            except Exception as e:
                logger.error('通知发送失败 [%s]: %s', channel, str(e))
                all_success = False

        return all_success, '' if all_success else '部分渠道通知失败'

    @staticmethod
    def _build_message(execution_data, notify_config=None):
        """构建通知消息内容。"""
        task_name = execution_data.get('task_name', '未知任务')
        total = execution_data.get('total_count', 0)
        passed = execution_data.get('pass_count', 0)
        failed = execution_data.get('fail_count', 0)
        errors = execution_data.get('error_count', 0)
        duration = execution_data.get('duration_ms', 0)
        duration_sec = round(duration / 1000.0, 1)
        status = execution_data.get('status', 0)
        start_time = str(execution_data.get('start_time', ''))
        execution_id = execution_data.get('id', '')

        # 计算通过率
        rate = round(passed * 100.0 / total, 1) if total > 0 else 0

        # 状态图标
        if status == 2:
            status_icon = '✅'
            status_text = '全部通过'
        elif status == 3:
            status_icon = '⚠️'
            status_text = '部分失败'
        elif status == 4:
            status_icon = '❌'
            status_text = '全部失败'
        else:
            status_icon = '⚡'
            status_text = '异常'

        # 失败项摘要（含 AI 分析）
        fail_items = execution_data.get('fail_items', [])
        fail_text = ''
        if fail_items:
            fail_text = '\n\n失败项:\n'
            for i, item in enumerate(fail_items[:5], 1):
                fail_text += '  {}. [{}] {} — {}\n'.format(
                    i, item.get('item_type', ''), item.get('name', ''),
                    (item.get('error_message', '') or '')[:80]
                )
                ai_reason = (item.get('ai_reason') or '').strip()
                root_cause = (item.get('ai_root_cause') or '').strip()
                category = (item.get('ai_category') or '').strip()
                if ai_reason:
                    fail_text += '     AI判定: {}\n'.format(ai_reason[:100])
                if root_cause:
                    fail_text += '     根因[{}]: {}\n'.format(category or '未知', root_cause[:100])
                suggestions = item.get('ai_suggestions') or []
                if suggestions:
                    fail_text += '     建议: {}\n'.format(str(suggestions[0])[:80])
            if len(fail_items) > 5:
                fail_text += '  ... 等 {} 项\n'.format(len(fail_items))

        return {
            'task_name': task_name,
            'status_icon': status_icon,
            'status_text': status_text,
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'rate': rate,
            'duration_sec': duration_sec,
            'start_time': start_time,
            'execution_id': execution_id,
            'fail_text': fail_text,
        }

    @staticmethod
    def _send_wechat(webhook_url, execution_data, notify_config=None):
        """企业微信 webhook 通知。"""
        msg = InspectionNotifyService._build_message(execution_data, notify_config)
        content = (
            '{status_icon} **巡检报告 - {task_name}**\n'
            '━━━━━━━━━━━━━━━━━━\n'
            '> 结果: **{status_text}** {passed}/{total} 通过 (**{rate}%**)\n'
            '> 耗时: {duration_sec}s\n'
            '> 时间: {start_time}\n'
            '{fail_text}\n'
            '> [查看详情](#/inspection/executions)'
        ).format(**msg)

        payload = {
            'msgtype': 'markdown',
            'markdown': {'content': content},
        }
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise Exception('企微通知发送失败: HTTP {}'.format(resp.status_code))
        result = resp.json()
        if result.get('errcode') != 0:
            raise Exception('企微通知发送失败: {}'.format(result.get('errmsg', '')))

    @staticmethod
    def _send_dingtalk(webhook_url, execution_data, notify_config=None):
        """钉钉 webhook 通知。"""
        msg = InspectionNotifyService._build_message(execution_data, notify_config)
        content = (
            '{status_icon} **巡检报告 - {task_name}**\n\n'
            '> 结果: **{status_text}** {passed}/{total} 通过 (**{rate}%**)\n\n'
            '> 耗时: {duration_sec}s\n\n'
            '> 时间: {start_time}\n\n'
            '{fail_text}\n\n'
            '> [查看详情](#/inspection/executions)'
        ).format(**msg)

        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'title': '巡检报告 - {}'.format(msg['task_name']),
                'text': content,
            },
        }

        # 支持 @人
        if notify_config and notify_config.get('at_mobiles'):
            payload['at'] = {'atMobiles': notify_config['at_mobiles']}

        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise Exception('钉钉通知发送失败: HTTP {}'.format(resp.status_code))
        result = resp.json()
        if result.get('errcode') != 0:
            raise Exception('钉钉通知发送失败: {}'.format(result.get('errmsg', '')))

    @staticmethod
    def _send_feishu(webhook_url, execution_data, notify_config=None):
        """飞书 webhook 通知。"""
        msg = InspectionNotifyService._build_message(execution_data, notify_config)
        content = (
            '{status_icon} **巡检报告 - {task_name}**\n'
            '结果: **{status_text}** {passed}/{total} 通过 (**{rate}%**)\n'
            '耗时: {duration_sec}s\n'
            '时间: {start_time}'
            '{fail_text}'
        ).format(**msg)

        payload = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {'tag': 'plain_text', 'content': '巡检报告 - {}'.format(msg['task_name'])},
                    'template': 'green' if msg['rate'] >= 80 else ('orange' if msg['rate'] >= 50 else 'red'),
                },
                'elements': [
                    {
                        'tag': 'markdown',
                        'content': content,
                    },
                    {
                        'tag': 'action',
                        'actions': [
                            {
                                'tag': 'button',
                                'text': {'tag': 'plain_text', 'content': '查看详情'},
                                'url': '#/inspection/executions',
                                'type': 'primary',
                            }
                        ],
                    }
                ],
            },
        }

        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise Exception('飞书通知发送失败: HTTP {}'.format(resp.status_code))
        result = resp.json()
        if result.get('code') != 0 and result.get('StatusCode') != 0:
            raise Exception('飞书通知发送失败: {}'.format(result.get('msg', '')))
