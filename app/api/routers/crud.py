# app/api/routers/crud.py
"""
CRUD Router - عمليات البيانات العامة
--------------------------------------
يوفر هذا الموجه (Router) نقاط نهاية موحدة للعمليات الأساسية (CRUD) للموارد.
يعتمد على `CrudBoundaryService` لتنفيذ المنطق، مما يضمن فصل طبقة العرض عن طبقة البيانات.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.crud import GenericResourceResponse, PaginatedResponse
from app.core.database import get_db
from app.services.boundaries.crud_boundary_service import CrudBoundaryService
from app.schemas.management import PaginatedResponse as BoundaryPaginatedResponse

router = APIRouter(tags=["CRUD"])


def _to_api_paginated_response(
    boundary_result: BoundaryPaginatedResponse,
) -> PaginatedResponse[GenericResourceResponse]:
    """
    يحول استجابة التقسيم إلى الصفحات من طبقة الحدود إلى نموذج الـ API الموحد.

    يضمن هذا التحويل توافق مفاتيح الحقول مع توقعات الواجهة العامة، بحيث تبقى
    الحقول `total`, `page`, `per_page`, `pages` متوفرة مع عناصر محسَّنة باستخدام
    `GenericResourceResponse` لضمان مرونة الحقول الإضافية.
    """

    pagination = boundary_result.pagination
    items = [GenericResourceResponse.model_validate(item) for item in boundary_result.items]

    return PaginatedResponse[GenericResourceResponse](
        items=items,
        total=pagination.total_items,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pagination.total_pages,
    )


def get_crud_service(db: AsyncSession = Depends(get_db)) -> CrudBoundaryService:
    """يوفر تبعية حقن لخدمة CRUD الحدية باستخدام جلسة قاعدة البيانات غير المتزامنة."""
    return CrudBoundaryService(db)

@router.get(
    "/resources/{resource_type}",
    summary="List Resources",
    response_model=PaginatedResponse[GenericResourceResponse],
)
async def list_resources(
    resource_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str | None = Query(None, description="Field to sort by"),
    order: str | None = Query("asc", description="Sort order (asc/desc)"),
    search: str | None = Query(None, description="Search query"),
    service: CrudBoundaryService = Depends(get_crud_service),
) -> PaginatedResponse[GenericResourceResponse]:
    """
    عرض قائمة الموارد لنوع محدد مع دعم التصفح (Pagination) والترشيح (Filtering).
    """
    filters = {}
    if search:
        filters["search"] = search

    result = await service.list_items(
        resource_type,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        filters=filters
    )
    # Ensure result matches the PaginatedResponse structure
    if isinstance(result, BoundaryPaginatedResponse):
        return _to_api_paginated_response(result)

    return PaginatedResponse[GenericResourceResponse].model_validate(result)

@router.post(
    "/resources/{resource_type}",
    summary="Create Resource",
    response_model=GenericResourceResponse,
)
async def create_resource(
    resource_type: str,
    payload: dict[str, object],
    service: CrudBoundaryService = Depends(get_crud_service),
) -> GenericResourceResponse:
    """
    إنشاء مورد جديد من نوع محدد.
    """
    result = await service.create_item(resource_type, payload)
    return GenericResourceResponse.model_validate(result)

@router.get(
    "/resources/{resource_type}/{item_id}",
    summary="Get Resource",
    response_model=GenericResourceResponse,
)
async def get_resource(
    resource_type: str,
    item_id: str,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> GenericResourceResponse:
    """
    جلب مورد محدد بواسطة المعرف.
    """
    result = await service.get_item(resource_type, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="المورد غير موجود")

    return GenericResourceResponse.model_validate(result)

@router.put(
    "/resources/{resource_type}/{item_id}",
    summary="Update Resource",
    response_model=GenericResourceResponse,
)
async def update_resource(
    resource_type: str,
    item_id: str,
    payload: dict[str, object],
    service: CrudBoundaryService = Depends(get_crud_service),
) -> GenericResourceResponse:
    """
    تحديث مورد موجود.
    """
    result = await service.update_item(resource_type, item_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="المورد غير موجود")

    return GenericResourceResponse.model_validate(result)

@router.delete(
    "/resources/{resource_type}/{item_id}",
    summary="Delete Resource",
    response_model=GenericResourceResponse,
)
async def delete_resource(
    resource_type: str,
    item_id: str,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> GenericResourceResponse:
    """
    حذف مورد محدد.
    """
    result = await service.delete_item(resource_type, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="المورد غير موجود")

    return GenericResourceResponse.model_validate(result)
