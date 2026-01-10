"""منطق تقسيم النصوص مع الحفاظ على المسافات والكتل البرمجية."""
from __future__ import annotations

import re
from collections.abc import Generator
from dataclasses import dataclass

from app.services.admin.streaming.config import StreamingConfig


@dataclass(slots=True)
class SmartTokenChunker:
    """يقسّم النص إلى أجزاء مثالية للبث مع احترام الفراغات والكتل."""

    config: StreamingConfig

    def __init__(self, config: StreamingConfig | None = None) -> None:
        """يبني الكائن مع إمكانية تمرير ضبط مخصص للتقسيم."""

        self.config = config or StreamingConfig()

    def chunk_text(self, text: str, chunk_size: int | None = None) -> list[str]:
        """يُقسّم النص إلى أجزاء من الكلمات مع الحفاظ على المحاذاة."""

        if not text:
            return []

        tokens = _split_into_tokens(text)
        size = chunk_size or self.config.optimal_chunk_size
        return _build_chunks_from_tokens(tokens, size)

    def smart_chunk(self, text: str, chunk_size: int | None = None) -> Generator[str, None, None]:
        """يُعالج النص مع احترام الكتل البرمجية المحاطة بعلامات ``` دون تجزئتها."""

        if not text:
            return

        size = chunk_size or self.config.optimal_chunk_size
        fence_pattern = re.compile(r"(```.*?```)", re.DOTALL)
        cursor = 0

        for match in fence_pattern.finditer(text):
            leading = text[cursor : match.start()]
            if leading:
                for chunk in self.chunk_text(leading, size):
                    yield chunk

            yield match.group(1)
            cursor = match.end()

        trailing = text[cursor:]
        if trailing:
            for chunk in self.chunk_text(trailing, size):
                yield chunk


def _split_into_tokens(text: str) -> list[str]:
    """يفصل النص إلى رموز كلمات ومسافات لضمان المحافظة على التنسيق."""

    return re.split(r"(\s+)", text)


def _build_chunks_from_tokens(tokens: list[str], chunk_size: int) -> list[str]:
    """يُكوّن أجزاء نصية من الرموز مع ضبط عدد الكلمات في كل جزء."""

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_word_count = 0

    for token in tokens:
        if not token:
            continue

        current_chunk.append(token)
        if not token.isspace():
            current_word_count += 1

        if current_word_count >= chunk_size:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_word_count = 0

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks
