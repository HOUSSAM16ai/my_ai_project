"""
عقود الدردشة المشتركة بين طبقات التفريع والحدود.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_gateway import AIClient


@dataclass(frozen=True, slots=True)
class ChatDispatchRequest:
    """بيانات موحدة لطلب الدردشة قبل التوجيه حسب الدور."""

    question: str
    conversation_id: str | int | None
    ai_client: AIClient
    session_factory: Callable[[], AsyncSession]
    ip: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True, slots=True)
class ChatDispatchResult:
    """نتيجة التفريع مع كود الحالة وتدفق الاستجابة."""

    status_code: int
    stream: AsyncGenerator[str, None]
