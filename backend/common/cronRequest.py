# -*- coding: utf-8 -*-
from const import STRESS_URI, QE_DOMAIN

from common.getRequest import Request


class CronRequest(object):
    def __init__(self, token):
        self.stress_api = STRESS_URI
        self.headers = {'accesstoken': token, 'Accept': '*/*', 'content-type': 'application/json;charset=UTF-8'}
        self.qe_domain = QE_DOMAIN

    def create(self, params):
        url = self.stress_api + '/back-end/stress/schedule/save'
        ret = Request.go('post', url, params, self.headers)
        if not ret:
            return
        return ret.get('id')

    def pause(self, jid):
        url = self.stress_api + '/back-end/stress/schedule/pause'
        params = [jid]
        Request.go('post', url, params, self.headers)

    def resume(self, jid):
        url = self.stress_api + '/back-end/stress/schedule/resume'
        params = [jid]
        Request.go('post', url, params, self.headers)

    def remove(self, jid):
        url = self.stress_api + '/back-end/stress/schedule/delete'
        params = [jid]
        Request.go('post', url, params, self.headers)

    def update(self, req_params):
        url = self.stress_api + '/back-end/stress/schedule/update'
        Request.go('post', url, req_params, self.headers)

    def test(self, req_params):
        url = self.stress_api + '/aida/keyword/run'
        print(url)
        b = Request.go('post', url, req_params, self.headers)
        print(b)

    def scrapy(self):
        url = self.stress_api + '/data/detail/scrapy'
        req_params = {"team": "USER", "fileName": "", "username": "", "password": ""}
        b = Request.go('post', url, req_params, self.headers)
        print(b)

    def detail(self):
        url = self.stress_api + '/detail/list'
        req_params = {"team": "USER", "fileName": "", "username": "", "password": ""}
        b = Request.go('get', url, req_params, self.headers)
        print(b)


if __name__ == '__main__':
    print('请配置环境变量 STRESS_URI 和 QE_DOMAIN 后使用')
