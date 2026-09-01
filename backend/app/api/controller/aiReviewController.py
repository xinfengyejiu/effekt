# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from ..service.aiReviewService import AiReviewService


class AiReviewController(BaseCrudController):
    def review_create(self):
        return AiReviewService.create_review(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def review_list(self):
        return AiReviewService.list_reviews(self.session, self.req_data)

    def review_detail(self):
        review_id = self._get(self.req_data, 'reviewId', 'review_id', 'id')
        if not review_id:
            return {}, 'reviewId 为必传参数'
        return AiReviewService.review_detail(self.session, review_id)

    def review_execute(self):
        review_id = self._get(self.req_data, 'reviewId', 'review_id', 'id')
        if not review_id:
            return {}, 'reviewId 为必传参数'
        return AiReviewService.execute_review(self.session, review_id)

    def review_confirm(self):
        return AiReviewService.confirm_review(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def finding_update(self):
        return AiReviewService.update_finding(self.session, self.req_data)

    def case_import(self):
        return AiReviewService.import_suggested_case(self.session, self.req_data, getattr(g, 'current_user_id', None))

    def case_link(self):
        return AiReviewService.link_existing_case(self.session, self.req_data)
