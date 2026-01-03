"""
ADMIN CHAT PERFORMANCE MONITORING SERVICE
==========================================
File: app/services/admin_chat_performance_service.py
Version: 1.0.0 - "REAL-TIME-METRICS"

MISSION (المهمة):
-----------------
خدمة مراقبة الأداء في الوقت الفعلي للمحادثات الإدارية.

Features:
- Real-time performance tracking
- A/B testing framework
- Latency monitoring
- User experience metrics
- Automatic optimization suggestions
"""
from typing import Any

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)

class PerformanceCategory(Enum):
    """Performance categories"""
    EXCELLENT = 'excellent'
    GOOD = 'good'
    ACCEPTABLE = 'acceptable'
    SLOW = 'slow'

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_id: str
    category: str
    latency_ms: float
    tokens: int
    model_used: str
    timestamp: datetime = field(default_factory=lambda : datetime.now(UTC))
    user_id: int | None = None

    def get_category(self) ->PerformanceCategory:
        """Get performance category based on latency"""
        if self.latency_ms < 500:
            return PerformanceCategory.EXCELLENT
        if self.latency_ms < 1000:
            return PerformanceCategory.GOOD
        if self.latency_ms < 3000:
            return PerformanceCategory.ACCEPTABLE
        return PerformanceCategory.SLOW


@dataclass
class MetricRecordConfig:
    """
    إعدادات تسجيل المقياس.
    Configuration for recording a performance metric.
    """
    category: str
    latency_ms: float
    tokens: int
    model_used: str
    user_id: int | None = None
    variant: ABTestVariant | None = None

class ABTestVariant(Enum):
    """A/B testing variants"""
    STREAMING_ENABLED = 'streaming_enabled'
    STREAMING_DISABLED = 'streaming_disabled'
    CHUNK_SIZE_3 = 'chunk_size_3'
    CHUNK_SIZE_5 = 'chunk_size_5'
    CHUNK_SIZE_1 = 'chunk_size_1'

@dataclass
class ABTestResult:
    """A/B test result"""
    variant: ABTestVariant
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    user_satisfaction: float = 0.0
    conversion_rate: float = 0.0

class AdminChatPerformanceService:
    """
    خدمة مراقبة أداء المحادثات الإدارية.

    Features:
    - Real-time metrics collection
    - Performance analysis
    - A/B testing support
    - Automatic optimization
    """

    def __init__(self):
        self.metrics: deque = deque(maxlen=10000)
        self.ab_tests: dict[ABTestVariant, ABTestResult] = {}
        self.user_variants: dict[int, ABTestVariant] = {}
        self.latency_threshold_ms = 1000
        self.error_threshold_pct = 5.0
        logger.info('✨ Admin Chat Performance Service initialized')

    def record_metric(
        self, 
        config: MetricRecordConfig
    ) -> PerformanceMetric:
        """
        تسجيل مقياس الأداء.
        Record a performance metric.

        Args:
            config: Metric recording configuration

        Returns:
            Recorded metric
        """
        metric = PerformanceMetric(
            metric_id=f'metric_{time.time()}',
            category=config.category, 
            latency_ms=config.latency_ms, 
            tokens=config.tokens,
            model_used=config.model_used, 
            user_id=config.user_id
        )
        
        self.metrics.append(metric)
        
        if config.variant:
            self._update_ab_test(config.variant, metric)
            
        self._check_performance_alerts(metric)
        
        return metric

    def get_statistics(self, category: (str | None)=None, hours: int=24
        ) ->dict[str, Any]:
        """
        الحصول على إحصائيات الأداء.
        Get performance statistics.

        Args:
            category: Filter by category (optional)
            hours: Time window in hours

        Returns:
            Statistics dictionary
        """
        filtered_metrics = self._filter_metrics_by_time(category, hours)
        
        if not filtered_metrics:
            return self._get_empty_statistics()
        
        latencies = sorted([m.latency_ms for m in filtered_metrics])
        category_counts = self._calculate_category_breakdown(filtered_metrics)
        perf_dist = self._calculate_performance_distribution(filtered_metrics)
        
        return self._build_statistics_dict(
            filtered_metrics, latencies, category_counts, perf_dist, hours
        )
    
    def _filter_metrics_by_time(
        self, 
        category: str | None, 
        hours: int
    ) -> list[PerformanceMetric]:
        """
        تصفية المقاييس حسب الوقت والفئة.
        Filter metrics by time window and category.
        
        Args:
            category: Optional category filter
            hours: Time window in hours
            
        Returns:
            Filtered list of metrics
        """
        cutoff_time = datetime.now(UTC).timestamp() - hours * 3600
        return [
            m for m in self.metrics 
            if m.timestamp.timestamp() > cutoff_time 
            and (category is None or m.category == category)
        ]
    
    def _get_empty_statistics(self) -> dict[str, Any]:
        """
        إرجاع إحصائيات فارغة عند عدم وجود بيانات.
        Return empty statistics when no data available.
        
        Returns:
            Empty statistics dictionary
        """
        return {
            'total_requests': 0, 
            'avg_latency_ms': 0,
            'p50_latency_ms': 0, 
            'p95_latency_ms': 0, 
            'p99_latency_ms': 0, 
            'total_tokens': 0, 
            'category_breakdown': {},
            'performance_distribution': {}
        }
    
    def _calculate_category_breakdown(
        self, 
        metrics: list[PerformanceMetric]
    ) -> dict[str, int]:
        """
        حساب توزيع الفئات.
        Calculate category distribution.
        
        Args:
            metrics: List of metrics
            
        Returns:
            Category counts dictionary
        """
        category_counts = defaultdict(int)
        for m in metrics:
            category_counts[m.category] += 1
        return dict(category_counts)
    
    def _calculate_performance_distribution(
        self, 
        metrics: list[PerformanceMetric]
    ) -> dict[str, int]:
        """
        حساب توزيع مستويات الأداء.
        Calculate performance level distribution.
        
        Args:
            metrics: List of metrics
            
        Returns:
            Performance distribution dictionary
        """
        perf_dist = defaultdict(int)
        for m in metrics:
            perf_dist[m.get_category().value] += 1
        return dict(perf_dist)
    
    def _build_statistics_dict(
        self,
        metrics: list[PerformanceMetric],
        latencies: list[float],
        category_counts: dict[str, int],
        perf_dist: dict[str, int],
        hours: int
    ) -> dict[str, Any]:
        """
        بناء قاموس الإحصائيات النهائي.
        Build final statistics dictionary.
        
        Args:
            metrics: List of metrics
            latencies: Sorted latencies list
            category_counts: Category breakdown
            perf_dist: Performance distribution
            hours: Time window hours
            
        Returns:
            Complete statistics dictionary
        """
        n = len(latencies)
        return {
            'total_requests': len(metrics), 
            'avg_latency_ms': sum(latencies) / n, 
            'p50_latency_ms': latencies[int(n * 0.5)],
            'p95_latency_ms': latencies[int(n * 0.95)], 
            'p99_latency_ms': latencies[int(n * 0.99)], 
            'total_tokens': sum(m.tokens for m in metrics), 
            'category_breakdown': category_counts,
            'performance_distribution': perf_dist,
            'time_window_hours': hours
        }

    def get_ab_results(self) ->dict[str, ABTestResult]:
        """Get A/B testing results"""
        return {v.value: r for v, r in self.ab_tests.items()}

    def get_optimization_suggestions(self) ->list[str]:
        """
        الحصول على اقتراحات التحسين التلقائية.
        Get automatic optimization suggestions based on metrics.

        Returns:
            List of optimization suggestions
        """
        stats = self.get_statistics()
        
        if stats['total_requests'] == 0:
            return ['Not enough data to provide suggestions. Keep using the system!']
        
        suggestions = []
        
        # Check various performance metrics
        self._check_average_latency(stats, suggestions)
        self._check_p95_latency(stats, suggestions)
        self._check_slow_requests(stats, suggestions)
        self._check_streaming_usage(stats, suggestions)
        self._check_excellent_performance(stats, suggestions)
        
        return suggestions if suggestions else [
            '✅ Performance is optimal! No suggestions at this time.'
        ]
    
    def _check_average_latency(
        self, 
        stats: dict[str, Any], 
        suggestions: list[str]
    ) -> None:
        """
        التحقق من متوسط زمن الاستجابة.
        Check if average latency is high.
        
        Args:
            stats: Performance statistics
            suggestions: List to append suggestions to
        """
        if stats['avg_latency_ms'] > 2000:
            suggestions.append(
                """⚠️ Average latency is high (>2s). Consider:
  - Enabling streaming if not already enabled
  - Using a faster AI model
  - Reducing context size"""
            )
    
    def _check_p95_latency(
        self, 
        stats: dict[str, Any], 
        suggestions: list[str]
    ) -> None:
        """
        التحقق من زمن الاستجابة للنسبة المئوية 95.
        Check if P95 latency is very high.
        
        Args:
            stats: Performance statistics
            suggestions: List to append suggestions to
        """
        if stats['p95_latency_ms'] > 5000:
            suggestions.append(
                """⚠️ P95 latency is very high (>5s). 5% of requests are slow. Consider:
  - Implementing request timeout
  - Adding caching layer
  - Load balancing across multiple instances"""
            )
    
    def _check_slow_requests(
        self, 
        stats: dict[str, Any], 
        suggestions: list[str]
    ) -> None:
        """
        التحقق من نسبة الطلبات البطيئة.
        Check percentage of slow requests.
        
        Args:
            stats: Performance statistics
            suggestions: List to append suggestions to
        """
        perf_dist = stats['performance_distribution']
        slow_pct = perf_dist.get('slow', 0) / stats['total_requests'] * 100
        
        if slow_pct > 10:
            suggestions.append(
                f"""⚠️ {slow_pct:.1f}% of requests are slow (>3s). Consider:
  - Increasing chunk size for faster streaming
  - Optimizing database queries
  - Using CDN for static assets"""
            )
    
    def _check_streaming_usage(
        self, 
        stats: dict[str, Any], 
        suggestions: list[str]
    ) -> None:
        """
        التحقق من استخدام البث المباشر.
        Check streaming adoption rate.
        
        Args:
            stats: Performance statistics
            suggestions: List to append suggestions to
        """
        streaming_pct = (
            stats['category_breakdown'].get('streaming', 0) / 
            stats['total_requests'] * 100
        )
        
        if streaming_pct < 50:
            suggestions.append(
                f"""💡 Only {streaming_pct:.1f}% of requests use streaming. Consider:
  - Enabling streaming by default
  - Streaming provides 6x better perceived performance"""
            )
    
    def _check_excellent_performance(
        self, 
        stats: dict[str, Any], 
        suggestions: list[str]
    ) -> None:
        """
        التحقق من الأداء الممتاز.
        Check if performance is excellent.
        
        Args:
            stats: Performance statistics
            suggestions: List to append suggestions to
        """
        perf_dist = stats['performance_distribution']
        excellent_pct = (
            perf_dist.get('excellent', 0) / 
            stats['total_requests'] * 100
        )
        
        if excellent_pct > 80:
            suggestions.append(
                f"""✅ Excellent performance! {excellent_pct:.1f}% of requests are <500ms.
  Keep up the great work!"""
            )

    def _update_ab_test(self, variant: ABTestVariant, metric: PerformanceMetric
        ):
        """Update A/B test results"""
        if variant not in self.ab_tests:
            self.ab_tests[variant] = ABTestResult(variant=variant)
        result = self.ab_tests[variant]
        result.total_requests += 1
        result.avg_latency_ms = (result.avg_latency_ms * (result.
            total_requests - 1) + metric.latency_ms) / result.total_requests

    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check for performance issues and log alerts"""
        if metric.latency_ms > self.latency_threshold_ms:
            logger.warning(
                f'⚠️ High latency detected: {metric.latency_ms}ms (category: {metric.category}, model: {metric.model_used})'
                )
        if metric.get_category() == PerformanceCategory.SLOW:
            logger.warning(
                f'⚠️ Slow request detected: {metric.latency_ms}ms (user: {metric.user_id}, category: {metric.category})'
                )

_performance_service: AdminChatPerformanceService | None = None

def get_performance_service() ->AdminChatPerformanceService:
    """Get or create performance service singleton"""
    global _performance_service
    if _performance_service is None:
        _performance_service = AdminChatPerformanceService()
    return _performance_service
