# app/api/routers/crud.py
"""
CRUD API endpoints for CogniForge platform.
Refactored to use 'CrudBoundaryService' for Separation of Concerns.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import AsyncSession, get_db
from app.services.crud_boundary_service import CrudBoundaryService

router = APIRouter(prefix="/api/v1", tags=["CRUD"])


def get_crud_service(db: AsyncSession = Depends(get_db)) -> CrudBoundaryService:
    """Dependency to get the CRUD Boundary Service."""
    return CrudBoundaryService(db)


@router.get("/users")
async def get_users(
    page: int = 1,
    per_page: int = 20,
    email: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """Get users with pagination and filtering."""
    return await service.get_users(
        page=page,
        per_page=per_page,
        email=email,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """Get a single user by ID."""
    result = await service.get_user_by_id(user_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/missions")
async def get_missions(
    status: str | None = None,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """Get missions with optional status filter."""
    return await service.get_missions(status=status)


@router.get("/missions/{mission_id}")
async def get_mission(
    mission_id: int,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """Get a single mission by ID."""
    result = await service.get_mission_by_id(mission_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/tasks")
async def get_tasks(
    mission_id: int | None = None,
    service: CrudBoundaryService = Depends(get_crud_service),
):
    """Get tasks with optional mission filter."""
    return await service.get_tasks(mission_id=mission_id)
