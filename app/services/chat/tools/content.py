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

        # 2. Build Candidate List
        # Priority:
        # 1. Refined Query (usually English/Normalized)
        # 2. Expanded Variations of Original Query (Arabic Typos/Plurals)
        # 3. Original Query itself

        query_candidates = []
        if refined_q and refined_q != q:
            query_candidates.append(refined_q)

        # Always add fallback variations of the original query
        if q:
            variations = FallbackQueryExpander.generate_variations(q)
            for var in variations:
                if var not in query_candidates:
                    query_candidates.append(var)

        content_ids: list[str] = []

        # We try to find content using the candidates.
        # First, check if LlamaIndex works for the first candidate (usually the most specific/refined one)
        # If LlamaIndex is active, it uses vector search which is robust.

        primary_q = query_candidates[0] if query_candidates else q

        if primary_q:
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                try:
                    retriever = get_retriever(db_url)
                    # Try searching with the refined query first
                    nodes = retriever.search(primary_q)

                    # If no results and we have multiple candidates, maybe try the second one?
                    # For now, let's stick to primary for vector search to save time.

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
        unique_results = set()

        for candidate_q in query_candidates:
            logger.info(f"Searching content with query: '{candidate_q}'")

            # Attempt 1: Hybrid Search (Keywords + Vector IDs)
            if content_ids:
                logger.info(f"Applying vector filter with {len(content_ids)} IDs.")
                batch_results = await content_service.search_content(
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
                if batch_results:
                    logger.info(f"Found {len(batch_results)} results with query '{candidate_q}' and vector filter.")
                    return batch_results
                else:
                    logger.info("Vector filter yielded 0 results. Retrying without vector IDs.")

            # Attempt 2: Pure Keyword Search (Fallback)
            # This is where 'علوم تجربة' -> 'علوم تجريبية' expansion shines.
            batch_results = await content_service.search_content(
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

            if batch_results:
                logger.info(f"Found {len(batch_results)} results with query '{candidate_q}' (Pure Keyword).")
                # We could return immediately or accumulate?
                # Returning immediately is safer to avoid duplicates and mixing unrelated stuff.
                return batch_results

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
