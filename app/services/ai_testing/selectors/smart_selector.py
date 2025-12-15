from collections import defaultdict
from datetime import datetime
from app.services.ai_testing.domain.models import TestCase, TestType


class SmartTestSelector:
    """
    محدد اختبارات ذكي يختار الاختبارات الأكثر أهمية للتشغيل
    """

    def __init__(self):
        self.test_history: dict[str, list[dict]] = defaultdict(list)
        self.failure_patterns: dict[str, int] = defaultdict(int)

    def select_tests(self, all_tests: list[TestCase], changed_files: list[
        str], time_budget: float=300.0) ->list[TestCase]:
        """
        اختيار الاختبارات الأكثر أهمية بناءً على ML
        """
        scored_tests = []
        for test in all_tests:
            score = self._calculate_test_priority(test, changed_files)
            scored_tests.append((score, test))
        scored_tests.sort(reverse=True, key=lambda x: x[0])
        selected = []
        total_time = 0.0
        for _score, test in scored_tests:
            if total_time + test.estimated_execution_time <= time_budget:
                selected.append(test)
                total_time += test.estimated_execution_time
            else:
                break
        return selected

    def _calculate_test_priority(self, test: TestCase, changed_files: list[str]
        ) ->float:
        """حساب أولوية الاختبار"""
        score = 0.0
        score += test.priority * 10
        score += test.confidence * 20
        failure_count = self.failure_patterns.get(test.test_id, 0)
        score += failure_count * 15
        if any(test.function_under_test in f for f in changed_files):
            score += 50
        type_weights = {TestType.SECURITY: 1.5, TestType.INTEGRATION: 1.3,
            TestType.UNIT: 1.0, TestType.PERFORMANCE: 0.8}
        score *= type_weights.get(test.test_type, 1.0)
        return score
