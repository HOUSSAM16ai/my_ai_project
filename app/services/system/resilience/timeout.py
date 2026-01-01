from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field

@dataclass
class TimeoutConfig:
    """Timeout hierarchy configuration"""

    connection_timeout_ms: int = 3000  # 3s for connection
    read_timeout_ms: int = 30000  # 30s for read
    request_timeout_ms: int = 60000  # 60s total
    adaptive_enabled: bool = True  # Use P95-based adaptive timeout

@dataclass
class LatencyMetrics:
    """Latency tracking for adaptive timeout"""

    samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    p999: float = 0.0

class AdaptiveTimeout:
    """
    Adaptive Timeout based on P95 latency

    Features:
    - Tracks latency history
    - Calculates P50, P95, P99, P99.9
    - Dynamically adjusts timeout = P95 * 1.5
    """

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self.metrics = LatencyMetrics()
        self._lock = threading.RLock()

    def record_latency(self, latency_ms: float) -> None:
        """Record a latency sample"""
        with self._lock:
            self.metrics.samples.append(latency_ms)
            self._update_percentiles()

    def get_timeout_ms(self) -> int:
        """Get adaptive timeout based on P95"""
        if not self.config.adaptive_enabled or len(self.metrics.samples) < 100:
            return self.config.request_timeout_ms

        # timeout = P95 * 1.5
        adaptive_timeout = int(self.metrics.p95 * 1.5)
        return min(adaptive_timeout, self.config.request_timeout_ms)

    def _update_percentiles(self) -> None:
        """Update percentile calculations"""
        if len(self.metrics.samples) < 10:
            return

        sorted_samples = sorted(self.metrics.samples)
        n = len(sorted_samples)

        self.metrics.p50 = sorted_samples[int(n * 0.50)]
        self.metrics.p95 = sorted_samples[int(n * 0.95)]
        self.metrics.p99 = sorted_samples[int(n * 0.99)]
        self.metrics.p999 = sorted_samples[int(n * 0.999)] if n >= 1000 else self.metrics.p99

    def get_stats(self) -> dict:
        """Get timeout statistics"""
        return {
            "adaptive_enabled": self.config.adaptive_enabled,
            "current_timeout_ms": self.get_timeout_ms(),
            "p50": round(self.metrics.p50, 2),
            "p95": round(self.metrics.p95, 2),
            "p99": round(self.metrics.p99, 2),
            "p999": round(self.metrics.p999, 2),
            "samples": len(self.metrics.samples),
        }
