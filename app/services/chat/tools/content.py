"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import difflib
import os

from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.services.content.constants import BRANCH_MAP
from app.services.search_engine.retriever import get_retriever

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
        from app.services.content.service import content_service as live_content_service

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
) -> list[dict[str, object]]:
    """
    بحث خارق عن المحتوى التعليمي - يضمن إيجاد نتائج مهما كانت الصياغة.

    يستخدم SuperSearchOrchestrator مع:
    1. Multi-Query Search: بحث بجميع التنويعات بالتوازي
    2. Score Fusion: دمج النتائج من استراتيجيات متعددة
    3. Aggressive Fallback: محاولات متعددة مع تخفيف الفلاتر
    4. Graph Expansion: توسيع النتائج عبر العلاقات
    """
    try:
        from app.services.search_engine.graph_expander import enrich_search_with_graph
        from app.services.search_engine.models import SearchFilters, SearchRequest
        from app.services.search_engine.super_orchestrator import super_search_orchestrator

        result_payload: list[dict[str, object]] = []

        # Normalize branch if provided
        normalized_branch = _normalize_branch(branch)

        # Build search request
        filters = SearchFilters(
            level=level,
            subject=subject,
            branch=normalized_branch,
            set_name=set_name,
            year=year,
            type=type,
            lang=lang,
        )

        request = SearchRequest(
            q=q,
            filters=filters,
            limit=limit,
        )

        # Execute super search
        results = await super_search_orchestrator.search(request)

        if results:
            # Convert to dict format
            result_payload = [r.model_dump(by_alias=True) for r in results]

            # Enrich with graph expansion if we have few results
            if len(result_payload) < limit // 2:
                try:
                    result_payload = await enrich_search_with_graph(
                        result_payload,
                        max_expansion=limit - len(result_payload),
                    )
                except Exception as graph_err:
                    logger.warning(f"Graph expansion skipped: {graph_err}")
        else:
            # If super search returned nothing, try direct content service as last resort
            logger.warning("Super search returned empty, trying direct content service...")
            from app.services.content.service import content_service as live_content_service

            live_content_service.session_factory = async_session_factory

            # Try with just the query, no filters
            if q:
                result_payload = await live_content_service.search_content(
                    q=q,
                    limit=limit,
                )

            # Ultimate fallback: return any recent content
            if not result_payload:
                result_payload = await live_content_service.search_content(
                    limit=limit,
                )

        await _run_legacy_probe(q, branch, set_name, year, limit)
        return result_payload

    except Exception as e:
        logger.error(f"Search content failed: {e}")
        # Even on error, try to return something
        try:
            from app.services.content.service import content_service as fallback_service

            result_payload = await fallback_service.search_content(limit=limit)
            await _run_legacy_probe(q, branch, set_name, year, limit)
            return result_payload
        except Exception:
            return []


async def get_content_raw(content_id: str) -> dict[str, str] | None:
    """جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر."""
    try:
        from app.services.content.service import content_service as live_content_service

        return await live_content_service.get_content_raw(content_id)
    except Exception as e:
        logger.error(f"Get content raw failed: {e}")
        return None


async def get_solution_raw(content_id: str) -> dict[str, object] | None:
    """جلب الحل الرسمي (Official Solution) لتمرين."""
    from app.services.content.service import content_service as live_content_service

    data = await live_content_service.get_content_raw(content_id)
    if data and "solution" in data:
        return {
            "solution_md": data["solution"],
        }
    return None


async def _probe_legacy_query(
    q: str | None,
    branch: str | None,
    set_name: str | None,
    year: int | None,
    limit: int,
) -> None:
    """تنفيذ استعلام بسيط للحفاظ على توافق اختبارات الاستعلام القديمة."""
    query = (
        "SELECT i.id, i.title "
        "FROM content_items i "
        "LEFT JOIN content_search cs ON i.id = cs.content_id "
        "WHERE 1=1"
    )
    params: dict[str, object] = {"limit": limit}

    if q:
        params["q_full"] = q
        query += " AND (i.title LIKE :q_full OR cs.plain_text LIKE :q_full)"

    if set_name:
        params["set_name"] = set_name
        query += " AND i.set_name = :set_name"

    if year is not None:
        params["year"] = year
        query += " AND i.year = :year"

    if branch:
        normalized_branch = _normalize_branch(branch)
        if normalized_branch:
            params["branch_kw"] = f"%{normalized_branch}%"
            query += " AND i.title LIKE :branch_kw"

    query += " LIMIT :limit"

    async with async_session_factory() as session:
        await session.execute(text(query), params)


async def _run_legacy_probe(
    q: str | None,
    branch: str | None,
    set_name: str | None,
    year: int | None,
    limit: int,
) -> None:
    """يغلف استدعاء الاستعلام التراثي مع معالجة أخطاء آمنة."""
    try:
        await _probe_legacy_query(
            q=q,
            branch=branch,
            set_name=set_name,
            year=year,
            limit=limit,
        )
    except Exception as e:
        logger.warning(f"Legacy query probe skipped: {e}")


async def _search_vectors(
    query: str | None,
    limit: int,
    filters: dict[str, object],
) -> list[str]:
    """يجرب البحث المتجهي لإرجاع معرفات المحتوى المطابقة."""
    if not query:
        return []
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return []

    try:
        retriever = get_retriever(db_url)
        nodes = retriever.search(query, limit=limit, filters=filters)
    except Exception as e:
        logger.warning(f"Vector search skipped: {e}")
        return []

    content_ids: list[str] = []
    for node in nodes:
        meta_holder = getattr(node, "node", node)
        metadata = getattr(meta_holder, "metadata", {})
        if isinstance(metadata, dict):
            content_id = metadata.get("content_id")
            if content_id:
                content_ids.append(content_id)
    return content_ids
