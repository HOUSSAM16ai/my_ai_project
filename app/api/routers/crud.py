"""
CRUD API endpoints for CogniForge platform.
Refactored to use 'CrudBoundaryService' with Pydantic Schemas for Strict Separation of Concerns.
This module acts as a pure Routing Layer, delegating all business logic to the Boundary Service.
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
    """
    Dependency Injection for CrudBoundaryService.
    Ensures that the service is initialized with a valid database session.

    Args:
        db (AsyncSession): The SQLAlchemy async session.

    Returns:
        CrudBoundaryService: An initialized instance of the service.
    """
    return CrudBoundaryService(db)


@router.get("/health", summary="API v1 Health Check")
async def health() -> dict[str, Any]:
    """
    Performs a lightweight health check for the API v1 subsystem.
    Maintained for backward compatibility with legacy monitoring tools.

    Returns:
        dict: Status information including version and database connectivity flag.
    """
    return {
        "status": "success",
        "message": "API v1 is healthy",
        "data": {"status": "healthy", "version": "v3.0-hyper", "database": "connected"},
    }


@router.get("/users", response_model=PaginatedResponse[UserResponse], summary="List Users with Pagination")
async def get_users(
    page: int = 1,
    per_page: int = 20,
    email: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    service: CrudBoundaryService = Depends(get_crud_service),
) -> PaginatedResponse[UserResponse]:
    """
    Retrieves a paginated list of users, with optional filtering and sorting.
    Delegates retrieval logic to CrudBoundaryService.

    Args:
        page (int): Page number (1-based).
        per_page (int): Number of items per page.
        email (str, optional): Filter by email address (partial match).
        sort_by (str, optional): Field to sort by.
        sort_order (str): 'asc' or 'desc'.
        service (CrudBoundaryService): The injected service instance.

    Returns:
        PaginatedResponse[UserResponse]: A structured response containing the list of users and pagination metadata.
    """
    return await service.get_users(
        page=page,
        per_page=per_page,
        email=email,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get User Details")
async def get_user(
    user_id: int,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> UserResponse:
    """
    Retrieves detailed information for a specific user by ID.

    Args:
        user_id (int): The unique identifier of the user.
        service (CrudBoundaryService): The injected service instance.

    Raises:
        HTTPException(404): If the user is not found.

    Returns:
        UserResponse: The user's profile data.
    """
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/missions", response_model=list[MissionResponse], summary="List Missions")
async def get_missions(
    status: str | None = None,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> list[MissionResponse]:
    """
    Retrieves a list of missions, optionally filtered by status.

    Args:
        status (str, optional): The status to filter by (e.g., 'pending', 'completed').
        service (CrudBoundaryService): The injected service instance.

    Returns:
        list[MissionResponse]: A list of mission objects.
    """
    return await service.get_missions(status=status)


@router.get("/missions/{mission_id}", response_model=MissionResponse, summary="Get Mission Details")
async def get_mission(
    mission_id: int,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> MissionResponse:
    """
    Retrieves detailed information for a specific mission by ID.

    Args:
        mission_id (int): The unique identifier of the mission.
        service (CrudBoundaryService): The injected service instance.

    Raises:
        HTTPException(404): If the mission is not found.

    Returns:
        MissionResponse: The mission's details.
    """
    mission = await service.get_mission_by_id(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.get("/tasks", response_model=list[TaskResponse], summary="List Tasks")
async def get_tasks(
    mission_id: int | None = None,
    service: CrudBoundaryService = Depends(get_crud_service),
) -> list[TaskResponse]:
    """
    Retrieves a list of tasks, optionally filtered by mission ID.

    Args:
        mission_id (int, optional): The ID of the mission to filter tasks by.
        service (CrudBoundaryService): The injected service instance.

    Returns:
        list[TaskResponse]: A list of task objects.
    """
    return await service.get_tasks(mission_id=mission_id)
