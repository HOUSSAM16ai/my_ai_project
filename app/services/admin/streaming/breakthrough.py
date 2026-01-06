"""خدمة البث الإداري مع واجهات قابلة للتمديد ومتوافقة مع SOLID."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Final

from app.services.admin.streaming.cache import AdaptiveCache
from app.services.admin.streaming.chunking import StreamingChunker
from app.services.admin.streaming.config import StreamingConfig

DEFAULT_STREAMING_CONFIG: Final[StreamingConfig] = StreamingConfig()


class BreakthroughStreamingService:
    """طبقة تنسيق للبث تستخدم مكونات قابلة للحقن للتقسيم والتنسيق."""

    def __init__(self, *, chunker: StreamingChunker | None = None) -> None:
        """يبني الخدمة مع خيار تمرير مكون تقسيم مخصص لسهولة الاختبار."""

        self.chunker = chunker or StreamingChunker(config=DEFAULT_STREAMING_CONFIG)

    async def stream_with_smart_chunking(
        self, generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """يبث محتوى المولد بشكل دفعات محسوبة مع الحفاظ على واجهة SSE."""

        async for event in self.chunker.chunk_stream(generator):
            yield event

    async def predict_next_tokens(self, text: str) -> list[str]:
        """نقطة امتداد مستقبلية للتنبؤ بالمخرجات دون تعطيل الواجهة الحالية."""

        _ = text
        return []


__all__ = ["AdaptiveCache", "BreakthroughStreamingService", "DEFAULT_STREAMING_CONFIG", "StreamingConfig"]
