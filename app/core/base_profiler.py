# app/core/base_profiler.py
"""
SUPERHUMAN BASE PROFILER - DRY PRINCIPLE ENFORCEMENT
====================================================
Base class فائق الذكاء لتوحيد telemetry/profiler duplications

This eliminates the catastrophic duplication found in overmind/planning/telemetry.py
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class RingBuffer(Generic[T]):  # noqa: UP046
    """
    Thread-safe ring buffer for storing samples.
    Unified implementation to eliminate duplication.
    """

    max_size: int
    buffer: deque[T] = field(default_factory=deque)

    def __post_init__(self):
        """Initialize with max size."""
        self.buffer = deque(maxlen=self.max_size)

    def append(self, item: T) -> None:
        """Add item to buffer."""
        self.buffer.append(item)

    def clear(self) -> None:
        """Clear all items."""
        self.buffer.clear()

    def __len__(self) -> int:
        """Get buffer size."""
        return len(self.buffer)

    def __iter__(self):
        """Iterate over buffer."""
        return iter(self.buffer)

    def to_list(self) -> list[T]:
        """Convert to list."""
        return list(self.buffer)

class BaseProfiler:
    """
    Base class for profilers with common functionality.

    ✅ Eliminates duplicated __init__, clear(), enable(), disable(), enabled() methods
    ✅ Provides consistent interface across all profilers
    ✅ Reduces code duplication from ~50 lines to ~10 lines per profiler
    """

    def __init__(self, max_samples: int = 1000):
        """
        Initialize profiler.

        Args:
            max_samples: Maximum number of samples to store
        """
        self._buffer: RingBuffer[Any] = RingBuffer(max_samples)
        self._enabled: bool = True

    def clear(self) -> None:
        """Clear all samples."""
        self._buffer.clear()

    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if profiling is enabled."""
        return self._enabled

    @property
    def sample_count(self) -> int:
        """Get number of samples."""
        return len(self._buffer)

    def get_samples(self) -> list[Any]:
        """Get all samples as list."""
        return self._buffer.to_list()

class BaseMetricsCollector(BaseProfiler):
    """
    Base class for metrics collectors with aggregation.

    ✅ Extends BaseProfiler with metrics-specific functionality
    ✅ Provides common aggregation methods
    """

    def __init__(self, max_samples: int = 1000):
        super().__init__(max_samples)
        self._total_count: int = 0

    def record(self, value: dict[str, str | int | bool]) -> None:
        """
        Record a metric value.

        Args:
            value: Value to record
        """
        if not self._enabled:
            return

        self._buffer.append(value)
        self._total_count += 1

    @property
    def total_count(self) -> int:
        """Get total number of recorded metrics."""
        return self._total_count

    def reset(self) -> None:
        """Reset all metrics."""
        self.clear()
        self._total_count = 0

    def get_statistics(self) -> dict[str, Any]:
        """
        Get basic statistics.

        Returns:
            Dictionary with count, enabled status
        """
        return {
            "enabled": self._enabled,
            "total_count": self._total_count,
            "buffer_size": self.sample_count,
            "max_samples": self._buffer.max_size,
        }

# ==================== SPECIALIZED PROFILERS ====================

class TimeProfiler(BaseMetricsCollector):
    """
    Time-based profiler for performance monitoring.

    ✅ Eliminates duplication in timing profilers
    """

    def record_duration(self, duration_ms: float, operation: str = "") -> None:
        """
        Record operation duration.

        Args:
            duration_ms: Duration in milliseconds
            operation: Optional operation name
        """
        self.record(
            {
                "duration_ms": duration_ms,
                "operation": operation,
            }
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get timing statistics with averages."""
        stats = super().get_statistics()

        samples = self.get_samples()
        if not samples:
            return stats

        durations = [s.get("duration_ms", 0) for s in samples if isinstance(s, dict)]
        if durations:
            stats["avg_duration_ms"] = sum(durations) / len(durations)
            stats["min_duration_ms"] = min(durations)
            stats["max_duration_ms"] = max(durations)

        return stats

class CountProfiler(BaseMetricsCollector):
    """
    Counter-based profiler for event counting.

    ✅ Eliminates duplication in counting profilers
    """

    def increment(self, category: str = "default") -> None:
        """
        Increment counter for category.

        Args:
            category: Category name
        """
        self.record({"category": category, "count": 1})

    def get_statistics(self) -> dict[str, Any]:
        """Get count statistics by category."""
        stats = super().get_statistics()

        samples = self.get_samples()
        if not samples:
            return stats

        # Count by category
        category_counts: dict[str, int] = {}
        for sample in samples:
            if isinstance(sample, dict):
                cat = sample.get("category", "default")
                category_counts[cat] = category_counts.get(cat, 0) + 1

        stats["categories"] = category_counts
        return stats

# ==================== EXPORTS ====================

__all__ = [
    "BaseMetricsCollector",
    "BaseProfiler",
    "CountProfiler",
    "RingBuffer",
    "TimeProfiler",
]

# ==================== MIGRATION GUIDE ====================
"""
MIGRATION GUIDE - How to use these base classes
================================================

# Before (DUPLICATED CODE):
class MyProfiler:
    def __init__(self, max_samples: int = 1000):
        self._buffer = RingBuffer(max_samples)
        self._enabled = True

    def clear(self) -> None:
        self._buffer.clear()

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ... custom methods

# After (DRY):
class MyProfiler(BaseMetricsCollector):
    # All common methods inherited!

    # Only implement custom functionality:
    def my_custom_method(self) -> None:
        self.record({"custom": "data"})

# For timing:
profiler = TimeProfiler()
profiler.record_duration(150.5, "database_query")
stats = profiler.get_statistics()

# For counting:
counter = CountProfiler()
counter.increment("api_calls")
counter.increment("api_calls")
stats = counter.get_statistics()  # {"categories": {"api_calls": 2}}
"""
