# encoding: UTF-8


class TestRecommendationService(object):
    @staticmethod
    def normalize_recommendations(analysis_result):
        tests = analysis_result.get('recommended_tests') or []
        return [item for item in tests if isinstance(item, dict)]
