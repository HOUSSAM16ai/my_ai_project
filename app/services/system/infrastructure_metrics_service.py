# app/services/infrastructure_metrics_service.py
# ======================================================================================
# ==   INFRASTRUCTURE METRICS SERVICE - TECH GIANTS STANDARD (v1.0 SUPERHUMAN)     ==
# ======================================================================================
# SHIM FILE FOR BACKWARD COMPATIBILITY
# This service has been refactored into a modular structure at app/services/infra_metrics/

from app.services.infra_metrics.application.manager import (
    InfrastructureMetricsService,
    get_infrastructure_service,
)
from app.services.infra_metrics.domain.models import (
    AvailabilityMetrics,
    CPUMetrics,
    DiskMetrics,
    HealthStatus,
    MemoryMetrics,
    NetworkMetrics,
    ProcessMetrics,
    ResourceType,
    SystemHealthSnapshot,
)

# Re-export all public members
__all__ = [
    "ResourceType",
    "HealthStatus",
    "CPUMetrics",
    "MemoryMetrics",
    "DiskMetrics",
    "NetworkMetrics",
    "ProcessMetrics",
    "SystemHealthSnapshot",
    "AvailabilityMetrics",
    "InfrastructureMetricsService",
    "get_infrastructure_service",
]
