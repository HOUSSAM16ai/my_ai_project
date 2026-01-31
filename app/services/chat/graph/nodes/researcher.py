"""
عقدة الباحث (Researcher Node).
------------------------------
تستخدم أدوات البحث لاسترجاع المحتوى التعليمي.
"""

import contextlib
import logging
import re

from app.services.chat.graph.components.intent_detector import RegexIntentDetector
from app.services.chat.graph.domain import WriterIntent
from app.services.chat.graph.search import build_graph_search_plan
from app.services.chat.graph.state import AgentState
from app.services.chat.tools import ToolRegistry
from microservices.research_agent.src.content.constants import BRANCH_MAP, SUBJECT_MAP

logger = logging.getLogger(__name__)


async def researcher_node(state: AgentState, tools: ToolRegistry) -> dict:
    """
    عقدة البحث: تنفذ أدوات البحث بناءً على سياق الرسائل.

    يستخدم استخراج سياق ديناميكي للسنة والمادة والشعبة.
    """
    search_plan = build_graph_search_plan(state)

    full_content: list[dict[str, object]] = []
    results: list[dict[str, object]] = []

    last_message = str(state.get("messages", [])[-1].content) if state.get("messages") else ""
    intent_detector = RegexIntentDetector()
    writer_intent = intent_detector.analyze(last_message)
    include_solution = writer_intent == WriterIntent.SOLUTION_REQUEST

    for query in search_plan.queries:
        params = {"q": query, "limit": 5}

        # Dynamic year extraction (supports both Arabic and Western numerals)
        year_match = re.search(r"(20[1-2][0-9]|١٩|٢٠[١٢][٠-٩])", query)
        if year_match:
            year_str = year_match.group(1)
            # Convert Arabic numerals if needed
            arabic_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
            year_western = year_str.translate(arabic_to_western)
            with contextlib.suppress(ValueError):
                params["year"] = int(year_western)

        # Dynamic subject extraction
        query_lower = query.lower()
        for subject_key, variants in SUBJECT_MAP.items():
            for variant in variants:
                if variant in query_lower or variant in query:
                    params["subject"] = subject_key
                    break
            if "subject" in params:
                break

        # Dynamic branch extraction
        for branch_key, variants in BRANCH_MAP.items():
            for variant in variants:
                if variant in query_lower or variant in query:
                    params["branch"] = branch_key
                    break
            if "branch" in params:
                break

        logger.info(f"Researcher searching with dynamic params: {params}")
        results = await tools.execute("search_content", params)
        if results:
            break

    if results:
        # Fetch raw content for top results
        for result in results[:2]:  # Get top 2 results
            raw = await tools.execute(
                "get_content_raw",
                {"content_id": result["id"], "include_solution": include_solution},
            )
            if raw:
                full_content.append(raw)

    return {
        "search_results": full_content,
        "current_step_index": state["current_step_index"] + 1,
    }
