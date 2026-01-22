"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import asyncio
import os

from app.core.logging import get_logger
from app.services.content.service import content_service
from app.services.search_engine import get_retriever
from app.services.search_engine.query_refiner import get_refined_query
from app.services.search_engine.fallback_expander import FallbackQueryExpander

logger = get_logger("content-tools")


async def get_curriculum_structure(
    level: str | None = None,
    lang: str = "ar",
) -> dict[str, object]:
    """جلب شجرة المنهج الدراسي بالكامل أو لمستوى محدد."""
    try:
        return await content_service.get_curriculum_structure(level)
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
) -> list[dict[str, object]]:
    """بحث متقدم عن المحتوى التعليمي مع فلاتر قابلة للتوسع."""
    try:
        refined_q = q
        api_key = os.environ.get("OPENROUTER_API_KEY")

        # 1. Try Smart Refinement (DSPy)
        if q and api_key:
            try:
                logger.info(f"Refining query with DSPy: {q}")
                refined_q = await asyncio.to_thread(get_refined_query, q, api_key)
                logger.info(f"Refined query: {refined_q}")
            except Exception as dspy_error:
                logger.warning(f"DSPy refinement failed: {dspy_error}")

        # 2. Fallback Refinement (Rule-based) if DSPy skipped or failed (refined_q is still just q)
        # We generate a list of queries to try sequentially.
        query_candidates = [refined_q] if refined_q else []

        if q and (refined_q == q):
            logger.info("Using fallback query expander to generate variations.")
            query_candidates = FallbackQueryExpander.generate_variations(q)

        content_ids: list[str] = []

        # We try to find content using the candidates.
        # First, check if LlamaIndex works for the first candidate (usually the most specific/refined one)
        # If LlamaIndex is active, it uses vector search which is robust.
        # If LlamaIndex is down/skipped, we rely on SQL keyword search loops.

        primary_q = query_candidates[0] if query_candidates else q

        if primary_q:
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                try:
                    retriever = get_retriever(db_url)
                    nodes = retriever.search(refined_q)
                    for node in nodes:
                        metadata = getattr(node, "node", node)
                        meta = getattr(metadata, "metadata", {})
                        if isinstance(meta, dict):
                            content_id = meta.get("content_id")
                            if isinstance(content_id, str):
                                content_ids.append(content_id)
                except Exception as e:
                    logger.warning(f"LlamaIndex search failed, falling back to basic search: {e}")

        # Delegate to ContentService with Fallback Loop
        # We iterate through query candidates until we find results or run out.

        results = []
        for candidate_q in query_candidates:
            logger.info(f"Searching content with query: '{candidate_q}'")

            # Attempt 1: Hybrid Search (Keywords + Vector IDs)
            if content_ids:
                logger.info(f"Applying vector filter with {len(content_ids)} IDs.")
                results = await content_service.search_content(
                    q=candidate_q,
                    level=level,
                    subject=subject,
                    branch=branch,
                    set_name=set_name,
                    year=year,
                    type=type,
                    lang=lang,
                    content_ids=content_ids,
                    limit=limit,
                )
                if results:
                    logger.info(f"Found {len(results)} results with query '{candidate_q}' and vector filter.")
                    return results
                else:
                    logger.info("Vector filter yielded 0 results. Retrying without vector IDs.")

            # Attempt 2: Pure Keyword Search (Fallback)
            results = await content_service.search_content(
                q=candidate_q,
                level=level,
                subject=subject,
                branch=branch,
                set_name=set_name,
                year=year,
                type=type,
                lang=lang,
                content_ids=None,
                limit=limit,
            )
            if results:
                logger.info(f"Found {len(results)} results with query '{candidate_q}' (Pure Keyword).")
                return results

        return results

    except Exception as e:
        logger.error(f"Search content failed: {e}")
        return []


async def get_content_raw(content_id: str) -> dict[str, str] | None:
    """جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر."""
    try:
        return await content_service.get_content_raw(content_id)
    except Exception as e:
        logger.error(f"Get content raw failed: {e}")
        return None


async def get_solution_raw(content_id: str) -> dict[str, object] | None:
    """جلب الحل الرسمي (Official Solution) لتمرين."""
    data = await content_service.get_content_raw(content_id)
    if data and "solution" in data:
        return {
            "solution_md": data["solution"],
        }
    return None
