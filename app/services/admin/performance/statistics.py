"""مُحلل إحصائي مخصص لمقاييس أداء المحادثات الإدارية."""

from __future__ import annotations

from collections import defaultdict

from app.services.admin.performance.metrics import PerformanceMetric

PerformanceStatistics = dict[str, float | int | dict[str, int]]


class PerformanceStatisticsCalculator:
    """حاسبة إحصائيات تعيد بيانات مجمعة قابلة للعرض."""

    def build_statistics(
        self, metrics: list[PerformanceMetric], hours: int
    ) -> PerformanceStatistics:
        """يبني قاموس الإحصائيات النهائي بناءً على المقاييس المتاحة."""
        if not metrics:
            return self._empty_statistics()

        latencies = sorted(metric.latency_ms for metric in metrics)
        category_counts = self._calculate_category_breakdown(metrics)
        perf_dist = self._calculate_performance_distribution(metrics)
        return self._build_statistics_dict(metrics, latencies, category_counts, perf_dist, hours)

    @staticmethod
    def _empty_statistics() -> PerformanceStatistics:
        """يعيد قاموسًا فارغًا عند غياب أي بيانات."""
        return {
            "total_requests": 0,
            "avg_latency_ms": 0,
            "p50_latency_ms": 0,
            "p95_latency_ms": 0,
            "p99_latency_ms": 0,
            "total_tokens": 0,
            "category_breakdown": {},
            "performance_distribution": {},
        }

    @staticmethod
    def _calculate_category_breakdown(
        metrics: list[PerformanceMetric],
    ) -> dict[str, int]:
        """يحسِب عدد المقاييس لكل فئة أداء."""
        category_counts: dict[str, int] = defaultdict(int)
        for metric in metrics:
            category_counts[metric.category] += 1
        return dict(category_counts)

    @staticmethod
    def _calculate_performance_distribution(
        metrics: list[PerformanceMetric],
    ) -> dict[str, int]:
        """يعيد توزيع مستويات الأداء وفق التصنيف القياسي."""
        perf_dist: dict[str, int] = defaultdict(int)
        for metric in metrics:
            perf_dist[metric.get_category().value] += 1
        return dict(perf_dist)

    @staticmethod
    def _build_statistics_dict(
        metrics: list[PerformanceMetric],
        latencies: list[float],
        category_counts: dict[str, int],
        perf_dist: dict[str, int],
        hours: int,
    ) -> PerformanceStatistics:
        """يبني قاموس الإحصائيات الكامل مع إضافة نافذة القياس."""
        total = len(latencies)
        return {
            "total_requests": len(metrics),
            "avg_latency_ms": sum(latencies) / total,
            "p50_latency_ms": latencies[int(total * 0.5)],
            "p95_latency_ms": latencies[int(total * 0.95)],
            "p99_latency_ms": latencies[int(total * 0.99)],
            "total_tokens": sum(metric.tokens for metric in metrics),
            "category_breakdown": category_counts,
            "performance_distribution": perf_dist,
            "time_window_hours": hours,
        }
