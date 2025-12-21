# app/api/routers/crud.py
"""
CRUD Router - عمليات البيانات العامة
--------------------------------------
يوفر هذا الموجه (Router) نقاط نهاية موحدة للعمليات الأساسية (CRUD) للموارد.
يعتمد على `CrudBoundaryService` لتنفيذ المنطق، مما يضمن فصل طبقة العرض عن طبقة البيانات.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.boundaries.crud_boundary_service import CrudBoundaryService

router = APIRouter(tags=["CRUD"])


def get_crud_service(db: AsyncSession = Depends(get_db)) -> CrudBoundaryService:
    """Dependency to get the CRUD Boundary Service."""
    return CrudBoundaryService(db)


@router.get("/resources/{resource_type}", summary="List Resources")
async def list_resources(
    resource_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str | None = Query(None, description="Field to sort by"),
    order: str | None = Query("asc", description="Sort order (asc/desc)"),
    search: str | None = Query(None, description="Search query"),
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    عرض قائمة الموارد لنوع محدد مع دعم التصفح (Pagination) والترشيح (Filtering).
    """
    filters = {}
    if search:
        filters["search"] = search

    return await service.list_items(
        resource_type,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        filters=filters
    )


@router.post("/resources/{resource_type}", summary="Create Resource")
async def create_resource(
    resource_type: str,
    payload: dict[str, Any],
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    إنشاء مورد جديد من نوع محدد.
    """
    return await service.create_item(resource_type, payload)


@router.get("/resources/{resource_type}/{item_id}", summary="Get Resource")
async def get_resource(
    resource_type: str,
    item_id: str,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    جلب مورد محدد بواسطة المعرف.
    """
    return await service.get_item(resource_type, item_id)


@router.put("/resources/{resource_type}/{item_id}", summary="Update Resource")
async def update_resource(
    resource_type: str,
    item_id: str,
    payload: dict[str, Any],
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    تحديث مورد موجود.
    """
    return await service.update_item(resource_type, item_id, payload)


@router.delete("/resources/{resource_type}/{item_id}", summary="Delete Resource")
async def delete_resource(
    resource_type: str,
    item_id: str,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    حذف مورد محدد.
    """
    return await service.delete_item(resource_type, item_id)
