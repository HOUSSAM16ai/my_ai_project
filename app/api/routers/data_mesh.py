# app/api/routers/data_mesh.py
"""
موجه شبكة البيانات (Data Mesh Router).
---------------------------------------
يوفر نقاط نهاية لإدارة عقود البيانات ومقاييس الشبكة بطريقة معمارية نظيفة
تعتمد بالكامل على خدمات الحدود (Boundary Services) لفصل الطبقات والمنطق.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.data_mesh import (
    DataContractRequest,
    DataContractResponse,
    DataMeshMetricsResponse,
)
from app.services.data_mesh.service import DataMeshBoundaryService

router = APIRouter(tags=["Data Mesh"])

def get_data_mesh_service() -> DataMeshBoundaryService:
    """تبعية للحصول على خدمة شبكة البيانات الحدية (Data Mesh Boundary Service)."""
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
    تسجيل عقد بيانات جديد داخل شبكة البيانات.
    يتم تفويض كل المنطق إلى خدمة الحدود لضمان عزل طبقة العرض.
    """
    try:
        result = await service.create_data_contract(contract.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
    استرجاع المقاييس التشغيلية لشبكة البيانات.
    يتم التفويض لخدمة الحدود لضمان فصل المسؤوليات.
    """
    result = await service.get_mesh_metrics()
    return DataMeshMetricsResponse.model_validate(result)
