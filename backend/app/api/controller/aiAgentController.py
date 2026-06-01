# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.agentRegistryService import AgentRegistryService


class AiAgentController(BaseCrudController):
    def agent_create(self):
        return AgentRegistryService.create_agent(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def agent_update(self):
        return AgentRegistryService.update_agent(self.session, self.req_data)

    def agent_delete(self):
        return AgentRegistryService.delete_agent(self.session, self.req_data)

    def agent_detail(self):
        agent_id = self._get(self.req_data, 'agentId', 'id')
        if not agent_id:
            return {}, 'agentId 为必传参数'
        return AgentRegistryService.agent_detail(self.session, agent_id)

    def agent_list(self):
        return AgentRegistryService.agent_list(self.session, self.req_data)

    def agent_execute(self):
        return AgentRegistryService.execute_agent(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def agent_test(self):
        return AgentRegistryService.execute_agent(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def execution_list(self):
        return AgentRegistryService.execution_list(self.session, self.req_data)

    def execution_detail(self):
        execution_id = self._get(self.req_data, 'executionId', 'id')
        if not execution_id:
            return {}, 'executionId 为必传参数'
        return AgentRegistryService.execution_detail(self.session, execution_id)
