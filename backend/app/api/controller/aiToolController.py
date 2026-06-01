# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.toolRegistryService import ToolRegistryService


class AiToolController(BaseCrudController):
    def tool_create(self):
        return ToolRegistryService.create_tool(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def tool_update(self):
        return ToolRegistryService.update_tool(self.session, self.req_data)

    def tool_delete(self):
        return ToolRegistryService.delete_tool(self.session, self.req_data)

    def tool_detail(self):
        tool_id = self._get(self.req_data, 'toolId', 'id')
        if not tool_id:
            return {}, 'toolId 为必传参数'
        return ToolRegistryService.tool_detail(self.session, tool_id)

    def tool_list(self):
        return ToolRegistryService.tool_list(self.session, self.req_data)

    def tool_execute(self):
        return ToolRegistryService.execute_tool(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def tool_test(self):
        return ToolRegistryService.execute_tool(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def execution_list(self):
        return ToolRegistryService.execution_list(self.session, self.req_data)

    def execution_detail(self):
        execution_id = self._get(self.req_data, 'executionId', 'id')
        if not execution_id:
            return {}, 'executionId 为必传参数'
        return ToolRegistryService.execution_detail(self.session, execution_id)
