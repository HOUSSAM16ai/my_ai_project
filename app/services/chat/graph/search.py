"""
مُنسّق البحث الرسومي (Graph Search Orchestrator).
-------------------------------------------------
يولّد هذا المكوّن قائمة استعلامات بحث ذكية بالاعتماد على
حالة الرسم البياني وإشارات السياق لضمان أعلى دقة ممكنة.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.utils.query_expander import FallbackQueryExpander
from app.services.chat.graph.state import AgentState


@dataclass(frozen=True)
class GraphSearchPlan:
    """خطة البحث الناتجة عن سياق الرسم البياني."""

    queries: list[str]
    signals: list[str]


def build_graph_search_plan(state: AgentState) -> GraphSearchPlan:
    """يبني خطة بحث متعددة المراحل اعتمادًا على السياق والخطة."""
    last_message = _safe_last_message(state)
    signals: list[str] = []

    if not last_message:
        return GraphSearchPlan(queries=[], signals=["empty_message"])

    queries = [last_message]
    signals.append("base_query")

    relaxed_queries = _build_relaxed_queries(last_message)
    if relaxed_queries:
        queries.extend(relaxed_queries)
        signals.append("relaxed_queries")

    enriched_query = _enrich_with_context(last_message, state)
    if enriched_query and enriched_query not in queries:
        queries.append(enriched_query)
        signals.append("context_enriched")

    unique_queries = _deduplicate(queries)
    return GraphSearchPlan(queries=unique_queries, signals=signals)


def _safe_last_message(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return ""
    return str(messages[-1].content)


def _build_relaxed_queries(message: str) -> list[str]:
    variations = FallbackQueryExpander.generate_variations(message)
    if not variations:
        return []
    return [q for q in variations if q and q != message]


def _enrich_with_context(message: str, state: AgentState) -> str | None:
    context = state.get("user_context", {})
    subject = context.get("subject")
    branch = context.get("branch")
    year = context.get("year")

    tokens = [message]
    if subject:
        tokens.append(str(subject))
    if branch:
        tokens.append(str(branch))
    if year:
        tokens.append(str(year))

    if len(tokens) == 1:
        return None
    return " ".join(tokens)


def _deduplicate(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered
