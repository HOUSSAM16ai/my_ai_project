"""
CRUD Boundary Service
Acts as a facade for CRUD operations, orchestrating business logic.
Refactored to return strongly-typed Pydantic models for Governance and Maintainability.
"""

from __future__ import annotations

import logging
from math import ceil

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


class CrudBoundaryService:
    """
    Boundary Service for CRUD operations.
    Orchestrates business logic and delegates data access to CrudPersistence.
    Enforces Type Safety via Pydantic Models.
    """

    def __init__(self, db: AsyncSession):
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
        # Get raw data from persistence (assuming it returns dicts or models)
        # Note: We need to adapt the persistence layer return type if it returns wrapped dicts.
        # Based on previous code, persistence returned a dict with 'items' and 'total'.
        # We will assume persistence returns a tuple (items, total) or similar,
        # but the previous code was unwrapping "data" dicts.
        # Let's inspect persistence output by looking at the old code:
        # data = await self.persistence.get_users(...) -> likely returns dict(items=[...], total=...)

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
        # Handle list of dicts or objects
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
