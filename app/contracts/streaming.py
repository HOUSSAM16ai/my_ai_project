"""
مخططات البث اللحظي (Realtime Streaming Contracts).
----------------------------------------------------
توفر هذه الوحدة العقود المعيارية للرسائل المتدفقة بين العميل والخادم
وبين الوكلاء أنفسهم، مع ضمان النسخ (Versioning) والتتبع (Tracing).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from app.core.schemas import RobustBaseModel

__all__ = [
    "EnvelopeDirection",
    "MessageEnvelope",
    "MessageType",
    "StreamAck",
    "StreamError",
    "StreamEvent",
    "StreamHeartbeat",
    "StreamSubscribe",
    "ToolCall",
    "ToolResult",
]


class MessageType(StrEnum):
    """
    أنواع الرسائل المدعومة في بروتوكول البث.
    """

    CONNECTED = "connected"
    ACK = "ack"
    DELTA = "delta"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    AGENT_EVENT = "agent_event"
    ERROR = "error"
    DONE = "done"
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"


class EnvelopeDirection(StrEnum):
    """
    اتجاه الرسالة بين العميل والخادم أو بين الوكلاء.
    """

    CLIENT_TO_SERVER = "client_to_server"
    SERVER_TO_CLIENT = "server_to_client"
    AGENT_TO_AGENT = "agent_to_agent"


class MessageEnvelope(RobustBaseModel):
    """
    مغلف الرسائل الموحّد لجميع أحداث البث.
    """

    id: str = Field(..., min_length=1, description="معرف الرسالة الفريد")
    type: MessageType = Field(..., description="نوع الرسالة")
    version: Literal["v1"] = Field("v1", description="نسخة البروتوكول")
    timestamp: datetime = Field(..., description="وقت إنشاء الرسالة")
    direction: EnvelopeDirection = Field(..., description="اتجاه الرسالة")
    sender: str = Field(..., min_length=1, description="المرسل")
    recipient: str | None = Field(None, description="المستقبل")
    correlation_id: str = Field(..., min_length=1, description="معرف الربط")
    trace_id: str = Field(..., min_length=1, description="معرف التتبع")
    sequence: int | None = Field(None, ge=0, description="رقم التسلسل")
    payload: dict[str, object] = Field(..., description="محتوى الرسالة")


class StreamSubscribe(RobustBaseModel):
    """
    رسالة الاشتراك في جلسة بث.
    """

    session_id: str = Field(..., min_length=1, description="معرف الجلسة")
    last_sequence: int | None = Field(None, ge=0, description="آخر تسلسل مستلم")


class StreamAck(RobustBaseModel):
    """
    رسالة تأكيد استلام نطاق من الرسائل.
    """

    sequence_from: int = Field(..., ge=0, description="بداية النطاق")
    sequence_to: int = Field(..., ge=0, description="نهاية النطاق")

    @model_validator(mode="after")
    def _validate_range(self) -> "StreamAck":
        """
        يتحقق من أن نهاية النطاق أكبر أو تساوي بدايته.
        """
        if self.sequence_to < self.sequence_from:
            raise ValueError("sequence_to must be greater than or equal to sequence_from")
        return self


class StreamHeartbeat(RobustBaseModel):
    """
    نبضة قلب للحفاظ على الاتصال.
    """

    interval_seconds: int = Field(15, ge=5, description="الفاصل الزمني بالثواني")


class StreamError(RobustBaseModel):
    """
    حمولة خطأ قياسية للبث.
    """

    code: str = Field(..., min_length=1, description="رمز الخطأ")
    message: str = Field(..., min_length=1, description="رسالة الخطأ")
    details: dict[str, object] | None = Field(None, description="تفاصيل إضافية")


class StreamEvent(RobustBaseModel):
    """
    حدث بث عالي المستوى موجه للواجهة الأمامية.
    """

    event: str = Field(..., min_length=1, description="اسم الحدث")
    data: dict[str, object] = Field(..., description="بيانات الحدث")


class ToolCall(RobustBaseModel):
    """
    طلب استدعاء أداة من قبل وكيل.
    """

    tool_name: str = Field(..., min_length=1, description="اسم الأداة")
    input: dict[str, object] = Field(..., description="مدخلات الأداة")


class ToolResult(RobustBaseModel):
    """
    نتيجة تنفيذ أداة.
    """

    tool_name: str = Field(..., min_length=1, description="اسم الأداة")
    status: str = Field(..., min_length=1, description="حالة التنفيذ")
    output: dict[str, object] | None = Field(None, description="مخرجات الأداة")
    error: StreamError | None = Field(None, description="خطأ الأداة إن وجد")
