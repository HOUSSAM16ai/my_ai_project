"""متتبع اختبارات A/B المرتبط بمقاييس الأداء."""

from __future__ import annotations

from app.services.admin.performance.metrics import ABTestResult, ABTestVariant, PerformanceMetric


class ABTestTracker:
    """يسجل نتائج اختبارات A/B ويحدث المتوسطات باستمرار."""

    def __init__(self) -> None:
        """يبني قاموس النتائج التراكمية."""
        self.ab_tests: dict[ABTestVariant, ABTestResult] = {}

    def update(self, variant: ABTestVariant, metric: PerformanceMetric) -> None:
        """يحدث سجل النتائج حسب المتغير والمقياس الجديد."""
        if variant not in self.ab_tests:
            self.ab_tests[variant] = ABTestResult(variant=variant)
        result = self.ab_tests[variant]
        result.total_requests += 1
        result.avg_latency_ms = (
            result.avg_latency_ms * (result.total_requests - 1) + metric.latency_ms
        ) / result.total_requests

    def results_by_name(self) -> dict[str, ABTestResult]:
        """يعيد النتائج مع مفاتيح نصية توافق واجهات العرض."""
        return {variant.value: result for variant, result in self.ab_tests.items()}
