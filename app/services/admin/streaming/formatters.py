"""مهيئات تدفق Server-Sent Events لضمان فصل التقديم عن المنطق."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol


class StreamFormatter(Protocol):
    """بروتوكول بسيط لتحويل النصوص إلى أحداث بث."""

    def format_delta(self, text: str) -> str:  # pragma: no cover - بروتوكول
        """يبني رسالة جزئية قابلة للإرسال عبر SSE."""

    def format_complete(self) -> str:  # pragma: no cover - بروتوكول
        """يبني رسالة انتهاء التدفق."""


class EventFormatter(Protocol):
    """بروتوكول لتنسيق أحداث SSE العامة مع اسم الحدث والبيانات."""

    def format_event(
        self, event_type: str, payload: dict[str, str | int | float | bool]
    ) -> str:  # pragma: no cover - بروتوكول
        """يحزم الحدث في شكل SSE قياسي."""


@dataclass(frozen=True)
class SSEStreamFormatter(StreamFormatter):
    """تنسيق رسائل SSE وفق معايير الأحداث المتدفقة."""

    def format_delta(self, text: str) -> str:
        """يحزم النص في حدث `delta` مع ترميز JSON آمن."""

        data = json.dumps({"text": text})
        return f"event: delta\ndata: {data}\n\n"

    def format_complete(self) -> str:
        """يُرجع رسالة اكتمال التدفق."""

        return "event: complete\ndata: {}\n\n"


@dataclass(frozen=True)
class SSEEventFormatter(EventFormatter):
    """يُنسّق أي حدث SSE باستخدام ترميز JSON للبيانات."""

    def format_event(self, event_type: str, payload: dict[str, str | int | float | bool]) -> str:
        """يُرجع الحدث مع اسم الحدث والبيانات بتنسيق SSE."""

        data = json.dumps(payload)
        return f"event: {event_type}\ndata: {data}\n\n"
