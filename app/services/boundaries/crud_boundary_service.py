"""
CRUD Boundary Service
Acts as a facade for CRUD operations, orchestrating business logic.
Refactored to return strongly-typed Pydantic models for Governance and Maintainability.
"""

from __future__ import annotations

import logging
from math import ceil
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.management import (
    MissionResponse,
    PaginatedResponse,
    PaginationMeta,
    TaskResponse,
    UserResponse,
)
from app.services.crud.crud_persistence import CrudPersistence

logger = logging.getLogger(__name__)

# Allowed sort columns per resource to prevent SQL Injection
ALLOWED_SORT_COLUMNS = {
    "users": {"id", "email", "full_name", "created_at", "is_active", "is_admin"},
    "missions": {"id", "name", "status", "created_at"},
    "tasks": {"id", "mission_id", "status", "created_at"},
}


class CrudBoundaryService:
    """
    Boundary Service for CRUD operations.
    Orchestrates business logic and delegates data access to CrudPersistence.
    Enforces Type Safety via Pydantic Models.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.persistence = CrudPersistence(db)

    async def get_users(
        self,
        page: int = 1,
        per_page: int = 20,
        email: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> PaginatedResponse[UserResponse]:
        """
        Retrieve users with pagination and filtering.
        """
        self._validate_sort("users", sort_by)

        # Get raw data from persistence
        raw_data = await self.persistence.get_users(
            page=page,
            per_page=per_page,
            email=email,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Adapt raw dict to Pydantic
        items = [UserResponse.model_validate(u) for u in raw_data.get("items", [])]
        total = raw_data.get("total", 0)
        total_pages = ceil(total / per_page) if per_page > 0 else 0

        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return PaginatedResponse(items=items, pagination=pagination)

    async def get_user_by_id(self, user_id: int) -> UserResponse | None:
        """
        Retrieve a single user by ID.
        """
        user = await self.persistence.get_user_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def get_missions(self, status: str | None = None) -> list[MissionResponse]:
        """
        Retrieve missions with optional status filter.
        """
        missions = await self.persistence.get_missions(status=status)
        return [MissionResponse.model_validate(m) for m in missions]

    async def get_mission_by_id(self, mission_id: int) -> MissionResponse | None:
        """
        Retrieve a single mission by ID.
        """
        mission = await self.persistence.get_mission_by_id(mission_id)
        if not mission:
            return None
        return MissionResponse.model_validate(mission)

    async def get_tasks(self, mission_id: int | None = None) -> list[TaskResponse]:
        """
        Retrieve tasks with optional mission filter.
        """
        tasks = await self.persistence.get_tasks(mission_id=mission_id)
        return [TaskResponse.model_validate(t) for t in tasks]

    async def list_items(
        self,
        resource_type: str,
        page: int = 1,
        per_page: int = 20,
        sort_by: str | None = None,
        order: str = "asc",
        filters: dict[str, Any] | None = None,
    ) -> PaginatedResponse[Any]:
        """
        Generic list items method to support generic CRUD router.
        Maps resource_type to specific method call.
        """
        self._validate_sort(resource_type, sort_by)

        if resource_type == "users":
            # Map filters['search'] to email search if possible or ignore
            email_filter = None
            if filters and "search" in filters:
                # Naive assumption: search string is email
                email_filter = filters["search"]

            return await self.get_users(
                page=page,
                per_page=per_page,
                email=email_filter,
                sort_by=sort_by,
                sort_order=order,
            )

        # Fallback or error for unknown resources
        raise ValueError(f"Unknown resource type: {resource_type}")

    async def get_item(self, resource_type: str, item_id: str) -> Any | None:
        """
        Generic get item method.
        """
        if resource_type == "users":
            try:
                uid = int(item_id)
                return await self.get_user_by_id(uid)
            except ValueError:
                return None
        return None

    async def create_item(
        self, resource_type: str, payload: dict[str, Any]
    ) -> dict[str, str | int | bool]:
        """Generic create item stub."""
        # Implement actual creation logic mapping
        return {"status": "created", "resource": resource_type}

    async def update_item(
        self, resource_type: str, item_id: str, payload: dict[str, Any]
    ) -> dict[str, str | int | bool]:
        """Generic update item stub."""
        return {"status": "updated", "resource": resource_type}

    async def delete_item(
        self, resource_type: str, item_id: str
    ) -> dict[str, str | int | bool]:
        """Generic delete item stub."""
        return {"status": "deleted", "resource": resource_type}

    def _validate_sort(self, resource_type: str, sort_by: str | None) -> None:
        """
        Validates the sort_by column against an allowed list to prevent SQL Injection.
        """
        if not sort_by:
            return

        allowed = ALLOWED_SORT_COLUMNS.get(resource_type)
        if allowed is None:
            # If resource definition is missing but method called, default to safe fail
            # or allow nothing.
            logger.warning(f"No sort whitelist for resource: {resource_type}")
            return

        if sort_by not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort column '{sort_by}' for resource '{resource_type}'"
            )
