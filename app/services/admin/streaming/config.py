"""ضبط بث المحادثات الإدارية بطريقة قابلة للتمديد."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamingConfig:
    """يحدد إعدادات البث مثل حجم الدفعات والفواصل الزمنية بين الأحداث."""

    optimal_chunk_size: int = 3
    min_chunk_delay_ms: int = 30
    max_chunk_delay_ms: int = 100
