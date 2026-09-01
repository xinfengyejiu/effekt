# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.aiWorkloadEstimateService import AiWorkloadEstimateService


class AiWorkloadEstimateController(BaseCrudController):
    def estimate_create(self):
        return AiWorkloadEstimateService.create_estimate(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def estimate_list(self):
        return AiWorkloadEstimateService.list_estimates(self.session, self.req_data)

    def estimate_detail(self):
        estimate_id = self._get(self.req_data, 'estimateId', 'estimate_id', 'id')
        if not estimate_id:
            return {}, 'estimateId 为必传参数'
        return AiWorkloadEstimateService.estimate_detail(self.session, estimate_id)

    def estimate_export(self):
        estimate_id = self._get(self.req_data, 'estimateId', 'estimate_id', 'id')
        if not estimate_id:
            return None, '', 'estimateId 为必传参数'
        return AiWorkloadEstimateService.export_estimate_excel(self.session, estimate_id)

    def estimate_execute(self):
        estimate_id = self._get(self.req_data, 'estimateId', 'estimate_id', 'id')
        if not estimate_id:
            return {}, 'estimateId 为必传参数'
        return AiWorkloadEstimateService.execute_estimate(
            self.session, estimate_id, getattr(g, 'current_user_id', None)
        )

    def estimate_assign(self):
        return AiWorkloadEstimateService.assign_owner(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def estimate_delete(self):
        return AiWorkloadEstimateService.delete_estimate(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def actual_save(self):
        return AiWorkloadEstimateService.save_actual_data(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def estimate_confirm(self):
        return AiWorkloadEstimateService.confirm_estimate(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def estimate_retry(self):
        estimate_id = self._get(self.req_data, 'estimateId', 'estimate_id', 'id')
        if not estimate_id:
            return {}, 'estimateId 为必传参数'
        return AiWorkloadEstimateService.retry_estimate(
            self.session, estimate_id, getattr(g, 'current_user_id', None)
        )
