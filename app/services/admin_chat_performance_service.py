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

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceCategory(Enum):
    """Performance categories"""
    EXCELLENT = "excellent"  # <500ms
    GOOD = "good"  # 500ms-1s
    ACCEPTABLE = "acceptable"  # 1-3s
    SLOW = "slow"  # >3s


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_id: str
    category: str  # streaming, traditional, analysis
    latency_ms: float
    tokens: int
    model_used: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    user_id: Optional[int] = None
    
    def get_category(self) -> PerformanceCategory:
        """Get performance category based on latency"""
        if self.latency_ms < 500:
            return PerformanceCategory.EXCELLENT
        elif self.latency_ms < 1000:
            return PerformanceCategory.GOOD
        elif self.latency_ms < 3000:
            return PerformanceCategory.ACCEPTABLE
        else:
            return PerformanceCategory.SLOW


class ABTestVariant(Enum):
    """A/B testing variants"""
    STREAMING_ENABLED = "streaming_enabled"
    STREAMING_DISABLED = "streaming_disabled"
    CHUNK_SIZE_3 = "chunk_size_3"
    CHUNK_SIZE_5 = "chunk_size_5"
    CHUNK_SIZE_1 = "chunk_size_1"


@dataclass
class ABTestResult:
    """A/B test result"""
    variant: ABTestVariant
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    user_satisfaction: float = 0.0  # 0-10 scale
    conversion_rate: float = 0.0  # Percentage


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
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.ab_tests: Dict[ABTestVariant, ABTestResult] = {}
        self.user_variants: Dict[int, ABTestVariant] = {}
        
        # Performance thresholds
        self.latency_threshold_ms = 1000  # Alert if P95 > 1s
        self.error_threshold_pct = 5.0  # Alert if error rate > 5%
        
        logger.info("✨ Admin Chat Performance Service initialized")
    
    def record_metric(
        self,
        category: str,
        latency_ms: float,
        tokens: int,
        model_used: str,
        user_id: Optional[int] = None,
        variant: Optional[ABTestVariant] = None
    ) -> PerformanceMetric:
        """
        Record a performance metric.
        
        Args:
            category: Type of operation (streaming, traditional, etc)
            latency_ms: Latency in milliseconds
            tokens: Number of tokens processed
            model_used: AI model used
            user_id: User ID if available
            variant: A/B test variant if applicable
            
        Returns:
            Recorded metric
        """
        metric = PerformanceMetric(
            metric_id=f"metric_{time.time()}",
            category=category,
            latency_ms=latency_ms,
            tokens=tokens,
            model_used=model_used,
            user_id=user_id
        )
        
        self.metrics.append(metric)
        
        # Update A/B test results if variant specified
        if variant:
            self._update_ab_test(variant, metric)
        
        # Check for performance issues
        self._check_performance_alerts(metric)
        
        return metric
    
    def get_statistics(
        self,
        category: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Args:
            category: Filter by category (optional)
            hours: Time window in hours
            
        Returns:
            Statistics dictionary
        """
        # Filter metrics
        cutoff_time = datetime.now(UTC).timestamp() - (hours * 3600)
        filtered_metrics = [
            m for m in self.metrics
            if m.timestamp.timestamp() > cutoff_time
            and (category is None or m.category == category)
        ]
        
        if not filtered_metrics:
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
        
        # Calculate latency percentiles
        latencies = sorted([m.latency_ms for m in filtered_metrics])
        n = len(latencies)
        
        # Category breakdown
        category_counts = defaultdict(int)
        for m in filtered_metrics:
            category_counts[m.category] += 1
        
        # Performance distribution
        perf_dist = defaultdict(int)
        for m in filtered_metrics:
            perf_dist[m.get_category().value] += 1
        
        return {
            'total_requests': len(filtered_metrics),
            'avg_latency_ms': sum(latencies) / n,
            'p50_latency_ms': latencies[int(n * 0.5)],
            'p95_latency_ms': latencies[int(n * 0.95)],
            'p99_latency_ms': latencies[int(n * 0.99)],
            'total_tokens': sum(m.tokens for m in filtered_metrics),
            'category_breakdown': dict(category_counts),
            'performance_distribution': dict(perf_dist),
            'time_window_hours': hours
        }
    
    def assign_ab_variant(self, user_id: int) -> ABTestVariant:
        """
        Assign A/B test variant to user using hash-based distribution.
        
        Args:
            user_id: User ID
            
        Returns:
            Assigned variant
        """
        # Check if user already has variant
        if user_id in self.user_variants:
            return self.user_variants[user_id]
        
        # Use hash for uniform distribution
        import hashlib
        hash_val = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
        variant_index = hash_val % len(ABTestVariant)
        variant = list(ABTestVariant)[variant_index]
        
        self.user_variants[user_id] = variant
        return variant
    
    def get_ab_results(self) -> Dict[str, ABTestResult]:
        """Get A/B testing results"""
        return {v.value: r for v, r in self.ab_tests.items()}
    
    def get_optimization_suggestions(self) -> List[str]:
        """
        Get automatic optimization suggestions based on metrics.
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        stats = self.get_statistics()
        
        if stats['total_requests'] == 0:
            return ["Not enough data to provide suggestions. Keep using the system!"]
        
        # Check average latency
        if stats['avg_latency_ms'] > 2000:
            suggestions.append(
                "⚠️ Average latency is high (>2s). Consider:\n"
                "  - Enabling streaming if not already enabled\n"
                "  - Using a faster AI model\n"
                "  - Reducing context size"
            )
        
        # Check P95 latency
        if stats['p95_latency_ms'] > 5000:
            suggestions.append(
                "⚠️ P95 latency is very high (>5s). 5% of requests are slow. Consider:\n"
                "  - Implementing request timeout\n"
                "  - Adding caching layer\n"
                "  - Load balancing across multiple instances"
            )
        
        # Check performance distribution
        perf_dist = stats['performance_distribution']
        slow_pct = (perf_dist.get('slow', 0) / stats['total_requests']) * 100
        
        if slow_pct > 10:
            suggestions.append(
                f"⚠️ {slow_pct:.1f}% of requests are slow (>3s). Consider:\n"
                "  - Increasing chunk size for faster streaming\n"
                "  - Optimizing database queries\n"
                "  - Using CDN for static assets"
            )
        
        # Check if streaming is being used
        streaming_pct = (
            stats['category_breakdown'].get('streaming', 0) / 
            stats['total_requests'] * 100
        )
        
        if streaming_pct < 50:
            suggestions.append(
                f"💡 Only {streaming_pct:.1f}% of requests use streaming. Consider:\n"
                "  - Enabling streaming by default\n"
                "  - Streaming provides 6x better perceived performance"
            )
        
        # Positive feedback
        excellent_pct = (
            perf_dist.get('excellent', 0) / stats['total_requests'] * 100
        )
        
        if excellent_pct > 80:
            suggestions.append(
                f"✅ Excellent performance! {excellent_pct:.1f}% of requests are <500ms.\n"
                "  Keep up the great work!"
            )
        
        return suggestions if suggestions else ["✅ Performance is optimal! No suggestions at this time."]
    
    def _update_ab_test(self, variant: ABTestVariant, metric: PerformanceMetric):
        """Update A/B test results"""
        if variant not in self.ab_tests:
            self.ab_tests[variant] = ABTestResult(variant=variant)
        
        result = self.ab_tests[variant]
        result.total_requests += 1
        
        # Update running average
        result.avg_latency_ms = (
            (result.avg_latency_ms * (result.total_requests - 1) + metric.latency_ms) /
            result.total_requests
        )
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check for performance issues and log alerts"""
        if metric.latency_ms > self.latency_threshold_ms:
            logger.warning(
                f"⚠️ High latency detected: {metric.latency_ms}ms "
                f"(category: {metric.category}, model: {metric.model_used})"
            )
        
        if metric.get_category() == PerformanceCategory.SLOW:
            logger.warning(
                f"⚠️ Slow request detected: {metric.latency_ms}ms "
                f"(user: {metric.user_id}, category: {metric.category})"
            )


# Singleton instance
_performance_service: Optional[AdminChatPerformanceService] = None


def get_performance_service() -> AdminChatPerformanceService:
    """Get or create performance service singleton"""
    global _performance_service
    if _performance_service is None:
        _performance_service = AdminChatPerformanceService()
    return _performance_service
