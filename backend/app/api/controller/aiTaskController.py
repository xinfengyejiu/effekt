# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.aiOrchestratorService import AiOrchestratorService


class AiTaskController(BaseCrudController):
    def task_create(self):
        return AiOrchestratorService.create_task(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def task_list(self):
        return AiOrchestratorService.task_list(self.session, self.req_data)

    def task_detail(self):
        task_id = self._get(self.req_data, 'taskId', 'id')
        if not task_id:
            return {}, 'taskId 为必传参数'
        return AiOrchestratorService.task_detail(self.session, task_id)

    def task_execute(self):
        return AiOrchestratorService.execute_task(self.session, self.req_data)

    def task_cancel(self):
        return AiOrchestratorService.cancel_task(self.session, self.req_data)
