# app/api/routers/data_mesh.py
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.data_mesh_service import DataDomainType, SchemaCompatibility
from app.services.platform_boundary_service import (
    PlatformBoundaryService,
    get_platform_boundary_service,
)

# Initialize logger
logger = logging.getLogger(__name__)

# Note: Prefix is handled by the Blueprint weaving mechanism (api/v1/data-mesh)
router = APIRouter(tags=["Data Mesh"])


# --- Pydantic Models ---


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


# --- Endpoints ---


@router.post("/contracts", summary="Create Data Contract")
async def create_data_contract(
    request: CreateDataContractRequest,
    service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Create a new Data Contract in the Data Mesh.
    Uses PlatformBoundaryService to orchestrate the creation.
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
    return {"ok": result, "message": "Data Contract created successfully"}


@router.get("/metrics", summary="Get Data Mesh Metrics")
async def get_data_mesh_metrics(
    service: PlatformBoundaryService = Depends(get_platform_boundary_service),
):
    """
    Get Data Mesh metrics.
    """
    metrics = service.data_mesh.get_mesh_metrics()
    return {"ok": True, "data": metrics}
