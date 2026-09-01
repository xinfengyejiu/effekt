# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.testAssetGovernanceService import TestAssetGovernanceService


class TestAssetGovernanceController(BaseCrudController):
    def scan_create(self):
        return TestAssetGovernanceService.create_scan(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def scan_list(self):
        return TestAssetGovernanceService.list_scans(self.session, self.req_data)

    def scan_detail(self):
        scan_id = self._get(self.req_data, 'scanId', 'scan_id', 'id')
        if not scan_id:
            return {}, 'scanId 为必传参数'
        return TestAssetGovernanceService.scan_detail(self.session, scan_id)

    def scan_execute(self):
        scan_id = self._get(self.req_data, 'scanId', 'scan_id', 'id')
        if not scan_id:
            return {}, 'scanId 为必传参数'
        return TestAssetGovernanceService.execute_scan(self.session, scan_id)

    def issue_list(self):
        return TestAssetGovernanceService.list_issues(self.session, self.req_data)

    def issue_update(self):
        return TestAssetGovernanceService.update_issue(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )

    def action_apply(self):
        return TestAssetGovernanceService.apply_action(
            self.session, self.req_data, getattr(g, 'current_user_id', None)
        )
