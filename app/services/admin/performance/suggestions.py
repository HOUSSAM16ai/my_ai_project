"""محرك اقتراحات تحسين أداء المحادثات الإدارية."""

from __future__ import annotations

from app.services.admin.performance.statistics import PerformanceStatistics


class PerformanceSuggestionEngine:
    """مولّد اقتراحات يقرأ الإحصائيات ويعيد نصوصًا إرشادية."""

    def suggest(self, stats: PerformanceStatistics) -> list[str]:
        """يعيد قائمة اقتراحات تحسين الأداء أو رسالة تفاؤلية."""
        if stats.get("total_requests", 0) == 0:
            return ["Not enough data to provide suggestions. Keep using the system!"]

        suggestions: list[str] = []
        self._check_average_latency(stats, suggestions)
        self._check_p95_latency(stats, suggestions)
        self._check_slow_requests(stats, suggestions)
        self._check_streaming_usage(stats, suggestions)
        self._check_excellent_performance(stats, suggestions)
        return suggestions or [
            "✅ Performance is optimal! No suggestions at this time."
        ]

    @staticmethod
    def _check_average_latency(
        stats: PerformanceStatistics, suggestions: list[str]
    ) -> None:
        """يتحقق من متوسط زمن الاستجابة ويضيف اقتراحًا عند الحاجة."""
        if stats.get("avg_latency_ms", 0) > 2000:
            suggestions.append(
                """⚠️ Average latency is high (>2s). Consider:
  - Enabling streaming if not already enabled
  - Using a faster AI model
  - Reducing context size"""
            )

    @staticmethod
    def _check_p95_latency(
        stats: PerformanceStatistics, suggestions: list[str]
    ) -> None:
        """يتحقق من زمن الاستجابة للنسبة المئوية 95."""
        if stats.get("p95_latency_ms", 0) > 5000:
            suggestions.append(
                """⚠️ P95 latency is very high (>5s). 5% of requests are slow. Consider:
  - Implementing request timeout
  - Adding caching layer
  - Load balancing across multiple instances"""
            )

    @staticmethod
    def _check_slow_requests(
        stats: PerformanceStatistics, suggestions: list[str]
    ) -> None:
        """يراقب نسبة الطلبات البطيئة ويقترح تحسينات."""
        total_requests = stats.get("total_requests", 0)
        if total_requests == 0:
            return
        perf_dist = stats.get("performance_distribution", {})
        slow_pct = perf_dist.get("slow", 0) / total_requests * 100
        if slow_pct > 10:
            suggestions.append(
                f"""⚠️ {slow_pct:.1f}% of requests are slow (>3s). Consider:
  - Increasing chunk size for faster streaming
  - Optimizing database queries
  - Using CDN for static assets"""
            )

    @staticmethod
    def _check_streaming_usage(
        stats: PerformanceStatistics, suggestions: list[str]
    ) -> None:
        """يتحقق من معدل استخدام البث المباشر ويضيف توصيات."""
        total_requests = stats.get("total_requests", 0)
        if total_requests == 0:
            return
        category_breakdown = stats.get("category_breakdown", {})
        streaming_pct = category_breakdown.get("streaming", 0) / total_requests * 100
        if streaming_pct < 50:
            suggestions.append(
                f"""💡 Only {streaming_pct:.1f}% of requests use streaming. Consider:
  - Enabling streaming by default
  - Streaming provides 6x better perceived performance"""
            )

    @staticmethod
    def _check_excellent_performance(
        stats: PerformanceStatistics, suggestions: list[str]
    ) -> None:
        """يتحقق من نسبة الأداء الممتاز ويضيف إشادة مناسبة."""
        total_requests = stats.get("total_requests", 0)
        if total_requests == 0:
            return
        perf_dist = stats.get("performance_distribution", {})
        excellent_pct = perf_dist.get("excellent", 0) / total_requests * 100
        if excellent_pct > 80:
            suggestions.append(
                f"""✅ Excellent performance! {excellent_pct:.1f}% of requests are <500ms.
  Keep up the great work!"""
            )
