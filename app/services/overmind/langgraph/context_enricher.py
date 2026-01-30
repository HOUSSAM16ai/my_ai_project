from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from app.core.logging import get_logger
from app.services.search_engine.query_refiner import get_refined_query
from app.services.search_engine.retriever import get_retriever

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ContextEnrichmentResult:
    """
    نتيجة إثراء السياق لمعالجة الهدف قبل تشغيل LangGraph.
    """

    refined_objective: str
    metadata: dict[str, object]
    snippets: list[dict[str, object]]


class ContextEnricher:
    """
    خدمة إثراء سياق تجمع بين DSPy و LlamaIndex.

    تعتمد على إعادة صياغة الهدف ثم استرجاع مقتطفات معرفة داعمة
    لضمان أن الوكلاء يفهمون نية المستخدم بعمق أكبر.
    """

    def __init__(self, *, max_snippets: int = 4) -> None:
        self.max_snippets = max_snippets

    async def enrich(
        self, objective: str, context: dict[str, object]
    ) -> ContextEnrichmentResult:
        """
        تنفيذ خط إثراء السياق وإرجاع النتيجة المجمعة.
        """
        refined_objective, metadata = await self._refine_objective(objective)
        snippets = await self._retrieve_snippets(refined_objective, context, metadata)
        return ContextEnrichmentResult(
            refined_objective=refined_objective, metadata=metadata, snippets=snippets
        )

    async def _refine_objective(self, objective: str) -> tuple[str, dict[str, object]]:
        """
        تحسين صياغة الهدف اعتماداً على DSPy عند توفر مفتاح واجهة.
        """
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return objective, {}

        try:
            result = await asyncio.to_thread(get_refined_query, objective, api_key)
        except Exception as exc:
            logger.warning("فشل تحسين الهدف عبر DSPy: %s", exc)
            return objective, {}

        if not isinstance(result, dict):
            return objective, {}

        refined = str(result.get("refined_query") or objective)
        metadata = {
            "year": result.get("year"),
            "subject": result.get("subject"),
            "branch": result.get("branch"),
        }
        cleaned_metadata = {k: v for k, v in metadata.items() if v is not None}
        return refined, cleaned_metadata

    async def _retrieve_snippets(
        self, query: str, context: dict[str, object], metadata: dict[str, object]
    ) -> list[dict[str, object]]:
        """
        جلب مقتطفات دلالية عبر LlamaIndex عند توفر قاعدة المتجهات.
        """
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return []

        filters = _extract_metadata_filters(context, metadata)

        try:
            retriever = get_retriever(db_url)
            nodes = retriever.search(query, limit=self.max_snippets, filters=filters)
        except Exception as exc:
            logger.warning("فشل استرجاع مقتطفات LlamaIndex: %s", exc)
            return []

        snippets: list[dict[str, object]] = []
        for node in nodes:
            text, metadata = _extract_node_payload(node)
            if not text:
                continue
            snippets.append({"text": text, "metadata": metadata})
        return snippets


def _extract_metadata_filters(
    context: dict[str, object], metadata: dict[str, object]
) -> dict[str, object]:
    """
    استخراج مرشحات البحث من السياق المشترك إن وجدت.
    """
    candidate = context.get("metadata_filters")
    if isinstance(candidate, dict):
        return candidate
    return metadata


def _extract_node_payload(node: object) -> tuple[str | None, dict[str, object]]:
    """
    استخراج النص والبيانات الوصفية من عقدة LlamaIndex بشكل آمن.
    """
    payload = getattr(node, "node", node)
    text_value = _safe_text(payload)
    metadata_value = getattr(payload, "metadata", {})
    if not isinstance(metadata_value, dict):
        metadata_value = {}
    return text_value, metadata_value


def _safe_text(payload: object) -> str | None:
    """
    استخراج النص من العقدة مع دعم عدة أشكال للواجهة.
    """
    if hasattr(payload, "get_text"):
        text_value = payload.get_text()
        return text_value if isinstance(text_value, str) else None
    text_value = getattr(payload, "text", None)
    return text_value if isinstance(text_value, str) else None
