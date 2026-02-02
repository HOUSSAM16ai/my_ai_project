from __future__ import annotations

import os
from dataclasses import dataclass

from app.services.overmind.langgraph.context_contracts import (
    ObjectiveRefiner,
    Snippet,
    SnippetRetriever,
)
from app.services.overmind.langgraph.context_providers import (
    build_default_refiner,
    build_default_retriever,
)


def get_retriever(database_url: str | None) -> SnippetRetriever:
    """يبني مسترجع المقتطفات الافتراضي وفق البيئة."""
    _ = database_url
    return build_default_retriever()


def get_reranker() -> object | None:
    """يعيد معالج إعادة الترتيب عند توفره."""
    return None


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
    خدمة إثراء سياق مبنية على مزودات قابلة للتبديل.

    تعتمد على تنقيح الهدف عبر مزود مخصص ثم استرجاع مقتطفات داعمة
    من مصدر خارجي دون اقتران مباشر على تفاصيل التنفيذ.
    """

    def __init__(
        self,
        *,
        max_snippets: int = 4,
        refiner: ObjectiveRefiner | None = None,
        retriever: SnippetRetriever | None = None,
    ) -> None:
        self.max_snippets = max_snippets
        self.refiner = refiner or build_default_refiner()
        self.retriever = retriever or get_retriever(os.environ.get("DATABASE_URL"))
        self.reranker = get_reranker()

    async def enrich(self, objective: str, context: dict[str, object]) -> ContextEnrichmentResult:
        """
        تنفيذ خط إثراء السياق وإرجاع النتيجة المجمعة.
        """
        refine_result = await self.refiner.refine(objective)
        snippets = await _collect_snippets(
            retriever=self.retriever,
            reranker=self.reranker,
            refined_objective=refine_result.refined_objective,
            context=context,
            metadata=refine_result.metadata,
            max_snippets=self.max_snippets,
        )
        return ContextEnrichmentResult(
            refined_objective=refine_result.refined_objective,
            metadata=refine_result.metadata,
            snippets=[_serialize_snippet(snippet) for snippet in snippets],
        )


def _serialize_snippet(snippet: Snippet) -> dict[str, object]:
    """
    تحويل المقتطف إلى قاموس قابل للإرسال.
    """
    return {"text": snippet.text, "metadata": snippet.metadata}


async def _collect_snippets(
    *,
    retriever: SnippetRetriever,
    reranker: object | None,
    refined_objective: str,
    context: dict[str, object],
    metadata: dict[str, object],
    max_snippets: int,
) -> list[Snippet]:
    """يجمع المقتطفات مع دعم مسارات الاسترجاع المختلفة."""
    retrieve = getattr(retriever, "retrieve", None)
    if callable(retrieve):
        return await retrieve(
            refined_objective,
            context=context,
            metadata=metadata,
            max_snippets=max_snippets,
        )

    search = getattr(retriever, "search", None)
    if not callable(search):
        return []

    nodes = search(refined_objective, limit=max_snippets, filters=metadata)
    if reranker and hasattr(reranker, "rerank"):
        nodes = reranker.rerank(refined_objective, nodes, top_n=max_snippets)
    return [_node_to_snippet(node) for node in nodes]


def _node_to_snippet(node: object) -> Snippet:
    """يحوّل عقدة بحث إلى مقتطف قياسي."""
    payload = getattr(node, "node", node)
    text = getattr(payload, "text", "")
    metadata = getattr(payload, "metadata", {})
    return Snippet(text=text, metadata=metadata)
