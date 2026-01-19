"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import os
import asyncio
from typing import List, Optional, Dict
from app.services.content.service import content_service
from app.services.search_engine.query_refiner import get_refined_query
from app.core.logging import get_logger

logger = get_logger("content-tools")

async def get_curriculum_structure(level: Optional[str] = None, lang: str = "ar") -> Dict[str, object]:
    """
    جلب شجرة المنهج الدراسي بالكامل أو لمستوى محدد.

    Structure: Subject -> Branch -> Set/Pack -> Lessons
    Returns IDs, titles, types, and counts.
    """
    try:
        return await content_service.get_curriculum_structure(level)
    except Exception as e:
        logger.error(f"Failed to fetch curriculum structure: {e}")
        return {}

async def search_content(
    q: Optional[str] = None,
    level: Optional[str] = None,
    subject: Optional[str] = None,
    branch: Optional[str] = None,
    set_name: Optional[str] = None,
    year: Optional[int] = None,
    type: Optional[str] = None,
    lang: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, object]]:
    """
    بحث متقدم عن المحتوى التعليمي.
    يرجع قائمة بالنتائج مع IDs لتمكين الوكيل من الاختيار.
    """
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

        return await content_service.search_content(
            q=refined_q,
            level=level,
            subject=subject,
            branch=branch,
            set_name=set_name,
            year=year,
            type=type,
            lang=lang,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Search content failed: {e}")
        return []

async def get_content_raw(content_id: str) -> Optional[Dict[str, str]]:
    """
    جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر.
    """
    try:
        return await content_service.get_content_raw(content_id)
    except Exception as e:
        logger.error(f"Get content raw failed: {e}")
        return None

async def get_solution_raw(content_id: str) -> Optional[Dict[str, object]]:
    """
    جلب الحل الرسمي (Official Solution) لتمرين.
    """
    data = await content_service.get_content_raw(content_id)
    if data and "solution" in data:
        return {
            "solution_md": data["solution"],
        }
    return None
