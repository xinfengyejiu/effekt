# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.skillFlowService import SkillFlowService


class AiFlowController(BaseCrudController):
    def flow_create(self):
        return SkillFlowService.create_flow(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def flow_update(self):
        return SkillFlowService.update_flow(self.session, self.req_data)

    def flow_delete(self):
        return SkillFlowService.delete_flow(self.session, self.req_data)

    def flow_detail(self):
        flow_id = self._get(self.req_data, 'flowId', 'id')
        if not flow_id:
            return {}, 'flowId 为必传参数'
        return SkillFlowService.flow_detail(self.session, flow_id)

    def flow_list(self):
        return SkillFlowService.flow_list(self.session, self.req_data)

    def flow_execute(self):
        return SkillFlowService.execute_flow(self.session, self.req_data)

    def execution_list(self):
        return SkillFlowService.execution_list(self.session, self.req_data)

    def execution_detail(self):
        execution_id = self._get(self.req_data, 'executionId', 'id')
        if not execution_id:
            return {}, 'executionId 为必传参数'
        return SkillFlowService.execution_detail(self.session, execution_id)
