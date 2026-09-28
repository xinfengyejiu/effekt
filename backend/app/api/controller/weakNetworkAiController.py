# encoding: UTF-8
from flask import g, has_app_context

from .baseCrudController import BaseCrudController
from ..service.weakNetworkAiService import WeakNetworkAiService


def _current_user_id():
    if not has_app_context():
        return None
    return getattr(g, 'current_user_id', None)


class WeakNetworkAiController(BaseCrudController):
    def list_tasks(self):
        return WeakNetworkAiService.list_tasks(self.session, self.req_data)

    def create_task(self):
        return WeakNetworkAiService.create_task(self.session, self.req_data, _current_user_id())

    def detail(self):
        task_id = self._get(self.req_data, 'taskId', 'task_id', 'id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        return WeakNetworkAiService.detail(self.session, task_id)

    def update_task(self):
        return WeakNetworkAiService.update_task(self.session, self.req_data, _current_user_id())

    def orchestrate(self):
        return WeakNetworkAiService.orchestrate(self.session, self.req_data, _current_user_id())

    def confirm(self):
        return WeakNetworkAiService.confirm(self.session, self.req_data, _current_user_id())

    def add_evidence(self, upload_bytes=None, filename=None):
        return WeakNetworkAiService.add_evidence(
            self.session, self.req_data, _current_user_id(),
            upload_file=upload_bytes, filename=filename,
        )

    def judge(self):
        return WeakNetworkAiService.judge(self.session, self.req_data, _current_user_id())

    def dismiss(self):
        return WeakNetworkAiService.dismiss_findings(self.session, self.req_data, _current_user_id())

    def confirm_to_bug(self):
        return WeakNetworkAiService.confirm_to_bug(self.session, self.req_data, _current_user_id())
