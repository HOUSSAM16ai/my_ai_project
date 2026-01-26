"""
Primitives for the Overmind Cognitive Domain.
---------------------------------------------
Basic building blocks and data models for the cognitive system.
Refactored to adhere to SRP and Clean Architecture.
"""

from typing import Protocol

from pydantic import BaseModel, Field

from app.services.overmind.domain.enums import CognitivePhase


# بروتوكول استدعاء تسجيل الأحداث
class EventLogger(Protocol):
    async def __call__(self, event_type: str, payload: dict[str, object]) -> None: ...


class CognitiveCritique(BaseModel):
    """
    نموذج نتيجة المراجعة والتدقيق.
    """

    approved: bool = Field(..., description="هل تمت الموافقة على العمل؟")
    feedback: str = Field(..., description="ملاحظات المراجعة أو أسباب الرفض")
    score: float = Field(0.0, description="درجة الجودة من 0 إلى 1")


class CognitiveState(BaseModel):
    """
    يحتفظ بالحالة المعرفية الحالية للمهمة.
    """

    mission_id: int
    objective: str
    plan: dict[str, object] | None = None
    design: dict[str, object] | None = None
    execution_result: dict[str, object] | None = None
    critique: CognitiveCritique | None = None
    iteration_count: int = Field(0, description="عدد المحاولات الحالية")
    max_iterations: int = Field(5, description="الحد الأقصى لمحاولات التصحيح الذاتي")
    current_phase: CognitivePhase = CognitivePhase.PLANNING

    # الذاكرة التجميعية (Cumulative Memory) لمنع الحلقات المفرغة
    history_hashes: list[str] = Field(default_factory=list, description="سجل بصمات الخطط السابقة")
