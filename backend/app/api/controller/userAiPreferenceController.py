# encoding: UTF-8
from flask import g, has_app_context

from .baseCrudController import BaseCrudController
from ..service.userAiPreferenceService import UserAiPreferenceService


def _current_user_id():
    if not has_app_context():
        return None
    return getattr(g, 'current_user_id', None)


class UserAiPreferenceController(BaseCrudController):
    def model_options(self):
        return UserAiPreferenceService.list_model_options()

    def preference_detail(self):
        user_id = _current_user_id() or self._get(self.req_data, 'userId', 'user_id')
        return UserAiPreferenceService.get_preference(self.session, user_id)

    def preference_save(self):
        user_id = _current_user_id() or self._get(self.req_data, 'userId', 'user_id')
        return UserAiPreferenceService.save_preference(self.session, user_id, self.req_data)

    def preference_clear(self):
        user_id = _current_user_id() or self._get(self.req_data, 'userId', 'user_id')
        return UserAiPreferenceService.clear_preference(self.session, user_id)

    def fetch_models(self):
        user_id = _current_user_id() or self._get(self.req_data, 'userId', 'user_id')
        return UserAiPreferenceService.fetch_remote_models(self.session, user_id, self.req_data)
