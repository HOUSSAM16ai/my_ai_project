"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import difflib

from app.core.logging import get_logger
from app.core.settings.base import get_settings
from app.domain.constants import BRANCH_MAP
from app.domain.models.agents import SearchRequest
from app.infrastructure.clients.http_research_client import HttpResearchClient
from app.services.chat.tools.schemas import SearchContentSchema

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
    # This requires a dedicated endpoint on Research Agent which is not yet available.
    # Returning empty structure to avoid monolith coupling.
    logger.warning("get_curriculum_structure called but not implemented remotely.")
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

    # --- Layer A: Schema Adapter & Validation ---
    try:
        explicit_args = {
            "q": q,
            "level": level,
            "subject": subject,
            "branch": branch,
            "set_name": set_name,
            "year": year,
            "type": type,
            "lang": lang,
            "limit": limit,
        }
        filtered_args = {k: v for k, v in explicit_args.items() if v is not None}
        raw_args = {**filtered_args, **kwargs}

        known_keys = set(explicit_args.keys()) | {"query"}
        unexpected = set(raw_args.keys()) - known_keys
        if unexpected:
            logger.warning(f"search_content received unexpected args (ignored): {unexpected}")

        validated_data = SearchContentSchema(**raw_args)

        q = validated_data.q
        # Other fields are in validated_data but we construct the Request object below

    except Exception as e:
        logger.error(f"Schema Validation Failed in search_content: {e}")
        raise e

    # ---------------------------------------------

    if not q:
        return []

    # Use HTTP Client instead of direct Orchestrator import
    try:
        settings = get_settings()
        client = HttpResearchClient(settings.RESEARCH_AGENT_URL)

        # Normalize branch if provided
        normalized_branch = (
            _normalize_branch(validated_data.branch)
            if validated_data.branch
            else validated_data.branch
        )

        # Build query context (mimicking original logic)
        context_parts = []
        if validated_data.subject:
            context_parts.append(f"Subject: {validated_data.subject}")
        if normalized_branch:
            context_parts.append(f"Branch: {normalized_branch}")
        if validated_data.year:
            context_parts.append(f"Year: {validated_data.year}")
        if validated_data.level:
            context_parts.append(f"Level: {validated_data.level}")
        if validated_data.type:
            context_parts.append(f"Type: {validated_data.type}")

        full_query = q
        if context_parts:
            full_query += f" ({', '.join(context_parts)})"

        # Using deep_research as per original docstring mentioning "Advanced deep-research engine"
        # The original code called 'SuperSearchOrchestrator.execute(full_query)' which is deep research.
        report = await client.deep_research(full_query)
        await client.close()

        return [
            {
                "id": "research_report",
                "title": f"Research Report: {q}",
                "content": report,
                "type": "report",
                "metadata": {"query": full_query, "source": "SuperSearchOrchestrator"},
            }
        ]
    except Exception as e:
        logger.error(f"Search Content Failed via HTTP: {e}")
        raise e


async def get_content_raw(
    content_id: str, *, include_solution: bool = True
) -> dict[str, str] | None:
    """جلب النص الخام (Markdown) لتمرين أو درس معين مع خيار الحل."""
    try:
        # Attempt retrieval via Search ID (Best Effort)
        settings = get_settings()
        client = HttpResearchClient(settings.RESEARCH_AGENT_URL)
        # We assume searching for the ID might return the item if indexed.
        req = SearchRequest(q=content_id, limit=1)
        results = await client.search(req)
        await client.close()

        if results:
            res = results[0]
            # Verify if result seems to match (optional)
            return {
                "content": res.content or "",
                "solution": "",  # Solution not exposed via search result model yet
            }
        return None
    except Exception as e:
        logger.error(f"Get content raw failed via HTTP: {e}")
        return None


async def get_solution_raw(content_id: str) -> dict[str, object] | None:
    """جلب الحل الرسمي (Official Solution) لتمرين."""
    # Solution retrieval not supported via basic search API yet.
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
