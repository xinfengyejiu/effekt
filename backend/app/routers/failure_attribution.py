# encoding: UTF-8
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.service.failureAttributionService import FailureAttributionService
from app.api.controller.baseCrudController import BaseCrudController

router = APIRouter(tags=['failure-attribution'])


class _FailureAttributionController(BaseCrudController):
    def summary(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        hours = self._get(self.req_data, 'hours', default=24)
        return FailureAttributionService.summary(self.session, project_id, hours=hours)


@router.get('/failure-attribution/summary')
async def failure_attribution_summary(
    request: Request,
    user: dict = Depends(require_permission('case:list')),
    db: Session = Depends(get_db),
):
    controller = _FailureAttributionController(dict(request.query_params))
    try:
        ret, err = controller.summary()
        if err:
            return api_failure(40011, msg=err)
        return api_success(data=ret)
    finally:
        controller.close_session()
