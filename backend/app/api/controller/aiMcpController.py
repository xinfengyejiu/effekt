# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.mcpConnectorService import McpConnectorService


class AiMcpController(BaseCrudController):
    def mcp_create(self):
        return McpConnectorService.create_connector(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def mcp_update(self):
        return McpConnectorService.update_connector(self.session, self.req_data)

    def mcp_delete(self):
        return McpConnectorService.delete_connector(self.session, self.req_data)

    def mcp_detail(self):
        connector_id = self._get(self.req_data, 'connectorId', 'id')
        if not connector_id:
            return {}, 'connectorId 为必传参数'
        return McpConnectorService.connector_detail(self.session, connector_id)

    def mcp_list(self):
        return McpConnectorService.connector_list(self.session, self.req_data)

    def mcp_test(self):
        return McpConnectorService.test_connector(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def mcp_call(self):
        return McpConnectorService.test_connector(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def call_log_list(self):
        return McpConnectorService.call_log_list(self.session, self.req_data)

    def call_log_detail(self):
        log_id = self._get(self.req_data, 'logId', 'callLogId', 'id')
        if not log_id:
            return {}, 'logId 为必传参数'
        return McpConnectorService.call_log_detail(self.session, log_id)
