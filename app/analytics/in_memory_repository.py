"""In-memory metrics repository - Dependency Inversion Principle."""

import threading
from collections import deque
from datetime import UTC, datetime, timedelta

from .entities import UsageMetric


class InMemoryMetricsRepository:
    """In-memory metrics repository - DIP: Implements domain interface."""

    def __init__(self, max_size: int = 10000):
        self._metrics: deque[UsageMetric] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def save(self, metric: UsageMetric) -> None:
        """Save a metric."""
        with self._lock:
            self._metrics.append(metric)

    def get_recent(self, hours: int) -> list[UsageMetric]:
        """Get metrics from the last N hours."""
        with self._lock:
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            return [m for m in self._metrics if m.timestamp > cutoff]

    def get_by_user(self, user_id: str) -> list[UsageMetric]:
        """Get all metrics for a specific user."""
        with self._lock:
            return [m for m in self._metrics if m.user_id == user_id]

    def get_range(self, start_time: datetime, end_time: datetime) -> list[UsageMetric]:
        """Get metrics within a time range."""
        with self._lock:
            return [m for m in self._metrics if start_time <= m.timestamp <= end_time]

    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self._metrics.clear()

    def count(self) -> int:
        """Get total count of metrics."""
        with self._lock:
            return len(self._metrics)
