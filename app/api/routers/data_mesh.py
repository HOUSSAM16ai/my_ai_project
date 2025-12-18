from typing import Any

from fastapi import APIRouter, Body, Depends

from app.services.data_mesh_service import DataMeshBoundaryService

router = APIRouter()


def get_data_mesh_service() -> DataMeshBoundaryService:
    """Dependency to get the Data Mesh Boundary Service."""
    return DataMeshBoundaryService()


@router.post("/contracts", summary="Create Data Contract")
async def create_data_contract(
    contract: dict[str, Any] = Body(...),
    service: DataMeshBoundaryService = Depends(get_data_mesh_service),
):
    """
    Register a new Data Contract within the Data Mesh.
    Delegates to DataMeshBoundaryService.
    """
    return await service.create_data_contract(contract)


@router.get("/metrics", summary="Get Data Mesh Metrics")
async def get_data_mesh_metrics(service: DataMeshBoundaryService = Depends(get_data_mesh_service)):
    """
    Retrieve operational metrics for the Data Mesh.
    Delegates to DataMeshBoundaryService.
    """
    return await service.get_mesh_metrics()
