"""
Performance Tracker - Application Service
"""

import uuid
from datetime import UTC, datetime

from ..domain.models import PerformanceSnapshot
from ..domain.ports import IPerformanceTracker as IPerformanceTrackerPort


class PerformanceTracker:
    """Tracks system performance"""

    def __init__(self, tracker: IPerformanceTrackerPort):
        self._tracker = tracker

    def capture_snapshot(self, **metrics) -> PerformanceSnapshot:
        """Capture a performance snapshot"""
        snapshot = PerformanceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            **metrics,
        )
        self._tracker.record_snapshot(snapshot)
        return snapshot

    def get_recent_snapshots(self, limit: int = 100) -> list[PerformanceSnapshot]:
        """Get recent performance snapshots"""
        return self._tracker.get_snapshots(limit=limit)

    def get_performance_trends(self) -> dict:
        """Get performance trends"""
        snapshots = self._tracker.get_snapshots(limit=100)
        if not snapshots:
            return {}

        return {
            "avg_deployment_time": sum(s.avg_deployment_time_seconds for s in snapshots)
            / len(snapshots),
            "avg_latency": sum(s.avg_latency_ms for s in snapshots) / len(snapshots),
            "avg_error_rate": sum(s.error_rate for s in snapshots) / len(snapshots),
            "avg_cpu_usage": sum(s.cluster_cpu_usage for s in snapshots) / len(snapshots),
            "avg_memory_usage": sum(s.cluster_memory_usage for s in snapshots)
            / len(snapshots),
        }
