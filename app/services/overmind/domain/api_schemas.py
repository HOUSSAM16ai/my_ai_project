# app/services/overmind/domain/api_schemas.py
"""
نماذج واجهة برمجة تطبيقات "العقل المدبر" (Overmind API Schemas).
---------------------------------------------------------
تحتوي هذه الوحدة على نماذج البيانات (Pydantic Models) الصارمة التي تحدد عقد التواصل
مع منظومة الوكلاء الخارقين. تلتزم هذه النماذج بمعايير CS50 2025.

المعايير:
- استخدام `pydantic` للتحقق الصارم من البيانات.
- توثيق "Legendary" باللغة العربية.
- عدم الاعتماد على `typing.List` أو `Optional` واستخدام `list` و `| None`.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MissionStatusEnum(str, Enum):
    """حالات المهمة الممكنة."""
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatusEnum(str, Enum):
    """حالات خطوة التنفيذ."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class MissionStepResponse(BaseModel):
    """
    نموذج استجابة لخطوة واحدة داخل المهمة.
    """
    id: int | None = Field(None, description="معرف الخطوة")
    name: str = Field(..., description="اسم الخطوة أو الإجراء")
    description: str | None = Field(None, description="وصف تفصيلي للخطوة")
    status: StepStatusEnum = Field(StepStatusEnum.PENDING, description="حالة الخطوة الحالية")
    result: str | None = Field(None, description="نتيجة تنفيذ الخطوة")
    tool_used: str | None = Field(None, description="اسم الأداة المستخدمة إن وجد")
    created_at: datetime = Field(..., description="توقيت إنشاء الخطوة")
    completed_at: datetime | None = Field(None, description="توقيت اكتمال الخطوة")

    class Config:
        from_attributes = True


class MissionCreate(BaseModel):
    """
    نموذج إنشاء مهمة جديدة.
    يطلب هذا النموذج الهدف الأساسي والسياق الاختياري.
    """
    objective: str = Field(..., min_length=5, max_length=5000, description="الهدف الرئيسي للمهمة")
    context: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict, description="سياق إضافي للمهمة (مثل بيئة العمل، قيود)"
    )
    priority: int = Field(1, ge=1, le=5, description="أولوية المهمة (1-5)")


class MissionResponse(BaseModel):
    """
    نموذج الاستجابة الكاملة للمهمة.
    """
    id: int = Field(..., description="معرف المهمة الفريد")
    objective: str = Field(..., description="الهدف الرئيسي")
    status: MissionStatusEnum = Field(..., description="الحالة العامة للمهمة")
    created_at: datetime = Field(..., description="توقيت الإنشاء")
    updated_at: datetime = Field(..., description="آخر تحديث")
    result: dict[str, str | int | float | bool | None] | None = Field(
        None, description="النتيجة النهائية للمهمة"
    )
    steps: list[MissionStepResponse] = Field(default_factory=list, description="قائمة خطوات التنفيذ")

    class Config:
        from_attributes = True


class MissionEventResponse(BaseModel):
    """
    نموذج لحدث واحد في تدفق البث (SSE).
    """
    event_type: str = Field(..., description="نوع الحدث (مثلاً: step_start, log, completion)")
    mission_id: int = Field(..., description="معرف المهمة")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="توقيت الحدث")
    payload: dict[str, str | int | float | bool | list | dict | None] = Field(
        default_factory=dict, description="بيانات الحدث التفصيلية"
    )
