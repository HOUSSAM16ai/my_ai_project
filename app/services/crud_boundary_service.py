"""
CRUD Boundary Service
Acts as a facade for CRUD operations, orchestrating business logic.
Follows the Boundary Service pattern from the Admin Router refactoring.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crud.crud_persistence import CrudPersistence

logger = logging.getLogger(__name__)


class CrudBoundaryService:
    """
    Boundary Service for CRUD operations.
    Orchestrates business logic and delegates data access to CrudPersistence.
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
    ) -> dict[str, Any]:
        """
        Retrieve users with pagination and filtering.
        Returns formatted response for API.
        """
        data = await self.persistence.get_users(
            page=page,
            per_page=per_page,
            email=email,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        return {
            "status": "success",
            "message": "Users retrieved",
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    async def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        """
        Retrieve a single user by ID.
        Returns formatted response for API.
        """
        user = await self.persistence.get_user_by_id(user_id)
        
        if not user:
            return {
                "status": "error",
                "message": "User not found",
                "data": None,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        
        return {
            "status": "success",
            "data": user,
            "message": "User found",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    async def get_missions(self, status: str | None = None) -> dict[str, Any]:
        """
        Retrieve missions with optional status filter.
        Returns formatted response for API.
        """
        missions = await self.persistence.get_missions(status=status)
        
        return {
            "status": "success",
            "data": {"items": missions},
            "message": "Missions retrieved",
        }

    async def get_mission_by_id(self, mission_id: int) -> dict[str, Any]:
        """
        Retrieve a single mission by ID.
        Returns formatted response for API.
        """
        mission = await self.persistence.get_mission_by_id(mission_id)
        
        if not mission:
            return {
                "status": "error",
                "message": "Mission not found",
                "data": None,
            }
        
        return {
            "status": "success",
            "data": mission,
            "message": "Mission found",
        }

    async def get_tasks(self, mission_id: int | None = None) -> dict[str, Any]:
        """
        Retrieve tasks with optional mission filter.
        Returns formatted response for API.
        """
        tasks = await self.persistence.get_tasks(mission_id=mission_id)
        
        return {
            "status": "success",
            "data": {"items": tasks},
            "message": "Tasks retrieved",
        }
