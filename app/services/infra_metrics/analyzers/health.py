from app.services.infra_metrics.domain.models import (
    CPUMetrics,
    DiskMetrics,
    HealthStatus,
    MemoryMetrics,
)


class HealthAnalyzer:
    """Analyzes system metrics to determine health status"""

    @staticmethod
    def determine_health_status(
        cpu: CPUMetrics, memory: MemoryMetrics, disk: DiskMetrics
    ) -> HealthStatus:
        """Determine overall system health status"""
        # Critical thresholds
        if cpu.usage_percent > 95 or memory.used_percent > 95 or disk.used_percent > 95:
            return HealthStatus.CRITICAL

        # Degraded thresholds
        if cpu.usage_percent > 80 or memory.used_percent > 80 or disk.used_percent > 80:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY
