# app/api/routers/data_mesh.py
"""
Data Mesh Router - Data Contract Management
Provides endpoints for data mesh operations and metrics.
Follows Clean Architecture by using Boundary Services.
"""

from fastapi import APIRouter, Depends

from app.api.schemas.data_mesh import (
    DataContractRequest,
    DataContractResponse,
    DataMeshMetricsResponse,
)
from app.services.data_mesh.service import DataMeshBoundaryService

router = APIRouter(tags=["Data Mesh"])


def get_data_mesh_service() -> DataMeshBoundaryService:
    """Dependency to get the Data Mesh Boundary Service."""
    return DataMeshBoundaryService()


@router.post(
    "/contracts",
    summary="Create Data Contract",
    response_model=DataContractResponse,
)
async def create_data_contract(
    contract: DataContractRequest,
    service: DataMeshBoundaryService = Depends(get_data_mesh_service),
) -> DataContractResponse:
    """
    Register a new Data Contract within the Data Mesh.
    Delegates to DataMeshBoundaryService.
    """
    result = await service.create_data_contract(contract.model_dump())
    return DataContractResponse.model_validate(result)


@router.get(
    "/metrics",
    summary="Get Data Mesh Metrics",
    response_model=DataMeshMetricsResponse,
)
async def get_data_mesh_metrics(
    service: DataMeshBoundaryService = Depends(get_data_mesh_service),
) -> DataMeshMetricsResponse:
    """
    Retrieve operational metrics for the Data Mesh.
    Delegates to DataMeshBoundaryService.
    """
    result = await service.get_mesh_metrics()
    return DataMeshMetricsResponse.model_validate(result)
