"""
Health Monitor - Application Service
"""

from datetime import UTC, datetime

from ..domain.models import HealthStatus
from ..domain.ports import IHealthMonitor as IHealthMonitorPort


class HealthMonitor:
    """Monitors system health"""

    def __init__(self, monitor: IHealthMonitorPort):
        self._monitor = monitor

    def check_component_health(self, component: str) -> HealthStatus:
        """Check health of a specific component"""
        return self._monitor.check_health(component)

    def get_overall_health(self) -> dict:
        """Get overall system health"""
        statuses = self._monitor.get_all_health_statuses()
        healthy_count = sum(1 for s in statuses.values() if s.healthy)
        total_count = len(statuses)

        return {
            "healthy": healthy_count == total_count,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "components": {name: status.healthy for name, status in statuses.items()},
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_unhealthy_components(self) -> list[HealthStatus]:
        """Get list of unhealthy components"""
        statuses = self._monitor.get_all_health_statuses()
        return [s for s in statuses.values() if not s.healthy]
