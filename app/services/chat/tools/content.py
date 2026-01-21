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
        # Use DSPy for query refinement if an API Key is available
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if q and api_key:
            try:
                logger.info(f"Refining query with DSPy: {q}")
                # Run sync DSPy call in thread to avoid blocking loop
                refined_q = await asyncio.to_thread(get_refined_query, q, api_key)
                logger.info(f"Refined query: {refined_q}")
            except Exception as dspy_error:
                logger.warning(f"DSPy refinement failed, using original query: {dspy_error}")

        content_ids: list[str] = []

        if refined_q:
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

        # Delegate to ContentService
        # If refined_q is different from q, we should prefer passing refined_q?
        # Actually, ContentService does keyword search on 'q'.
        # If we found content_ids via LlamaIndex (semantic search), we pass them.
        # But if LlamaIndex fails or returns nothing, we still want keyword search.

        # If we have content_ids, they act as a filter in ContentService.
        # If refined_q is available, we pass it as 'q' for keyword highlighting/filtering within results.

        search_q = refined_q if refined_q else q

        return await content_service.search_content(
            q=search_q,
            level=level,
            subject=subject,
            branch=branch,
            set_name=set_name,
            year=year,
            type=type,
            lang=lang,
            content_ids=content_ids if content_ids else None,
            limit=limit,
        )

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
