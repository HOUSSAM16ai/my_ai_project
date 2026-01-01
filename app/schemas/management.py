"""
Management API Schemas.
Pydantic models for Admin Dashboard and CRUD operations.
Ensures strict typing and governance for data exchange.
"""

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class PaginationMeta(BaseModel):
    """Metadata for paginated responses."""
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse[T](BaseModel):
    """
    Generic wrapper for paginated data.
    Standardizes response format across the API.
    """
    items: list[T]
    pagination: PaginationMeta

class UserResponse(BaseModel):
    """
    DTO for User data.
    Excludes sensitive fields like password hashes.
    """
    id: int
    email: str
    full_name: str | None = None
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class MissionResponse(BaseModel):
    """DTO for Mission data."""
    id: int
    name: str | None = None
    objective: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    """DTO for Task data."""
    id: int
    mission_id: int | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class GenericResponse(BaseModel):
    """Simple success/error response."""
    status: str = "success"
    message: str | None = None
    data: Any | None = None
