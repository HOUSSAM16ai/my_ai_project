"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import difflib

from app.core.logging import get_logger
from microservices.research_agent.src.content.constants import BRANCH_MAP

logger = get_logger("content-tools")

_BRANCH_LABELS: dict[str, str] = {
    "experimental_sciences": "علوم تجريبية",
    "math_tech": "تقني رياضي",
    "mathematics": "رياضيات",
    "foreign_languages": "لغات أجنبية",
    "literature_philosophy": "آداب وفلسفة",
}


def _normalize_branch(value: str | None) -> str | None:
    """توحيد اسم الشعبة باستخدام منطق الخدمة الموحد."""
    if not value:
        return None

    normalized = value.strip().lower()
    for key, variants in BRANCH_MAP.items():
        if normalized in variants:
            return _BRANCH_LABELS.get(key, key)

    reverse_map: dict[str, str] = {}
    all_variants: list[str] = []
    for key, variants in BRANCH_MAP.items():
        for variant in variants:
            reverse_map[variant] = key
            all_variants.append(variant)

    matches = difflib.get_close_matches(normalized, all_variants, n=1, cutoff=0.6)
    if matches:
        return _BRANCH_LABELS.get(reverse_map[matches[0]], reverse_map[matches[0]])

    for variant in all_variants:
        if len(variant) > 3 and variant in normalized:
            return _BRANCH_LABELS.get(reverse_map[variant], reverse_map[variant])

    return value


async def get_curriculum_structure(
    level: str | None = None,
    lang: str = "ar",
) -> dict[str, object]:
    """جلب شجرة المنهج الدراسي بالكامل أو لمستوى محدد."""
    try:
        from microservices.research_agent.src.content.service import (
            content_service as live_content_service,
        )

        return await live_content_service.get_curriculum_structure(level)
    except Exception as e:
        logger.error(f"Failed to fetch curriculum structure: {e}")
        return {}


async def search_content(
    q: str | None = None,
    level: str | None = None,
    subject: str | None = None,
    branch: str | None = None,
    set_name: str | None = None,
    year: int | None = None,
    type: str | None = None,
    lang: str | None = None,
    limit: int = 10,
    **kwargs,
) -> list[dict[str, object]]:
    """
    Cognitive Research Infrastructure (CRI).
    Advanced deep-research engine. Use this for ALL information retrieval.
    It performs multi-step reasoning, scraping, and fact-checking using
    autonomous agents (Tavily/Firecrawl).
    Returns a detailed research report.
    """
    if kwargs:
        logger.warning(f"search_content received unexpected arguments: {kwargs}")

    if not q:
        return []

    from microservices.research_agent.src.search_engine.super_search import (
        SuperSearchOrchestrator,
    )

    # Normalize branch if provided
    normalized_branch = _normalize_branch(branch) if branch else branch

    # Build query context
    context_parts = []
    if subject:
        context_parts.append(f"Subject: {subject}")
    if normalized_branch:
        context_parts.append(f"Branch: {normalized_branch}")
    if year:
        context_parts.append(f"Year: {year}")
    if level:
        context_parts.append(f"Level: {level}")
    if type:
        context_parts.append(f"Type: {type}")

    full_query = q
    if context_parts:
        full_query += f" ({', '.join(context_parts)})"

    orchestrator = SuperSearchOrchestrator()
    report = await orchestrator.execute(full_query)

    return [
        {
            "id": "research_report",
            "title": f"Research Report: {q}",
            "content": report,
            "type": "report",
            "metadata": {"query": full_query, "source": "SuperSearchOrchestrator"},
        }
    ]


async def get_content_raw(
    content_id: str, *, include_solution: bool = True
) -> dict[str, str] | None:
    """جلب النص الخام (Markdown) لتمرين أو درس معين مع خيار الحل."""
    try:
        from microservices.research_agent.src.content.service import (
            content_service as live_content_service,
        )

        return await live_content_service.get_content_raw(
            content_id, include_solution=include_solution
        )
    except Exception as e:
        logger.error(f"Get content raw failed: {e}")
        return None


async def get_solution_raw(content_id: str) -> dict[str, object] | None:
    """جلب الحل الرسمي (Official Solution) لتمرين."""
    from microservices.research_agent.src.content.service import (
        content_service as live_content_service,
    )

    data = await live_content_service.get_content_raw(content_id, include_solution=True)
    if data and "solution" in data:
        return {
            "solution_md": data["solution"],
        }
    return None


def register_content_tools(registry: dict) -> None:
    """
    Register content tools into the provided registry.
    """
    registry["search_content"] = search_content
    registry["get_content_raw"] = get_content_raw
    registry["get_solution_raw"] = get_solution_raw
    registry["get_curriculum_structure"] = get_curriculum_structure

    logger.info("Content tools registered successfully in agent registry")
