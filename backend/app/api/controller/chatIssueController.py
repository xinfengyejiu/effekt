# encoding: UTF-8
from flask import g, has_app_context

from .baseCrudController import BaseCrudController
from ..service.chatIssueService import ChatIssueService


def _current_user_id():
    if not has_app_context():
        return None
    return getattr(g, 'current_user_id', None)


class ChatIssueController(BaseCrudController):
    def import_text(self):
        return ChatIssueService.import_text(
            self.session, self.req_data, _current_user_id()
        )

    def import_list(self):
        return ChatIssueService.list_imports(self.session, self.req_data)

    def import_detail(self):
        import_id = self._get(self.req_data, 'importId', 'import_id', 'sessionId', 'id')
        if not import_id:
            return {}, 'importId 为必传参数'
        return ChatIssueService.detail(self.session, import_id)

    def item_update(self):
        return ChatIssueService.update_item(
            self.session, self.req_data, _current_user_id()
        )

    def item_delete(self):
        return ChatIssueService.delete_item(
            self.session, self.req_data, _current_user_id()
        )

    def analyze(self):
        return ChatIssueService.analyze(
            self.session, self.req_data, _current_user_id()
        )

    def dismiss(self):
        return ChatIssueService.dismiss(
            self.session, self.req_data, _current_user_id()
        )

    def confirm_to_bug(self):
        return ChatIssueService.confirm_to_bug(
            self.session, self.req_data, _current_user_id()
        )

    def to_case(self):
        return ChatIssueService.to_case(
            self.session, self.req_data, _current_user_id()
        )
