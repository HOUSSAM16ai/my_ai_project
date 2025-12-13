import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.aiops_self_healing_service import MetricType
from app.services.data_mesh_service import DataDomainType, SchemaCompatibility
from app.services.platform_boundary_service import (
    PlatformBoundaryService,
    get_platform_boundary_service,
)

router = APIRouter(
    prefix="/api/v1/platform",
    tags=["Intelligent Platform"],
)


# --- Pydantic Models for Request Bodies (DTOs) ---


class CreateDataContractRequest(BaseModel):
    domain: DataDomainType
    name: str
    description: str
    schema_version: str
    schema_definition: dict[str, Any]
    compatibility_mode: SchemaCompatibility = SchemaCompatibility.BACKWARD
    owners: list[str] = Field(default_factory=list)
    consumers: list[str] = Field(default_factory=list)
    sla_guarantees: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectTelemetryRequest(BaseModel):
    service_name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    unit: str = ""
    timestamp: datetime | None = None


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


@router.post("/data-mesh/contracts")
async def create_data_contract(
    request: CreateDataContractRequest,
    service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Create data contract.
    Refactored: Delegates DTO mapping and creation to PlatformBoundaryService.
    """
    result = await service.create_data_contract(
        domain=request.domain,
        name=request.name,
        description=request.description,
        schema_version=request.schema_version,
        schema_definition=request.schema_definition,
        compatibility_mode=request.compatibility_mode,
        owners=request.owners,
        consumers=request.consumers,
        sla_guarantees=request.sla_guarantees,
        metadata=request.metadata,
    )
    return {"ok": result}


@router.post("/aiops/telemetry")
async def collect_telemetry(
    request: CollectTelemetryRequest,
    service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Collect telemetry.
    Refactored: Delegates logic to PlatformBoundaryService.
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


# Note: Metric endpoints have been moved to app/api/routers/observability.py
# for better Separation of Concerns.
