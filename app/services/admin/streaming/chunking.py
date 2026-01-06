"""منطق تقسيم تدفقات النص إلى حزم متسقة قابلة للبث."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Protocol

from app.services.admin.streaming.config import StreamingConfig
from app.services.admin.streaming.formatters import SSEStreamFormatter, StreamFormatter


class AsyncSleeper(Protocol):
    """بروتوكول لتجريد آلية الإيقاف المؤقت أثناء البث."""

    async def __call__(self, delay_seconds: float) -> None:  # pragma: no cover - بروتوكول
        """ينفذ إيقافاً مؤقتاً غير حاجز."""


@dataclass(slots=True)
class StreamingChunker:
    """مسؤول عن تقسيم التدفقات إلى أحداث قابلة للتوسعة."""

    config: StreamingConfig
    formatter: StreamFormatter
    sleep: AsyncSleeper

    def __init__(
        self,
        config: StreamingConfig | None = None,
        formatter: StreamFormatter | None = None,
        sleep: AsyncSleeper | None = None,
    ) -> None:
        """تهيئة الكائن مع الاعتماد على التجريدات بدلاً من تطبيقات صلبة."""

        self.config = config or StreamingConfig()
        self.formatter = formatter or SSEStreamFormatter()
        self.sleep = sleep or asyncio.sleep

    async def chunk_stream(self, generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """يبث البيانات الواردة في حزم محسوبة بدون خلط المنطق مع التنسيق."""

        buffer = ""
        async for token in generator:
            buffer += token
            if self._should_flush(buffer):
                yield self.formatter.format_delta(buffer)
                buffer = ""
                await self.sleep(self._min_delay_seconds)

        if buffer:
            yield self.formatter.format_delta(buffer)

        yield self.formatter.format_complete()

    @property
    def _min_delay_seconds(self) -> float:
        """يحول قيمة التأخير الدنيا بالمللي ثانية إلى ثواني للاستخدام الداخلي."""

        return self.config.min_chunk_delay_ms / 1000

    def _should_flush(self, buffer: str) -> bool:
        """يتحقق مما إذا كانت الدفعة الحالية جاهزة للإرسال بناءً على الحجم المثالي."""

        return len(buffer.split()) >= self.config.optimal_chunk_size
