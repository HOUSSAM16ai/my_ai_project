"""
CRUD API endpoints for CogniForge platform.
Refactored to use 'CrudBoundaryService' with Pydantic Schemas.
Implements Strict Type Safety and Governance.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import AsyncSession, get_db
from app.schemas.management import (
    MissionResponse,
    PaginatedResponse,
    TaskResponse,
    UserResponse,
)
from app.services.crud_boundary_service import CrudBoundaryService

router = APIRouter(tags=["CRUD"])


def get_crud_service(db: AsyncSession = Depends(get_db)) -> CrudBoundaryService:
    """Dependency to get the CRUD Boundary Service."""
    return CrudBoundaryService(db)


@router.get("/health")
async def health() -> dict[str, Any]:
    """
    Health check for API v1.
    Maintained for backward compatibility.
    """
    return {
        "status": "success",
        "message": "API v1 is healthy",
        "data": {"status": "healthy", "version": "v3.0-hyper", "database": "connected"},
    }


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def get_users(
    page: int = 1,
    per_page: int = 20,
    email: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    service: CrudBoundaryService = Depends(get_crud_service),
) -> PaginatedResponse[UserResponse]:
    """
    Get users with pagination and filtering.
    Returns typed PaginatedResponse.
    """
    return await service.get_users(
        page=page,
        per_page=per_page,
        email=email,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> UserResponse:
    """Get a single user by ID."""
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/missions", response_model=list[MissionResponse])
async def get_missions(
    status: str | None = None,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> list[MissionResponse]:
    """Get missions with optional status filter."""
    return await service.get_missions(status=status)


@router.get("/missions/{mission_id}", response_model=MissionResponse)
async def get_mission(
    mission_id: int,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> MissionResponse:
    """Get a single mission by ID."""
    mission = await service.get_mission_by_id(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.get("/tasks", response_model=list[TaskResponse])
async def get_tasks(
    mission_id: int | None = None,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> list[TaskResponse]:
    """Get tasks with optional mission filter."""
    return await service.get_tasks(mission_id=mission_id)
