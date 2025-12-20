"""
Observability

هذا الملف جزء من مشروع CogniForge.
"""

# app/api/routers/observability.py
"""
Observability Router - System Health and Metrics
Provides endpoints for system observability and monitoring.
Follows Clean Architecture by using Boundary Services.
"""
from fastapi import APIRouter, Depends

from app.services.observability_boundary_service import ObservabilityBoundaryService

router = APIRouter(tags=["Observability"])


def get_observability_service() -> ObservabilityBoundaryService:
    """Dependency to get the Observability Boundary Service."""
    return ObservabilityBoundaryService()


@router.get("/health", summary="System Health Check")
async def health_check(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
):
    """
    Get the overall system health status.
    Delegates to ObservabilityBoundaryService.
    """
    return await service.get_system_health()


@router.get("/metrics", summary="Get Golden Signals")
async def get_metrics(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
):
    """
    Get SRE Golden Signals (Latency, Traffic, Errors, Saturation).
    """
    return await service.get_golden_signals()


@router.get("/aiops", summary="Get AIOps Metrics")
async def get_aiops_metrics(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
):
    """
    Get AIOps anomaly detection and self-healing metrics.
    """
    return await service.get_aiops_metrics()


@router.get("/gitops", summary="Get GitOps Status")
async def get_gitops_metrics():
    """
    Get GitOps synchronization status.
    Note: Currently a placeholder awaiting GitOps Service integration.
    """
    # Placeholder for GitOps metrics
    return {"status": "gitops_active", "sync_rate": 100}


@router.get("/performance", summary="Get Performance Snapshot")
async def get_performance_snapshot(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
):
    """
    Get detailed performance statistics for the runtime.
    """
    return await service.get_performance_snapshot()


@router.get("/analytics/{path:path}", summary="Get Endpoint Analytics")
async def get_endpoint_analytics(
    path: str,
    service: ObservabilityBoundaryService = Depends(get_observability_service),
):
    """
    Get trace analytics for a specific API path.
    """
    return await service.get_endpoint_analytics(path)


@router.get("/alerts", summary="Get Active Alerts")
async def get_alerts(
    service: ObservabilityBoundaryService = Depends(get_observability_service),
):
    """
    Get currently active anomaly alerts.
    """
    return await service.get_active_alerts()
