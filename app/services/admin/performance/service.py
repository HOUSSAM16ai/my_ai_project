"""خدمة مراقبة أداء المحادثات الإدارية مع فصل واضح للمسؤوليات."""

from __future__ import annotations

import logging
import time

from app.services.admin.performance.ab_testing import ABTestTracker
from app.services.admin.performance.alerts import PerformanceAlertPolicy
from app.services.admin.performance.metrics import (
    ABTestResult,
    ABTestVariant,
    MetricRecordConfig,
    PerformanceMetric,
)
from app.services.admin.performance.statistics import (
    PerformanceStatistics,
    PerformanceStatisticsCalculator,
)
from app.services.admin.performance.store import MetricStore
from app.services.admin.performance.suggestions import PerformanceSuggestionEngine

logger = logging.getLogger(__name__)


class AdminChatPerformanceService:
    """منسق أداء المحادثات الإدارية مع حدود واضحة لكل مسؤولية."""

    def __init__(self) -> None:
        """يبني الخدمة ويجهز المخازن والسياسات المساعدة."""
        self._metric_store = MetricStore(maxlen=10_000)
        self._ab_test_tracker = ABTestTracker()
        self._statistics_calculator = PerformanceStatisticsCalculator()
        self._suggestion_engine = PerformanceSuggestionEngine()
        self._alert_policy = PerformanceAlertPolicy(latency_threshold_ms=1000)

        self.metrics = self._metric_store.metrics
        self.ab_tests = self._ab_test_tracker.ab_tests
        self.user_variants: dict[int, ABTestVariant] = {}
        self.latency_threshold_ms = 1000
        self.error_threshold_pct = 5.0

        logger.info("✨ Admin Chat Performance Service initialized")

    def record_metric(self, config: MetricRecordConfig) -> PerformanceMetric:
        """يسجل مقياس أداء جديد ويحدث مسارات التحليل ذات الصلة."""
        metric = PerformanceMetric(
            metric_id=f"metric_{time.time()}",
            category=config.category,
            latency_ms=config.latency_ms,
            tokens=config.tokens,
            model_used=config.model_used,
            user_id=config.user_id,
        )

        self._metric_store.append(metric)

        if config.variant:
            self._ab_test_tracker.update(config.variant, metric)

        self._alert_policy.check(metric)
        return metric

    def get_statistics(self, category: str | None = None, hours: int = 24) -> PerformanceStatistics:
        """يعيد إحصائيات الأداء ضمن النافذة الزمنية المطلوبة."""
        filtered_metrics = self._metric_store.filter_by_time(category, hours)
        return self._statistics_calculator.build_statistics(filtered_metrics, hours)

    def get_ab_results(self) -> dict[str, ABTestResult]:
        """يعيد نتائج اختبار A/B بصيغة مناسبة للعرض."""
        return self._ab_test_tracker.results_by_name()

    def get_optimization_suggestions(self) -> list[str]:
        """يعيد اقتراحات التحسين المستندة إلى الإحصائيات."""
        stats = self.get_statistics()
        return self._suggestion_engine.suggest(stats)


_performance_service: AdminChatPerformanceService | None = None


def get_performance_service() -> AdminChatPerformanceService:
    """يوفر مثيلاً مشتركًا لخدمة الأداء عند الحاجة."""
    global _performance_service
    if _performance_service is None:
        _performance_service = AdminChatPerformanceService()
    return _performance_service
