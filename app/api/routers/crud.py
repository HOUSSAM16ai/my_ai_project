# app/api/routers/crud.py
"""
CRUD Router - Generic Data Operations
Provides standardized CRUD endpoints for resources.
Handles pagination, filtering, and sorting.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.services.boundaries.crud_boundary_service import CrudBoundaryService

router = APIRouter(tags=["CRUD"])


def get_crud_service() -> CrudBoundaryService:
    """Dependency to get the CRUD Boundary Service."""
    return CrudBoundaryService()


@router.get("/resources/{resource_type}", summary="List Resources")
async def list_resources(
    resource_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    order: Optional[str] = Query("asc", description="Sort order (asc/desc)"),
    search: Optional[str] = Query(None, description="Search query"),
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    List all resources of a specific type with pagination and filtering.
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
    Create a new resource.
    """
    return await service.create_item(resource_type, payload)


@router.get("/resources/{resource_type}/{item_id}", summary="Get Resource")
async def get_resource(
    resource_type: str,
    item_id: str,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    Get a specific resource by ID.
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
    Update an existing resource.
    """
    return await service.update_item(resource_type, item_id, payload)


@router.delete("/resources/{resource_type}/{item_id}", summary="Delete Resource")
async def delete_resource(
    resource_type: str,
    item_id: str,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """
    Delete a resource.
    """
    return await service.delete_item(resource_type, item_id)
