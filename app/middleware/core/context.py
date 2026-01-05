# app/middleware/core/context.py
# ======================================================================================
# ==                    UNIFIED REQUEST CONTEXT (FASTAPI EDITION)                   ==
# ======================================================================================
"""
سياق الطلب الموحد - Unified Request Context

حاوية معيارية لبيانات الطلب وبياناته التعريفية مصممة خصيصاً لـ FastAPI، مع
تركيز على البساطة للمبتدئين وقابلية التوسعة للأنظمة الكبيرة.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from fastapi import Request


Primitive = str | int | float | bool | None

@dataclass
class RequestContext:
    """حاوية بيانات موحّدة لطلبات FastAPI تسهّل مشاركة المعلومات بين الوسطاء."""

    # Request identification
    request_id: str = field(default_factory=lambda: str(uuid4()))
    method: str = "GET"
    path: str = "/"

    # Request data
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Primitive] = field(default_factory=dict)
    body: dict[str, Primitive] | None = None

    # Client information
    ip_address: str = "unknown"
    user_agent: str = ""

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Extensibility
    metadata: dict[str, object] = field(default_factory=dict)

    # Observability
    trace_id: str | None = None
    span_id: str | None = None

    # Authentication/Authorization
    user_id: str | None = None
    session_id: str | None = None

    # Framework-specific request object (for advanced use cases)
    _raw_request: Request | None = None

    @classmethod
    async def from_fastapi_request(cls, request: Request) -> "RequestContext":
        """ينشئ سياقاً جاهزاً من كائن طلب FastAPI دون استهلاك جسم الطلب."""
        # Attempt to read body if possible, but usually middleware consumes it carefully
        # For now we default body to None to avoid consuming stream unless necessary

        return cls(
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            _raw_request=request,
        )

    def set_trace_context(self, trace_id: str, span_id: str) -> None:
        """يضبط معرفات التتبع الموزعة لضمان ترابط السجلات."""
        self.trace_id = trace_id
        self.span_id = span_id

    def set_user_context(self, user_id: str, session_id: str | None = None) -> None:
        """يحفظ هوية المستخدم المتحقق منها ومعرّف الجلسة إن وجد."""
        self.user_id = user_id
        self.session_id = session_id

    def add_metadata(self, key: str, value: object) -> None:
        """يضيف بيانات تعريفية مهيكلة يمكن استهلاكها من الوسطاء اللاحقة."""

        self.metadata[key] = value

    def get_metadata(self, key: str, default: object | None = None) -> object | None:
        """يعيد بيانات تعريفية محفوظة أو القيمة الافتراضية عند غيابها."""

        return self.metadata.get(key, default)

    def get_header(self, name: str, default: str = "") -> str:
        """يجلب قيمة ترويسة محددة دون التأثر بحالة الأحرف."""
        name_lower = name.lower()
        for key, value in self.headers.items():
            if key.lower() == name_lower:
                return value
        return default

    def to_dict(self) -> dict[str, object]:
        """يحّول السياق إلى قاموس مناسب للتسجيل أو التسلسل."""
        return {
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }
