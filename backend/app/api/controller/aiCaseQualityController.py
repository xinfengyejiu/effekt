# encoding: UTF-8
from app.api.controller.baseCrudController import BaseCrudController
from app.api.service.aiCaseQualityService import AiCaseQualityService


class AiCaseQualityController(BaseCrudController):

    def summary(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        from_time = self._get(self.req_data, 'from', 'fromTime', 'startTime')
        to_time = self._get(self.req_data, 'to', 'toTime', 'endTime')
        return AiCaseQualityService.summary(self.session, project_id, from_time, to_time)

    def rewritten_list(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        page_no = self._get(self.req_data, 'pageNo', 'page_no', default=1)
        page_size = self._get(self.req_data, 'pageSize', 'page_size', default=20)
        status = self._get(self.req_data, 'status', default='rewritten')
        return AiCaseQualityService.rewritten_list(
            self.session, project_id, page_no=page_no, page_size=page_size, status=status
        )
