"""نماذج إدارة النظام مع توثيق عربي صارم وتجنب الأنواع العامة."""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """بيانات التعريف الخاصة بالترقيم في الاستجابات المتعددة الصفحات."""

    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse[T](BaseModel):
    """غلاف موحّد لنتائج متعددة الصفحات يضمن اتساق الحقول للمبتدئين."""

    items: list[T]
    pagination: PaginationMeta


class UserResponse(BaseModel):
    """كائن نقل بيانات للمستخدمين بدون الحقول الحساسة."""

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
    """كائن نقل بيانات للمهام مع الحفاظ على الحقول الاختيارية بسيطة."""

    id: int
    name: str | None = None
    objective: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """كائن نقل بيانات للمهام الفرعية بأسلوب واضح للمبتدئين."""

    id: int
    mission_id: int | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class GenericResponse[T](BaseModel):
    """استجابة بسيطة تحافظ على التناسق مع إمكانية تمرير حمولة محددة النوع."""

    status: str = "success"
    message: str | None = None
    data: T | None = None
