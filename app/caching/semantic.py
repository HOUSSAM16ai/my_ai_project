"""
ذاكرة الرنين المعرفي (Semantic Cache).
---------------------------------------------------------
توفر طبقة تخزين مؤقت دلالية (Semantic Caching Layer) لاسترجاع الإجابات
بناءً على المعنى وليس فقط التطابق النصي الحرفي.

المعايير:
- Harvard CS50: صرامة النوع والتوثيق العربي.
- Berkeley SICP: التجريد (Abstraction) وفصل التنفيذ.
"""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.caching.strategies import LRUPolicy, StrategicMemoryCache

if TYPE_CHECKING:
    from app.core.ai_gateway import AIClient

logger = logging.getLogger(__name__)


class SemanticEncoder(ABC):
    """
    بروتوكول لترميز النصوص إلى متجهات أو مفاتيح دلالية.
    """

    @abstractmethod
    async def encode(self, text: str) -> str:
        """تحويل النص إلى مفتاح دلالي فريد (Hash/Vector ID)."""
        ...


class SimpleTextNormalizer(SemanticEncoder):
    """
    مشفر بسيط يعتمد على تطبيع النص (Normalization).
    يستخدم كبديل مؤقت لنماذج التضمين (Embeddings).
    """

    async def encode(self, text: str) -> str:
        # 1. توحيد الحروف (Lower case)
        text = text.lower()
        # 2. إزالة التشكيل والحروف الخاصة (Regex for Arabic/English)
        # إزالة الرموز غير الحرفية والرقمية والمسافات
        text = re.sub(r"[^\w\s]", "", text)
        # 3. تقليم المسافات الزائدة
        text = re.sub(r"\s+", " ", text).strip()
        # 4. إنشاء بصمة (Hash)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SemanticCache:
    """
    الذاكرة الدلالية (Semantic Cache).

    تستخدم لتخزين أزواج (سؤال، إجابة) واسترجاعها بسرعة لتجنب المعالجة المكررة.
    """

    def __init__(
        self,
        encoder: SemanticEncoder | None = None,
        capacity: int = 1000,
        ttl: int = 3600,  # ساعة واحدة افتراضياً
    ) -> None:
        self._encoder = encoder or SimpleTextNormalizer()
        self._backend = StrategicMemoryCache(policy=LRUPolicy(capacity), default_ttl=ttl)

    async def get(self, query: str) -> str | None:
        """
        استرجاع إجابة مخزنة لسؤال مشابه دلالياً.
        """
        try:
            key = await self._encoder.encode(query)
            result = await self._backend.get(key)
            if result and isinstance(result, str):
                logger.debug("Semantic Cache Hit", extra={"query_hash": key})
                return result
            return None
        except Exception as e:
            logger.error(f"Error reading from Semantic Cache: {e}")
            return None

    async def set(self, query: str, response: str) -> None:
        """
        تخزين إجابة لسؤال.
        """
        try:
            key = await self._encoder.encode(query)
            await self._backend.set(key, response)
            logger.debug("Semantic Cache Set", extra={"query_hash": key})
        except Exception as e:
            logger.error(f"Error writing to Semantic Cache: {e}")

    async def clear(self) -> None:
        """مسح الذاكرة بالكامل."""
        await self._backend.clear()
