from typing import Any

from app.services.ai_testing.domain.models import CodeAnalysis, TestCase
from app.services.ai_testing.generators.test_generator import AITestGenerator
from app.services.ai_testing.optimizers.coverage_optimizer import CoverageOptimizer
from app.services.ai_testing.selectors.smart_selector import SmartTestSelector


class IntelligentTestingSystem:
    """
    نظام الاختبار الذكي المدعوم بالذكاء الاصطناعي
    """

    def __init__(self):
        self.generator = AITestGenerator()
        self.selector = SmartTestSelector()
        self.optimizer = CoverageOptimizer()

    def analyze_and_generate(self, code: str, file_path: str, num_tests: int = 5) -> tuple[CodeAnalysis, list[TestCase]]:
        """
        تحليل الكود وتوليد الاختبارات
        """
        analysis = self.generator.analyze_code(code, file_path)

        all_tests = []
        for func in analysis.functions:
            tests = self.generator.generate_tests_for_function(func, file_path, num_tests=num_tests)
            all_tests.extend(tests)

        return analysis, all_tests

    def select_tests(
        self,
        all_tests: list[TestCase],
        changed_files: list[str],
        time_budget: float = 300.0,
    ) -> list[TestCase]:
        """اختيار الاختبارات الذكي"""
        return self.selector.select_tests(all_tests, changed_files, time_budget)

    def optimize_suite(self, tests: list[TestCase], coverage_goal: float = 90.0) -> list[TestCase]:
        """تحسين مجموعة الاختبارات"""
        return self.optimizer.optimize_test_suite(tests, coverage_goal)


# Global instance
testing_system = IntelligentTestingSystem()
