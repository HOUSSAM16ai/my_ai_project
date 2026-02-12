"""
عقدة الباحث (Researcher Node).
------------------------------
تستخدم أدوات البحث لاسترجاع المحتوى التعليمي عبر Kagent Mesh.
Refactored for Unified Architecture.
"""

import contextlib
import logging
import re

from app.services.chat.graph.search import build_graph_search_plan
from app.services.chat.graph.state import AgentState
from app.services.kagent.domain import AgentRequest
from app.services.kagent.interface import KagentMesh
from app.domain.constants import BRANCH_MAP, SUBJECT_MAP

logger = logging.getLogger(__name__)


async def researcher_node(state: AgentState, kagent: KagentMesh) -> dict:
    """
    عقدة البحث: تنفذ أدوات البحث بناءً على سياق الرسائل باستخدام Kagent.
    """
    search_plan = build_graph_search_plan(state)

    results: list[dict] = []

    last_message = str(state.get("messages", [])[-1].content) if state.get("messages") else ""

    # We keep intent detection for building params, though ideally the Agent handles this.
    # For now, we pass clean params to the agent.

    params = {"limit": 5}

    # Use the first query from plan or the last message
    query = search_plan.queries[0] if search_plan.queries else last_message
    params["query"] = query

    # Dynamic Extraction Logic (Preserved but simplified)
    # ... (Logic to extract year/subject/branch) ...
    year_match = re.search(r"(20[1-2][0-9]|١٩|٢٠[١٢][٠-٩])", query)
    if year_match:
        year_str = year_match.group(1)
        arabic_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        with contextlib.suppress(ValueError):
            params["year"] = int(year_str.translate(arabic_to_western))

    query_lower = query.lower()
    for subject_key, variants in SUBJECT_MAP.items():
        if any(v in query_lower for v in variants):
            params["subject"] = subject_key
            break

    for branch_key, variants in BRANCH_MAP.items():
        if any(v in query_lower for v in variants):
            params["branch"] = branch_key
            break

    logger.info(f"Researcher executing via Kagent with params: {params}")

    # --- UNIFIED AGENT CALL ---
    request = AgentRequest(
        caller_id="researcher_node",
        target_service="research_agent",
        action="search",
        payload=params,
    )

    response = await kagent.execute_action(request)

    if response.status == "success":
        # Normalize data structure if needed
        data = response.data
        if isinstance(data, dict):
            results = data.get("results", [])
        elif isinstance(data, list):
            results = data

        return {
            "search_results": results,
            "current_step_index": state.get("current_step_index", 0) + 1,
        }

    logger.error(f"Research Agent failed: {response.error}")
    return {"search_results": [], "error": response.error}
