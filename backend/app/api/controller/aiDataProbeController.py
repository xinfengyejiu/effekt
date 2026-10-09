# encoding: UTF-8
from flask import g, has_app_context

from .baseCrudController import BaseCrudController
from ..service.aiDataProbeService import AiDataProbeService


def _current_user_id():
    if not has_app_context():
        return None
    return getattr(g, 'current_user_id', None)


class AiDataProbeController(BaseCrudController):
    def connection_list(self):
        return AiDataProbeService.list_connections(self.session, self.req_data)

    def connection_create(self):
        return AiDataProbeService.create_connection(self.session, self.req_data, _current_user_id())

    def connection_update(self):
        return AiDataProbeService.update_connection(self.session, self.req_data, _current_user_id())

    def connection_delete(self):
        return AiDataProbeService.delete_connection(self.session, self.req_data, _current_user_id())

    def connection_test(self):
        return AiDataProbeService.test_connection(self.session, self.req_data, _current_user_id())

    def connection_tables(self):
        return AiDataProbeService.list_tables(self.session, self.req_data, _current_user_id())

    def connection_table_columns(self):
        return AiDataProbeService.table_columns(self.session, self.req_data, _current_user_id())

    def connection_import(self):
        return AiDataProbeService.import_from_project(self.session, self.req_data, _current_user_id())

    def session_list(self):
        return AiDataProbeService.list_sessions(self.session, self.req_data)

    def session_create(self):
        return AiDataProbeService.create_session(self.session, self.req_data, _current_user_id())

    def session_detail(self):
        return AiDataProbeService.session_detail(self.session, self.req_data)

    def session_rename(self):
        return AiDataProbeService.rename_session(self.session, self.req_data, _current_user_id())

    def ask(self):
        return AiDataProbeService.ask(self.session, self.req_data, _current_user_id())

    def ask_stream(self):
        return AiDataProbeService.ask_stream(self.session, self.req_data, _current_user_id())

    def rerun_sql(self):
        return AiDataProbeService.rerun_sql(self.session, self.req_data, _current_user_id())
