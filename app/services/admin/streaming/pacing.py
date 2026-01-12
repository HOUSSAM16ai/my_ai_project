"""استراتيجية ضبط إيقاع بث الأحداث لضمان توافق DIP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.admin.streaming.config import StreamingConfig
from app.services.admin.streaming.metrics import StreamingMetrics


class PacingStrategy(Protocol):
    """بروتوكول لتحديد زمن التوقف بين الدُفعات بناءً على الإحصاءات."""

    def delay_ms(
        self, metrics: StreamingMetrics, config: StreamingConfig
    ) -> float:  # pragma: no cover - بروتوكول
        """يحسب التأخير المناسب بالمللي ثانية."""


@dataclass(frozen=True)
class AdaptivePacingStrategy:
    """حساب تأخير ديناميكي يعتمد على آخر زمن إرسال وحدود الضبط."""

    def delay_ms(self, metrics: StreamingMetrics, config: StreamingConfig) -> float:
        """يضبط التأخير بين الدُفعات مع ضمان البقاء داخل الحدود الدنيا والعليا."""

        latest_latency = (
            metrics.chunk_times[-1] if metrics.chunk_times else config.min_chunk_delay_ms
        )
        bounded = max(config.min_chunk_delay_ms, latest_latency)
        return min(bounded, config.max_chunk_delay_ms)
