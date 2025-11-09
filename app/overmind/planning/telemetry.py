# app/overmind/planning/telemetry.py
# ======================================================================================
# PLANNER FACTORY TELEMETRY - RING BUFFERS & PROFILING
# Version 5.0.0 - Bounded Memory Profiling
# ======================================================================================
"""
Telemetry and profiling support for the Planner Factory.
Implements ring buffers for selection and instantiation profiling with bounded memory.
"""

import time
from collections import deque
from typing import Any, Dict, List


class RingBuffer:
    """
    Thread-safe ring buffer with fixed capacity.
    Automatically evicts oldest entries when capacity is reached.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize ring buffer.

        Args:
            max_size: Maximum number of entries to store
        """
        self._buffer: deque = deque(maxlen=max_size)
        self._max_size = max_size

    def push(self, sample: Dict[str, Any]):
        """Add a sample to the buffer, evicting oldest if at capacity."""
        self._buffer.append(sample)

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all samples in the buffer."""
        return list(self._buffer)

    def get_last(self, n: int) -> List[Dict[str, Any]]:
        """Get last N samples from the buffer."""
        if n <= 0:
            return []
        return list(self._buffer)[-n:]

    def clear(self):
        """Clear all samples from the buffer."""
        self._buffer.clear()

    def __len__(self) -> int:
        """Return current number of samples in buffer."""
        return len(self._buffer)

    @property
    def max_size(self) -> int:
        """Return maximum capacity of buffer."""
        return self._max_size


class SelectionProfiler:
    """
    Profiler for planner selection operations.
    Tracks selection decisions, scores, and timing.
    """

    def __init__(self, max_samples: int = 1000):
        self._buffer = RingBuffer(max_samples)
        self._enabled = True

    def record_selection(
        self,
        objective_len: int,
        required_caps: list[str],
        best_planner: str,
        score: float,
        candidates_count: int,
        deep_context: bool,
        hotspots_count: int,
        breakdown: Dict[str, Any],
        duration_s: float,
        boost_config: Dict[str, Any],
    ):
        """Record a planner selection event."""
        if not self._enabled:
            return

        sample = {
            "objective_len": objective_len,
            "required_caps": sorted(required_caps),
            "best": best_planner,
            "score": score,
            "candidates_considered": candidates_count,
            "deep_index": deep_context,
            "hotspots": hotspots_count,
            "breakdown": breakdown,
            "boost_config": boost_config,
            "duration_s": duration_s,
            "ts": time.time(),
        }
        self._buffer.push(sample)

    def get_samples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent selection samples."""
        return self._buffer.get_last(limit)

    def get_all_samples(self) -> List[Dict[str, Any]]:
        """Get all selection samples."""
        return self._buffer.get_all()

    def clear(self):
        """Clear all samples."""
        self._buffer.clear()

    def enable(self):
        """Enable profiling."""
        self._enabled = True

    def disable(self):
        """Disable profiling."""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if profiling is enabled."""
        return self._enabled


class InstantiationProfiler:
    """
    Profiler for planner instantiation operations.
    Tracks instantiation timing and success/failure.
    """

    def __init__(self, max_samples: int = 1000):
        self._buffer = RingBuffer(max_samples)
        self._enabled = True

    def record_instantiation(self, planner_name: str, duration_s: float, success: bool = True):
        """Record a planner instantiation event."""
        if not self._enabled:
            return

        sample = {
            "name": planner_name,
            "duration_s": duration_s,
            "success": success,
            "ts": time.time(),
        }
        self._buffer.push(sample)

    def get_samples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent instantiation samples."""
        return self._buffer.get_last(limit)

    def get_all_samples(self) -> List[Dict[str, Any]]:
        """Get all instantiation samples."""
        return self._buffer.get_all()

    def clear(self):
        """Clear all samples."""
        self._buffer.clear()

    def enable(self):
        """Enable profiling."""
        self._enabled = True

    def disable(self):
        """Disable profiling."""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if profiling is enabled."""
        return self._enabled


class TelemetryManager:
    """
    Central telemetry manager for the factory.
    Coordinates selection and instantiation profiling.
    """

    def __init__(
        self,
        max_profiles: int = 1000,
        enable_selection: bool = True,
        enable_instantiation: bool = True,
    ):
        self.selection_profiler = SelectionProfiler(max_profiles)
        self.instantiation_profiler = InstantiationProfiler(max_profiles)

        if not enable_selection:
            self.selection_profiler.disable()
        if not enable_instantiation:
            self.instantiation_profiler.disable()

    def record_selection(self, **kwargs):
        """Record a selection event."""
        self.selection_profiler.record_selection(**kwargs)

    def record_instantiation(self, **kwargs):
        """Record an instantiation event."""
        self.instantiation_profiler.record_instantiation(**kwargs)

    def get_selection_samples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent selection samples."""
        return self.selection_profiler.get_samples(limit)

    def get_instantiation_samples(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent instantiation samples."""
        return self.instantiation_profiler.get_samples(limit)

    def clear_all(self):
        """Clear all telemetry data."""
        self.selection_profiler.clear()
        self.instantiation_profiler.clear()


__all__ = [
    "RingBuffer",
    "SelectionProfiler",
    "InstantiationProfiler",
    "TelemetryManager",
]
