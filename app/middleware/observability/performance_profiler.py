"""
مُحلل الأداء - Performance Profiler

Detailed performance profiling middleware that tracks latency,
throughput, and identifies bottlenecks.
"""
import time
from typing import Any

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


class PerformanceProfiler(BaseMiddleware):
    """
    Performance Profiler Middleware

    Features:
    - P50/P95/P99 latency tracking
    - Throughput measurement
    - Bottleneck identification
    - Resource utilization tracking
    """
    name = 'PerformanceProfiler'
    order = 1

    def _setup(self):
        """Initialize profiler"""
        self.latencies: list[float] = []
        self.max_latencies = self.config.get('max_latencies', 10000)
        self.profiled_count = 0
        self.total_duration = 0.0
        self.endpoint_stats: dict[str, dict[str, Any]] = {}

    def process_request(self, ctx: RequestContext) ->MiddlewareResult:
        """
        Start performance profiling

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        ctx.add_metadata('profiler_start', time.time())
        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult):
        """
        Record performance metrics

        Args:
            ctx: Request context
            result: Middleware result
        """
        start_time = ctx.get_metadata('profiler_start')
        if not start_time:
            return
        duration = time.time() - start_time
        duration_ms = duration * 1000
        self.profiled_count += 1
        self.total_duration += duration
        self.latencies.append(duration_ms)
        if len(self.latencies) > self.max_latencies:
            self.latencies = self.latencies[-self.max_latencies:]
        endpoint = ctx.path
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {'count': 0, 'total_duration':
                0.0, 'min_duration': float('inf'), 'max_duration': 0.0}
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_duration'] += duration_ms
        stats['min_duration'] = min(stats['min_duration'], duration_ms)
        stats['max_duration'] = max(stats['max_duration'], duration_ms)
        ctx.add_metadata('performance_profile', {'duration_ms': duration_ms,
            'endpoint': endpoint})

    def get_percentile(self, percentile: float) ->float:
        """
        Calculate latency percentile

        Args:
            percentile: Percentile to calculate (0-100)

        Returns:
            Latency value at percentile
        """
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * (percentile / 100))
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def get_statistics(self) ->dict:
        """Return performance profiler statistics"""
        stats = super().get_statistics()
        p50 = self.get_percentile(50)
        p95 = self.get_percentile(95)
        p99 = self.get_percentile(99)
        stats.update({'profiled_count': self.profiled_count,
            'total_duration_seconds': self.total_duration,
            'average_duration_ms': self.total_duration * 1000 / self.
            profiled_count if self.profiled_count > 0 else 0.0,
            'p50_latency_ms': p50, 'p95_latency_ms': p95, 'p99_latency_ms':
            p99, 'throughput_rps': self.profiled_count / self.
            total_duration if self.total_duration > 0 else 0.0,
            'tracked_endpoints': len(self.endpoint_stats)})
        return stats
