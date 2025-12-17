from app.services.ai_testing.domain.models import TestCase
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

    def select_tests(self, all_tests: list[TestCase], changed_files: list[
        str], time_budget: float=300.0) ->list[TestCase]:
        """اختيار الاختبارات الذكي"""
        return self.selector.select_tests(all_tests, changed_files, time_budget
            )


testing_system = IntelligentTestingSystem()
