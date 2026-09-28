# encoding: UTF-8
from flask import g, request

from .baseCrudController import BaseCrudController
from ..service.exploreSessionService import ExploreSessionService


class ExploreSessionController(BaseCrudController):
    def session_create(self):
        return ExploreSessionService.create_session(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def session_list(self):
        return ExploreSessionService.list_sessions(self.session, self.req_data)

    def session_detail(self):
        session_id = self._get(self.req_data, 'sessionId', 'session_id', 'id')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        return ExploreSessionService.detail(self.session, session_id)

    def session_update(self):
        return ExploreSessionService.update_session(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def session_start(self):
        session_id = self._get(self.req_data, 'sessionId', 'session_id', 'id')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        return ExploreSessionService.start_session(
            self.session, session_id, getattr(g, 'current_user_id', None)
        )

    def session_end(self):
        return ExploreSessionService.end_session(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def session_archive(self):
        session_id = self._get(self.req_data, 'sessionId', 'session_id', 'id')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        return ExploreSessionService.archive_session(
            self.session, session_id, getattr(g, 'current_user_id', None)
        )

    def entry_add(self):
        return ExploreSessionService.add_entry(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def entry_update(self):
        return ExploreSessionService.update_entry(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def entry_delete(self):
        return ExploreSessionService.delete_entry(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def upload(self, flask_request=None):
        return ExploreSessionService.upload_screenshot(
            self.session,
            flask_request if flask_request is not None else request,
            getattr(g, 'current_user_id', None),
        )

    def to_bug(self):
        return ExploreSessionService.to_bug(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def to_case_draft(self):
        return ExploreSessionService.to_case_draft(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )
