# app/api/routers/intelligent_platform.py
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.aiops_self_healing_service import MetricType
from app.services.platform_boundary_service import (
    PlatformBoundaryService,
    get_platform_boundary_service,
)

# Note: The prefix is handled by the Blueprint (api/v1/platform)
router = APIRouter(
    tags=["Intelligent Platform"],
)


# --- Pydantic Models for Request Bodies (DTOs) ---


class CollectTelemetryRequest(BaseModel):
    service_name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    unit: str = ""
    timestamp: Any | None = None  # Using Any to be permissive with datetime input


# --- Endpoints ---


@router.get("/overview")
async def get_platform_overview(
    service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get platform overview.
    Refactored: Delegates aggregation logic to PlatformBoundaryService.
    """
    data = await service.get_platform_overview()
    return {"ok": True, "data": data}


@router.post("/aiops/telemetry")
async def collect_telemetry(
    request: CollectTelemetryRequest,
    service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Collect telemetry.
    Refactored: Delegates logic to PlatformBoundaryService.
    Note: Ideally this should move to an AIOps specific router, but kept here for now
    as part of the Platform API surface until full decomposition.
    """
    await service.collect_telemetry(
        service_name=request.service_name,
        metric_type=request.metric_type,
        value=request.value,
        labels=request.labels,
        unit=request.unit,
        timestamp=request.timestamp,
    )
    return {"ok": True}


# Note: Data Mesh endpoints have been moved to app/api/routers/data_mesh.py
