# app/api/routers/observability.py
import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.observability import (
    AiOpsResponse,
    AlertsResponse,
    EndpointAnalyticsData,
    HealthCheckData,
    LegacyResponse,
    MetricsData,
    MetricsResponse,
    PerformanceSnapshotModel,
    SnapshotResponse,
)
from app.services.platform_boundary_service import (
    PlatformBoundaryService,
    get_platform_boundary_service,
)

router = APIRouter(prefix="/api/observability", tags=["Observability"])
logger = logging.getLogger(__name__)


@router.get("/health", summary="System Health Check", response_model=LegacyResponse[HealthCheckData])
async def health_check():
    """
    Basic health check for the observability subsystem.
    Refactored to use LegacyResponse[HealthCheckData] for type safety and backward compatibility.
    """
    return LegacyResponse(
        status="success",
        data=HealthCheckData(status="healthy")
    )


@router.get("/metrics", summary="Unified System Metrics", response_model=MetricsResponse)
async def get_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Aggregated metrics from all subsystems (AIOps, API Performance).
    Now served via the Platform Boundary Service with strict Pydantic Response.
    Matches the legacy format: { "status": "success", "timestamp": ..., "metrics": { ... } }
    """
    snapshot = await platform_service.get_performance_snapshot()
    aiops_health = platform_service.aiops.get_aiops_metrics()

    # Convert dataclass to Pydantic model
    snapshot_model = PerformanceSnapshotModel(**asdict(snapshot))

    return MetricsResponse(
        status="success",
        timestamp=snapshot.timestamp,
        metrics=MetricsData(
            api_performance=snapshot_model,
            aiops_health=aiops_health,
        ),
    )


@router.get("/metrics/aiops", summary="AIOps Specific Metrics", response_model=AiOpsResponse)
async def get_aiops_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get detailed AIOps metrics (Anomalies, Healing Actions).
    Uses AiOpsResponse to preserve {"ok": True, "data": ...} structure.
    """
    metrics = platform_service.aiops.get_aiops_metrics()
    return AiOpsResponse(
        ok=True,
        data=metrics
    )


@router.get("/metrics/datamesh", summary="Data Mesh Metrics", response_model=AiOpsResponse)
async def get_data_mesh_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get Data Mesh metrics.
    Uses AiOpsResponse format (ok/data) for consistency with other sub-metric endpoints if they shared format.
    (Review said this used ok: True in previous implementation)
    """
    metrics = platform_service.data_mesh.get_mesh_metrics()
    return AiOpsResponse(ok=True, data=metrics)


@router.get("/metrics/gitops", summary="GitOps Metrics", response_model=AiOpsResponse)
async def get_gitops_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get GitOps metrics.
    Uses AiOpsResponse format (ok/data).
    """
    metrics = platform_service.gitops.get_gitops_metrics()
    return AiOpsResponse(ok=True, data=metrics)


@router.get("/performance/snapshot", summary="API Performance Snapshot", response_model=SnapshotResponse)
async def get_performance_snapshot(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get current API performance snapshot including P99 latency.
    Uses SnapshotResponse to preserve {"status": "success", "snapshot": ...} structure.
    """
    snapshot = await platform_service.get_performance_snapshot()
    snapshot_model = PerformanceSnapshotModel(**asdict(snapshot))

    return SnapshotResponse(
        status="success",
        snapshot=snapshot_model
    )


@router.get("/performance/endpoint/{path:path}", summary="Endpoint Analytics", response_model=EndpointAnalyticsData)
async def get_endpoint_analytics(
    path: str,
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get detailed analytics for a specific endpoint.
    """
    if not path.startswith("/"):
        path = "/" + path

    data = await platform_service.get_endpoint_analytics(path)
    if data.get("status") == "no_data":
        raise HTTPException(status_code=404, detail="No metrics found for this endpoint")

    # data is a dict that matches EndpointAnalyticsData structure
    return data


@router.get("/alerts", summary="System Alerts", response_model=AlertsResponse)
async def get_alerts(
    severity: str | None = None,
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get active system alerts (Anomalies, SLA Violations).
    Uses AlertsResponse to preserve {"status": "success", "alerts": ...} structure.
    """
    alerts = await platform_service.get_system_alerts(severity)
    return AlertsResponse(
        status="success",
        alerts=alerts
    )
