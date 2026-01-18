"""
عقدة الباحث (Researcher Node).
------------------------------
تستخدم أدوات البحث لاسترجاع المحتوى التعليمي.
"""

from app.services.chat.graph.state import AgentState
from app.services.chat.tools import ToolRegistry
import logging

logger = logging.getLogger(__name__)

async def researcher_node(state: AgentState, tools: ToolRegistry) -> dict:
    """
    عقدة البحث: تنفذ أدوات البحث بناءً على سياق الرسائل.
    """
    messages = state["messages"]
    last_message = messages[-1].content

    # 1. Extract params (Simplified here, in reality we might call LLM again or use Orchestrator logic)
    # For now, we assume the last user message contains the query.
    # Ideally, we should check if the PLANNER passed specific search queries.

    # Check if we have a search query in the state? No, let's derive from conversation.
    # In a full agent, we might have a specific 'generate_search_query' step.
    # Here we reuse the Orchestrator's heuristics or Tool calls.

    # We will assume a simple "search_content" call for now using the raw message.
    # A better approach: The Planner could have outputted a specific search query.

    # Let's try to infer parameters using a heuristic for this node to be fast.
    params = {"q": last_message, "limit": 3}
    if "2024" in last_message: params["year"] = 2024
    if "رياضيات" in last_message: params["subject"] = "Mathematics"

    logger.info(f"Researcher searching for: {params}")

    results = await tools.execute("search_content", params)

    full_content = []

    if results:
        # Fetch raw content for top result
        top_result = results[0]
        raw = await tools.execute("get_content_raw", {"content_id": top_result["id"]})
        if raw:
             full_content.append(raw)

    return {
        "search_results": full_content,
        "current_step_index": state["current_step_index"] + 1
    }
