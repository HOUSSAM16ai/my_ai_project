"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import asyncio
import os

from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.services.content.service import content_service
from app.services.search_engine import get_retriever
from app.services.search_engine.query_refiner import get_refined_query

logger = get_logger("content-tools")


_SET_NAME_ALIASES: dict[str, set[str]] = {
    "subject_1": {
        "subject 1",
        "subject1",
        "s1",
        "sub1",
        "subject_1",
        "subject-1",
        "الموضوع الأول",
        "الموضوع الاول",
        "الموضوع 1",
    },
    "subject_2": {
        "subject 2",
        "subject2",
        "s2",
        "sub2",
        "subject_2",
        "subject-2",
        "الموضوع الثاني",
        "الموضوع الثانى",
        "الموضوع 2",
    },
}

_BRANCH_ALIASES: dict[str, set[str]] = {
    "علوم تجريبية": {
        "experimental_sciences",
        "experimental sciences",
        "experimental",
        "علوم تجريبية",
        "تجريبية",
        "علوم تجريبة",
        "science",
        "ex",
    },
    "تقني رياضي": {
        "math_tech",
        "math tech",
        "technical math",
        "math technique",
        "تقني رياضي",
        "تقني",
        "tm",
        "mt",
    },
    "لغات أجنبية": {
        "foreign_languages",
        "foreign languages",
        "languages",
        "لغات أجنبية",
        "لغات",
        "lang",
        "fl",
    },
}


def _normalize_set_name(value: str | None) -> str | None:
    """توحيد اسم المجموعة إلى صيغة معيارية متوافقة مع الاختبارات."""
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    for normalized, aliases in _SET_NAME_ALIASES.items():
        if cleaned in aliases:
            return normalized
    return value


def _normalize_branch(value: str | None) -> str | None:
    """توحيد اسم الشعبة إلى التسمية العربية المعيارية."""
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    for normalized, aliases in _BRANCH_ALIASES.items():
        if cleaned in aliases:
            return normalized
    return value


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

        normalized_set = _normalize_set_name(set_name)
        normalized_branch = _normalize_branch(branch)
        content_ids: list[str] = []

        if refined_q:
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                retriever = get_retriever(db_url)
                nodes = retriever.search(refined_q)
                for node in nodes:
                    metadata = getattr(node, "node", node)
                    meta = getattr(metadata, "metadata", {})
                    if isinstance(meta, dict):
                        content_id = meta.get("content_id")
                        if isinstance(content_id, str):
                            content_ids.append(content_id)

        query_str = (
            "SELECT i.id, i.title, i.type, i.level, i.subject, i.branch, "
            "i.set_name, i.year, i.lang "
            "FROM content_items i "
            "LEFT JOIN content_search cs ON i.id = cs.content_id "
            "WHERE 1=1"
        )
        params: dict[str, object] = {}

        if refined_q:
            terms = [term for term in refined_q.split() if term.strip()]
            term_clauses: list[str] = []
            params["q_full"] = refined_q
            for index, term in enumerate(terms):
                title_key = f"tq_{index}"
                body_key = f"bq_{index}"
                term_clauses.append(f"(i.title LIKE :{title_key} OR cs.plain_text LIKE :{body_key})")
                like_value = f"%{term}%"
                params[title_key] = like_value
                params[body_key] = like_value
            if term_clauses:
                query_str += " AND " + " AND ".join(term_clauses)

        if level:
            query_str += " AND i.level = :level"
            params["level"] = level

        if subject:
            query_str += " AND i.subject = :subject"
            params["subject"] = subject

        if normalized_set:
            query_str += " AND i.set_name = :set_name"
            params["set_name"] = normalized_set

        if normalized_branch:
            query_str += " AND i.title LIKE :branch_kw"
            params["branch_kw"] = f"%{normalized_branch}%"

        if content_ids:
            placeholders: list[str] = []
            for index, content_id in enumerate(content_ids):
                key = f"content_id_{index}"
                placeholders.append(f":{key}")
                params[key] = content_id
            query_str += f" AND i.id IN ({', '.join(placeholders)})"

        if year is not None:
            query_str += " AND i.year = :year"
            params["year"] = year

        if type:
            query_str += " AND i.type = :type"
            params["type"] = type

        if lang:
            query_str += " AND i.lang = :lang"
            params["lang"] = lang

        query_str += " LIMIT :limit"
        params["limit"] = limit

        async with async_session_factory() as session:
            result = await session.execute(text(query_str), params)
            rows = result.fetchall()

        def _row_value(row: object, attr: str, index: int) -> object:
            if hasattr(row, attr):
                return getattr(row, attr)
            return row[index]

        return [
            {
                "id": _row_value(row, "id", 0),
                "title": _row_value(row, "title", 1),
                "type": _row_value(row, "type", 2),
                "level": _row_value(row, "level", 3),
                "subject": _row_value(row, "subject", 4),
                "branch": _row_value(row, "branch", 5),
                "set": _row_value(row, "set_name", 6),
                "year": _row_value(row, "year", 7),
                "lang": _row_value(row, "lang", 8),
            }
            for row in rows
        ]
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
