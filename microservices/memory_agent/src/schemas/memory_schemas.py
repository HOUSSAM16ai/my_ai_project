"""
مخططات بيانات وكيل الذاكرة (Memory Agent Schemas).

يحتوي هذا الملف على جميع نماذج Pydantic المستخدمة في API.
تم فصل المخططات عن المنطق لتطبيق مبدأ SRP.

المبادئ:
- SOLID: Single Responsibility Principle
- Harvard CS50 2025: توثيق عربي شامل
"""

from uuid import UUID

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    """حمولة إنشاء عنصر ذاكرة جديد."""

    content: str = Field(..., description="نص الذاكرة المراد حفظها")
    tags: list[str] = Field(default_factory=list, description="وسوم مساعدة")


class MemoryResponse(BaseModel):
    """استجابة بيانات الذاكرة."""

    entry_id: UUID
    content: str
    tags: list[str]


class MemorySearchFilters(BaseModel):
    """مرشحات البحث بالوسوم."""

    tags: list[str] = Field(default_factory=list, description="وسوم التصفية المطلوبة")


class MemorySearchRequest(BaseModel):
    """حمولة البحث عن الذاكرة عبر POST."""

    query: str = Field(default="", description="نص البحث")
    filters: MemorySearchFilters = Field(
        default_factory=MemorySearchFilters,
        description="مرشحات البحث الدلالي",
    )
    limit: int = Field(default=10, ge=1, le=50, description="عدد النتائج المطلوب")
