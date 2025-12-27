"""
نماذج البيانات لخدمة عميل النماذج اللغوية الكبيرة.
Data models for the LLM Client service.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class LLMTool(BaseModel):
    """
    نموذج لتمثيل أداة يمكن للنموذج استخدامها.
    Represents a tool available to the LLM.
    """
    type: Literal["function"] = "function"
    function: dict[str, Any]


class LLMMessage(BaseModel):
    """
    نموذج لتمثيل رسالة في المحادثة.
    Represents a message in the conversation.
    """
    role: str
    content: str | None = None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class LLMPayload(BaseModel):
    """
    حمولـة الطلب المرسلة إلى النموذج.
    Request payload sent to the model.
    """
    model: str
    messages: list[dict[str, Any]]  # Using dict for flexibility with different providers, but logically LLMMessage
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    extra: dict[str, Any] | None = None

    model_config = ConfigDict(extra="ignore")


class LLMMeta(BaseModel):
    """
    بيانات وصفية حول الاستجابة.
    Metadata about the response.
    """
    latency_ms: float
    attempts: int
    retry_schedule: list[float]
    timestamp_start: float
    timestamp_end: float
    model_used: str
    finish_reason: str | None = None
    stream: bool = False


class LLMResponseEnvelope(BaseModel):
    """
    الغلاف الموحد لاستجابة النموذج.
    Standardized envelope for model response.
    """
    content: str
    role: str = "assistant"
    tool_calls: list[dict[str, Any]] | None = None
    meta: LLMMeta
    raw: dict[str, Any] | None = None  # For debugging/hooks
