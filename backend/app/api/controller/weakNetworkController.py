# encoding: UTF-8
from flask import g, has_app_context

from .baseCrudController import BaseCrudController
from ..service.weakNetworkService import WeakNetworkService


def _current_user_id():
    if not has_app_context():
        return None
    return getattr(g, 'current_user_id', None)


class WeakNetworkController(BaseCrudController):
    def profile_list(self):
        return WeakNetworkService.list_profiles(self.session, self.req_data)

    def profile_create(self):
        return WeakNetworkService.create_profile(self.session, self.req_data, _current_user_id())

    def profile_update(self):
        return WeakNetworkService.update_profile(self.session, self.req_data, _current_user_id())

    def profile_delete(self):
        return WeakNetworkService.delete_profile(self.session, self.req_data, _current_user_id())

    def session_create(self):
        return WeakNetworkService.create_session(self.session, self.req_data, _current_user_id())

    def session_list(self):
        return WeakNetworkService.list_sessions(self.session, self.req_data)

    def session_download(self, session_id):
        return WeakNetworkService.build_pack_bytes(self.session, session_id)
