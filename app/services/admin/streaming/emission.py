"""طبقة إخراج الدُفعات لفصل تنسيق الأحداث عن منطق التنسيق الأعلى."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.admin.streaming.formatters import EventFormatter
from app.services.admin.streaming.metrics import (
    MS_TO_SECONDS,
    SessionRecorder,
    StreamingMetrics,
    SystemTimer,
    Timer,
)


@dataclass(slots=True)
class ChunkEmitter:
    """يتولى تنسيق الأحداث الجزئية وتسجيل مؤشرات الأداء."""

    formatter: EventFormatter
    metrics: StreamingMetrics
    timer: Timer = field(default_factory=SystemTimer)

    def emit_delta(self, text: str, *, session: SessionRecorder | None = None) -> str:
        """يبني حدث `delta` ويقيس زمن معالجته لتحديث الإحصاءات."""

        start = self.timer.now()
        event = self.formatter.format_event("delta", {"text": text})
        latency_ms = (self.timer.now() - start) * MS_TO_SECONDS
        self.metrics.record_chunk(len(text), latency_ms)
        if session:
            session.record_chunk(text)
        return event

    def format_event(self, event_type: str, payload: dict[str, str | int | float | bool]) -> str:
        """يمرر تنسيق الأحداث العامة إلى المهيئ المحقون للحفاظ على الاتساق."""

        return self.formatter.format_event(event_type, payload)


__all__ = ["MS_TO_SECONDS", "ChunkEmitter", "SystemTimer", "Timer"]
