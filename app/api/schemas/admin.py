from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from app.core.schemas import RobustBaseModel

class MessageResponse(RobustBaseModel):
    """
    نموذج استجابة لرسالة واحدة.
    """
    id: int | None = Field(None, description="معرف الرسالة")
    role: str = Field(..., description="دور المرسل (user, assistant, system)")
    content: str = Field(..., description="محتوى الرسالة")
    timestamp: datetime | None = Field(None, description="وقت الرسالة")

class ConversationSummaryResponse(RobustBaseModel):
    """
    نموذج ملخص المحادثة للقوائم.
    """

    id: int | str = Field(..., description="معرف المحادثة الموحد")
    conversation_id: int | str | None = Field(
        None, description="معرف المحادثة (للتوافق مع العملاء القدامى)"
    )
    title: str | None = Field(None, description="عنوان المحادثة")
    created_at: datetime | None = Field(None, description="تاريخ الإنشاء")
    updated_at: datetime | None = Field(None, description="تاريخ آخر تحديث")
    message_count: int = Field(0, description="عدد الرسائل")

    @model_validator(mode="after")
    def _sync_identifiers(self) -> "ConversationSummaryResponse":
        """ضمان تساوي معرفي المحادثة بين الحقلين id و conversation_id."""

        normalized_id = self.conversation_id or self.id
        self.id = normalized_id
        self.conversation_id = normalized_id
        return self

class ConversationDetailsResponse(RobustBaseModel):
    """
    نموذج تفاصيل المحادثة الكاملة.
    """
    conversation_id: int | str = Field(..., description="معرف المحادثة")
    title: str | None = Field(None, description="عنوان المحادثة")
    messages: list[MessageResponse] = Field(..., description="قائمة الرسائل")
    metadata: dict[str, Any] | None = Field(None, description="بيانات وصفية إضافية")
