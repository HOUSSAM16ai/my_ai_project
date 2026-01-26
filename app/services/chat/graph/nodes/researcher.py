"""
عقدة الباحث (Researcher Node).
------------------------------
تستخدم أدوات البحث لاسترجاع المحتوى التعليمي.
"""

import logging

from app.services.chat.graph.search import build_graph_search_plan
from app.services.chat.graph.state import AgentState
from app.services.chat.tools import ToolRegistry

logger = logging.getLogger(__name__)


async def researcher_node(state: AgentState, tools: ToolRegistry) -> dict:
    """
    عقدة البحث: تنفذ أدوات البحث بناءً على سياق الرسائل.
    """
    # 1. Extract params (Simplified here, in reality we might call LLM again or use Orchestrator logic)
    # For now, we assume the last user message contains the query.
    # Ideally, we should check if the PLANNER passed specific search queries.

    # Check if we have a search query in the state? No, let's derive from conversation.
    # In a full agent, we might have a specific 'generate_search_query' step.
    # Here we reuse the Orchestrator's heuristics or Tool calls.

    # We will assume a simple "search_content" call for now using the raw message.
    # A better approach: The Planner could have outputted a specific search query.

    search_plan = build_graph_search_plan(state)

    full_content: list[dict[str, object]] = []
    results: list[dict[str, object]] = []

    for query in search_plan.queries:
        params = {"q": query, "limit": 3}
        if "2024" in query:
            params["year"] = 2024
        if "رياضيات" in query:
            params["subject"] = "Mathematics"

        logger.info(f"Researcher searching for: {params}")
        results = await tools.execute("search_content", params)
        if results:
            break

    if results:
        top_result = results[0]
        raw = await tools.execute("get_content_raw", {"content_id": top_result["id"]})
        if raw:
            full_content.append(raw)

    return {
        "search_results": full_content,
        "current_step_index": state["current_step_index"] + 1,
    }
