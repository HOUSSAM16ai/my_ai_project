# app/api/routers/observability.py
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.services.aiops_self_healing_service import AIOpsService, get_aiops_service
from app.services.api_observability_service import (
    APIObservabilityService,
    get_observability_service,
)
from app.services.data_mesh_service import DataMeshService, get_data_mesh_service
from app.services.gitops_policy_service import GitOpsPolicyService, get_gitops_policy_service

# For Dependency Injection type hinting
from app.services.gitops_policy.facade import GitOpsPolicyServiceFacade

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
    aiops_service: AIOpsService = Depends(get_aiops_service),
    observability_service: APIObservabilityService = Depends(get_observability_service),
):
    """
    Aggregated metrics from all subsystems (AIOps, API Performance).
    """
    return {
        "status": "success",
        "timestamp": observability_service.get_performance_snapshot().timestamp,
        "metrics": {
            "api_performance": observability_service.get_performance_snapshot(),
            "aiops_health": aiops_service.get_aiops_metrics(),
        },
    }


@router.get("/metrics/aiops", summary="AIOps Specific Metrics")
async def get_aiops_metrics(
    service: AIOpsService = Depends(get_aiops_service),
):
    """
    Get detailed AIOps metrics (Anomalies, Healing Actions).
    Moved from intelligent_platform.py for better separation of concerns.
    """
    metrics = service.get_aiops_metrics()
    return {"ok": True, "data": metrics}


@router.get("/metrics/datamesh", summary="Data Mesh Metrics")
async def get_data_mesh_metrics(
    service: DataMeshService = Depends(get_data_mesh_service),
):
    """
    Get Data Mesh metrics.
    Moved from intelligent_platform.py.
    """
    metrics = service.get_mesh_metrics()
    return {"ok": True, "data": metrics}


@router.get("/metrics/gitops", summary="GitOps Metrics")
async def get_gitops_metrics(
    service_facade: GitOpsPolicyServiceFacade = Depends(get_gitops_policy_service),
):
    """
    Get GitOps metrics.
    Moved from intelligent_platform.py.
    """
    out_of_sync = service_facade.get_out_of_sync_apps()

    metrics = {
        "out_of_sync_apps": len(out_of_sync),
        "status": "active"
    }

    return {"ok": True, "data": metrics}


@router.get("/performance/snapshot", summary="API Performance Snapshot")
async def get_performance_snapshot(
    service: APIObservabilityService = Depends(get_observability_service),
):
    """
    Get current API performance snapshot including P99 latency.
    """
    return {"status": "success", "snapshot": service.get_performance_snapshot()}


@router.get("/performance/endpoint/{path:path}", summary="Endpoint Analytics")
async def get_endpoint_analytics(
    path: str,
    service: APIObservabilityService = Depends(get_observability_service),
):
    """
    Get detailed analytics for a specific endpoint.
    """
    # Normalize path if needed (e.g., ensure leading slash)
    if not path.startswith("/"):
        path = "/" + path

    data = service.get_endpoint_analytics(path)
    if data["status"] == "no_data":
        raise HTTPException(status_code=404, detail="No metrics found for this endpoint")
    return data


@router.get("/alerts", summary="System Alerts")
async def get_alerts(
    severity: str | None = None,
    service: APIObservabilityService = Depends(get_observability_service),
):
    """
    Get active system alerts (Anomalies, SLA Violations).
    """
    return {"status": "success", "alerts": service.get_all_alerts(severity)}
