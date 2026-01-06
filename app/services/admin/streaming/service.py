"""خدمة بث المحادثات الإدارية بتجميع واضح وقابل للاستبدال."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Protocol

from app.services.admin.streaming.config import StreamingConfig
from app.services.admin.streaming.emission import ChunkEmitter, MS_TO_SECONDS
from app.services.admin.streaming.formatters import EventFormatter, SSEEventFormatter
from app.services.admin.streaming.metrics import (
    SessionRecorder,
    StreamingMetrics,
    StreamingStats,
    SystemTimer,
    Timer,
)
from app.services.admin.streaming.pacing import AdaptivePacingStrategy, PacingStrategy
from app.services.admin.streaming.speculative import SpeculativeDecoder
from app.services.admin.streaming.token_chunker import SmartTokenChunker

EventPayload = dict[str, str | int | float | bool]


class SleepCallable(Protocol):
    """بروتوكول بسيط لتأخير غير حاجز قابل للاستبدال أثناء الاختبار."""

    async def __call__(self, delay_seconds: float) -> None:  # pragma: no cover - بروتوكول
        """ينفذ إيقافاً مؤقتاً بالثواني."""


class StreamingServiceFactory(Protocol):
    """بروتوكول مصنع خدمة البث لضمان الفصل بين التجميع والاستخدام."""

    def create(self) -> "AdminChatStreamingService":  # pragma: no cover - بروتوكول
        """ينشئ خدمة بث جاهزة بالاعتماد على تجميع محدد مسبقاً."""


@dataclass(slots=True)
class AdminChatStreamingService:
    """يُدير بث الردود مع تقسيم ذكي وقياس أداء شفاف."""

    config: StreamingConfig
    metrics: StreamingMetrics
    speculative_decoder: SpeculativeDecoder
    chunker: SmartTokenChunker
    formatter: EventFormatter
    emitter: ChunkEmitter
    timer: Timer
    sleep: SleepCallable
    pacing_strategy: PacingStrategy

    def __init__(
        self,
        *,
        config: StreamingConfig | None = None,
        metrics: StreamingMetrics | None = None,
        speculative_decoder: SpeculativeDecoder | None = None,
        chunker: SmartTokenChunker | None = None,
        formatter: EventFormatter | None = None,
        emitter: ChunkEmitter | None = None,
        timer: Timer | None = None,
        sleep: SleepCallable | None = None,
        pacing_strategy: PacingStrategy | None = None,
    ) -> None:
        """يُهيّئ الخدمة مع حقن التبعيات لسهولة الاختبار والتوسعة."""

        self.config = config or StreamingConfig()
        self.metrics = metrics or StreamingMetrics()
        self.speculative_decoder = speculative_decoder or SpeculativeDecoder()
        self.chunker = chunker or SmartTokenChunker(self.config)
        self.formatter = formatter or SSEEventFormatter()
        self.timer = timer or SystemTimer()
        self.emitter = emitter or ChunkEmitter(
            formatter=self.formatter, metrics=self.metrics, timer=self.timer
        )
        self.sleep = sleep or asyncio.sleep
        self.pacing_strategy = pacing_strategy or AdaptivePacingStrategy()


    async def stream_response(
        self, text: str, metadata: EventPayload | None = None
    ) -> AsyncGenerator[str, None]:
        """يبث نصاً جاهزاً كدفعات مع تضمين بيانات تعريف اختيارية."""

        session, initial_events = self._start_session(metadata)

        for event in initial_events:
            yield event

        if not text:
            yield self._finalize_session(session)
            return

        async for event in self._emit_chunks(text, session):
            yield event

        yield self._finalize_session(session)

    async def async_stream_response(
        self, generator: AsyncGenerator[str, None], metadata: EventPayload | None = None
    ) -> AsyncGenerator[str, None]:
        """يبث محتوى مولّد غير تزامني مع الالتزام بتنسيق SSE."""

        session, initial_events = self._start_session(metadata)
        for event in initial_events:
            yield event

        buffer = ""
        async for token in generator:
            buffer += token
            if self._buffer_ready(buffer):
                yield self.emitter.emit_delta(buffer, session=session)
                buffer = ""
                await self.sleep(self.config.min_chunk_delay_ms / MS_TO_SECONDS)

        if buffer:
            yield self.emitter.emit_delta(buffer, session=session)

        yield self._finalize_session(session)

    def get_metrics(self) -> StreamingStats:
        """يعرض إحصائيات الأداء الحالية ببيانات منظمة."""

        return self.metrics.get_stats()

    def _buffer_ready(self, buffer: str) -> bool:
        """يتحقق من جاهزية الدفعة للإرسال بناءً على حجم الكلمات."""

        return len(buffer.split()) >= self.config.optimal_chunk_size

    def _start_session(
        self, metadata: EventPayload | None = None
    ) -> tuple[SessionRecorder, list[str]]:
        """يُنشئ جلسة جديدة ويهيئ أحداث البيانات الوصفية بشكل موحد."""

        session = SessionRecorder(timer=self.timer)
        events: list[str] = []
        if metadata:
            events.append(self.emitter.format_event("metadata", metadata))
        return session, events

    def _finalize_session(self, session: SessionRecorder) -> str:
        """يسجّل زمن الجلسة ويعيد حدث الإكمال المهيأ."""

        total_time_ms = session.duration_ms()
        self.metrics.record_session(total_time_ms)
        return self.emitter.format_event(
            "complete",
            {"total_time_ms": total_time_ms, "chunks_sent": session.chunk_count},
        )

    async def _emit_chunks(self, text: str, session: SessionRecorder) -> AsyncGenerator[str, None]:
        """يتعامل مع تقسيم النص وإرسال الدفعات مع تأخير محسوب."""

        async for chunk in self._iterate_chunks(text, session):
            yield chunk
            delay_ms = self.pacing_strategy.delay_ms(self.metrics, self.config)
            await self.sleep(delay_ms / MS_TO_SECONDS)

    async def _iterate_chunks(self, text: str, session: SessionRecorder) -> AsyncGenerator[str, None]:
        """ينتج الدفعات المهيئة للإرسال من النص الخام."""

        for chunk in self.chunker.smart_chunk(text):
            yield self.emitter.emit_delta(chunk, session=session)


@dataclass(slots=True)
class AdminChatStreamingServiceFactory:
    """يبني خدمة البث مع حقن التبعيات الافتراضية أو المخصصة."""

    config: StreamingConfig | None = None
    metrics: StreamingMetrics | None = None
    speculative_decoder: SpeculativeDecoder | None = None
    chunker: SmartTokenChunker | None = None
    formatter: EventFormatter | None = None
    emitter: ChunkEmitter | None = None
    timer: Timer | None = None
    sleep: SleepCallable | None = None
    pacing_strategy: PacingStrategy | None = None

    def create(self) -> AdminChatStreamingService:
        """يجمّع خدمة بث جديدة دون الاعتماد على حالة عالمية."""

        return AdminChatStreamingService(
            config=self.config,
            metrics=self.metrics,
            speculative_decoder=self.speculative_decoder,
            chunker=self.chunker,
            formatter=self.formatter,
            emitter=self.emitter,
            timer=self.timer,
            sleep=self.sleep,
            pacing_strategy=self.pacing_strategy,
        )


# Singleton management عبر مصنع قابل للاستبدال لضمان DIP
_streaming_service: AdminChatStreamingService | None = None
_streaming_service_factory: StreamingServiceFactory = AdminChatStreamingServiceFactory()


def set_streaming_service_factory(factory: StreamingServiceFactory) -> None:
    """يضبط مصنع الخدمة لتمكين التهيئة المخصصة وإعادة الاستخدام في الاختبارات."""

    global _streaming_service_factory, _streaming_service
    _streaming_service_factory = factory
    _streaming_service = None


def reset_streaming_service() -> None:
    """يمسح النسخة الحالية لإجبار إعادة التجميع في الاستدعاء التالي."""

    global _streaming_service
    _streaming_service = None


def get_streaming_service() -> AdminChatStreamingService:
    """يعيد خدمة بث مفردة تُنشأ عبر المصنع المحقون للحفاظ على التوافقية."""

    global _streaming_service
    if _streaming_service is None:
        _streaming_service = _streaming_service_factory.create()
    return _streaming_service


__all__ = [
    "AdminChatStreamingService",
    "ChunkEmitter",
    "SmartTokenChunker",
    "SpeculativeDecoder",
    "AdaptivePacingStrategy",
    "StreamingMetrics",
    "StreamingStats",
    "AdminChatStreamingServiceFactory",
    "StreamingServiceFactory",
    "set_streaming_service_factory",
    "reset_streaming_service",
    "get_streaming_service",
]
