"""
CRUD Persistence Layer
Encapsulates all Data Access Logic for CRUD operations.
Part of the "Evolutionary Logic Distillation" - separating persistence from orchestration.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mission, Task, User

logger = logging.getLogger(__name__)


class CrudPersistence:
    """
    Encapsulates all Data Access Logic for CRUD operations.
    Handles database queries for Users, Missions, and Tasks.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

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
        """
        query = select(User)
        
        # Apply email filter
        if email:
            query = query.where(User.email == email)
        
        # Apply sorting
        if sort_by and hasattr(User, sort_by):
            col = getattr(User, sort_by)
            if sort_order == "desc":
                query = query.order_by(col.desc())
            else:
                query = query.order_by(col.asc())
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(User)
        if email:
            count_query = count_query.where(User.email == email)
        
        total_result = await self.db.execute(count_query)
        total_items = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Calculate pagination metadata
        total_pages = (total_items + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "items": list(users),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            },
        }

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a single user by ID.
        """
        return await self.db.get(User, user_id)

    async def get_missions(self, status: str | None = None) -> list[Mission]:
        """
        Retrieve missions with optional status filter.
        """
        query = select(Mission)
        
        if status:
            query = query.where(Mission.status == status)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_mission_by_id(self, mission_id: int) -> Mission | None:
        """
        Retrieve a single mission by ID.
        """
        return await self.db.get(Mission, mission_id)

    async def get_tasks(self, mission_id: int | None = None) -> list[Task]:
        """
        Retrieve tasks with optional mission filter.
        """
        query = select(Task)
        
        if mission_id:
            query = query.where(Task.mission_id == mission_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task_by_id(self, task_id: int) -> Task | None:
        """
        Retrieve a single task by ID.
        """
        return await self.db.get(Task, task_id)
