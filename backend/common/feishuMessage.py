import os
import requests
import json


class FeiShuMessage:

    def __init__(self):
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.webhook = os.environ.get('FEISHU_WEBHOOK_URL', '')

    def send_message(self, msg, url=None):
        url = url if url else self.webhook
        if not url:
            return False
        res = requests.post(url, headers=self.headers, json=msg, verify=False)
        if res.status_code == 200:
            return True
        else:
            return False

    def is_valid_key_url(self, f_url):
        test_msg_body = {"msg_type": "text", "content": {"text": ""}}
        res = requests.post(f_url, headers=self.headers, json=test_msg_body, verify=False)
        if res.status_code == 200:
            code = json.loads(res.text)['code']
            if code == 19024:
                return True, ''
            else:
                return False, '不是有效的飞书关键字链接，请检查!'
        else:
            return False, '网络异常请稍后重试'


if __name__ == '__main__':
    test = FeiShuMessage()
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    if webhook_url:
        msg = {"msg_type": "text", "content": {"text": "测试消息"}}
        print(test.is_valid_key_url(webhook_url))
    else:
        print('请设置环境变量 FEISHU_WEBHOOK_URL')
