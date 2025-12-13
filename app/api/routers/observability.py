# app/api/routers/observability.py
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.services.platform_boundary_service import (
    PlatformBoundaryService,
    get_platform_boundary_service,
)

router = APIRouter(prefix="/api/observability", tags=["Observability"])
logger = logging.getLogger(__name__)


@router.get("/health", summary="System Health Check")
async def health_check():
    """
    Basic health check for the observability subsystem.
    """
    return {"status": "success", "data": {"status": "healthy"}}


@router.get("/metrics", summary="Unified System Metrics")
async def get_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Aggregated metrics from all subsystems (AIOps, API Performance).
    Now served via the Platform Boundary Service.

    OPTIMIZATION: Calls specific sub-services via the boundary to avoid
    calculating the full platform overview (which includes heavy operations).
    """
    # Fetch only what we need for this specific endpoint to avoid over-fetching
    snapshot = await platform_service.get_performance_snapshot()
    aiops_health = platform_service.aiops.get_aiops_metrics()

    return {
        "status": "success",
        "timestamp": snapshot.timestamp,
        "metrics": {
            "api_performance": snapshot,
            "aiops_health": aiops_health,
        },
    }


@router.get("/metrics/aiops", summary="AIOps Specific Metrics")
async def get_aiops_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get detailed AIOps metrics (Anomalies, Healing Actions).
    Delegates to Platform Boundary.
    """
    metrics = platform_service.aiops.get_aiops_metrics()
    return {"ok": True, "data": metrics}


@router.get("/metrics/datamesh", summary="Data Mesh Metrics")
async def get_data_mesh_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get Data Mesh metrics.
    Delegates to Platform Boundary.
    """
    metrics = platform_service.data_mesh.get_mesh_metrics()
    return {"ok": True, "data": metrics}


@router.get("/metrics/gitops", summary="GitOps Metrics")
async def get_gitops_metrics(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get GitOps metrics.
    Delegates to Platform Boundary.
    """
    metrics = platform_service.gitops.get_gitops_metrics()
    return {"ok": True, "data": metrics}


@router.get("/performance/snapshot", summary="API Performance Snapshot")
async def get_performance_snapshot(
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get current API performance snapshot including P99 latency.
    Delegates to Platform Boundary.
    """
    snapshot = await platform_service.get_performance_snapshot()
    return {"status": "success", "snapshot": snapshot}


@router.get("/performance/endpoint/{path:path}", summary="Endpoint Analytics")
async def get_endpoint_analytics(
    path: str,
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get detailed analytics for a specific endpoint.
    Delegates to Platform Boundary.
    """
    if not path.startswith("/"):
        path = "/" + path

    data = await platform_service.get_endpoint_analytics(path)
    if data["status"] == "no_data":
        raise HTTPException(status_code=404, detail="No metrics found for this endpoint")
    return data


@router.get("/alerts", summary="System Alerts")
async def get_alerts(
    severity: str | None = None,
    platform_service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get active system alerts (Anomalies, SLA Violations).
    Delegates to Platform Boundary.
    """
    alerts = await platform_service.get_system_alerts(severity)
    return {"status": "success", "alerts": alerts}
