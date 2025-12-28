# app/api/routers/observability.py
"""
Observability Router - System Health and Metrics
Provides endpoints for system observability and monitoring.
Follows Clean Architecture by using Boundary Services.
"""
from fastapi import APIRouter, Depends

from app.api.schemas.observability import (
    AIOpsMetricsResponse,
    AlertResponse,
    EndpointAnalyticsResponse,
    GitOpsMetricsResponse,
    GoldenSignalsResponse,
    HealthResponse,
    PerformanceSnapshotResponse,
)
from app.services.boundaries.observability_boundary_service import ObservabilityBoundaryService

router = APIRouter(tags=["Observability"])


def get_observability_service() -> ObservabilityBoundaryService:
    """Dependency to get the Observability Boundary Service."""
    return ObservabilityBoundaryService()


@router.get(
    "/health",
    summary="System Health Check",
    response_model=HealthResponse,
)
async def health_check(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
) -> HealthResponse:
    """
    Get the overall system health status.
    Delegates to ObservabilityBoundaryService.
    """
    result = await service.get_system_health()
    return HealthResponse.model_validate(result)


@router.get(
    "/metrics",
    summary="Get Golden Signals",
    response_model=GoldenSignalsResponse,
)
async def get_metrics(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
) -> GoldenSignalsResponse:
    """
    Get SRE Golden Signals (Latency, Traffic, Errors, Saturation).
    """
    result = await service.get_golden_signals()
    return GoldenSignalsResponse.model_validate(result)


@router.get(
    "/aiops",
    summary="Get AIOps Metrics",
    response_model=AIOpsMetricsResponse,
)
async def get_aiops_metrics(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
) -> AIOpsMetricsResponse:
    """
    Get AIOps anomaly detection and self-healing metrics.
    """
    result = await service.get_aiops_metrics()
    return AIOpsMetricsResponse.model_validate(result)


@router.get(
    "/gitops",
    summary="Get GitOps Status",
    response_model=GitOpsMetricsResponse,
)
async def get_gitops_metrics() -> GitOpsMetricsResponse:
    """
    Get GitOps synchronization status.
    Note: Currently a placeholder awaiting GitOps Service integration.
    """
    # Placeholder for GitOps metrics
    return GitOpsMetricsResponse(status="gitops_active", sync_rate=100)


@router.get(
    "/performance",
    summary="Get Performance Snapshot",
    response_model=PerformanceSnapshotResponse,
)
async def get_performance_snapshot(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
) -> PerformanceSnapshotResponse:
    """
    Get detailed performance statistics for the runtime.
    """
    result = await service.get_performance_snapshot()
    return PerformanceSnapshotResponse.model_validate(result)


@router.get(
    "/analytics/{path:path}",
    summary="Get Endpoint Analytics",
    response_model=EndpointAnalyticsResponse,
)
async def get_endpoint_analytics(
    path: str,
    service: ObservabilityBoundaryService = Depends(get_observability_service),
) -> EndpointAnalyticsResponse:
    """
    Get trace analytics for a specific API path.
    """
    result = await service.get_endpoint_analytics(path)
    return EndpointAnalyticsResponse.model_validate(result)


@router.get(
    "/alerts",
    summary="Get Active Alerts",
    response_model=list[AlertResponse],
)
async def get_alerts(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
) -> list[AlertResponse]:
    """
    Get currently active anomaly alerts.
    """
    results = await service.get_active_alerts()
    return [AlertResponse.model_validate(r) for r in results]
