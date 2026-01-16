"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app.core.database import async_session_factory
from app.core.logging import get_logger

logger = get_logger("content-tools")

async def get_curriculum_structure(level: Optional[str] = None, lang: str = "ar") -> Dict[str, Any]:
    """
    جلب شجرة المنهج الدراسي بالكامل أو لمستوى محدد.

    Structure: Subject -> Branch -> Set/Pack -> Lessons
    Returns IDs, titles, types, and counts.
    """
    async with async_session_factory() as session:
        # 1. Base Query
        query_str = """
            SELECT id, title, type, level, subject, set_name, year
            FROM content_items
            WHERE 1=1
        """
        params = {}

        if level:
            query_str += " AND level = :level"
            params["level"] = level

        # Order by hierarchy to make processing easier
        query_str += " ORDER BY subject, level, set_name, id"

        result = await session.execute(text(query_str), params)
        rows = result.fetchall()

    structure = {}

    # Process rows into a tree
    for row in rows:
        c_id = row.id
        title = row.title or "Untitled"
        c_type = row.type or "exercise"
        lvl = row.level or "General"
        subj = row.subject or "Uncategorized"
        pack = row.set_name or "Misc"
        year = row.year

        # Build hierarchy: Subject -> Level -> Pack -> Items
        if subj not in structure:
            structure[subj] = {"type": "subject", "levels": {}}

        if lvl not in structure[subj]["levels"]:
            structure[subj]["levels"][lvl] = {"type": "level", "packs": {}}

        if pack not in structure[subj]["levels"][lvl]["packs"]:
            structure[subj]["levels"][lvl]["packs"][pack] = {"type": "pack", "items": []}

        # Add Item
        item_data = {
            "id": c_id,
            "title": title,
            "type": c_type,
            "year": year
        }
        structure[subj]["levels"][lvl]["packs"][pack]["items"].append(item_data)

    return structure

async def search_content(
    q: Optional[str] = None,
    level: Optional[str] = None,
    subject: Optional[str] = None,
    set_name: Optional[str] = None,
    type: Optional[str] = None,
    lang: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    بحث متقدم عن المحتوى التعليمي.
    يرجع قائمة بالنتائج مع IDs لتمكين الوكيل من الاختيار.
    """
    async with async_session_factory() as session:
        query_str = """
            SELECT id, title, type, level, subject, set_name, year, lang
            FROM content_items
            WHERE 1=1
        """
        params = {}

        if q:
            # Smart Keyword Splitting (Improved LIKE)
            # Split query by spaces to allow "Math 2024" to match "2024 Math"
            keywords = q.strip().split()
            if keywords:
                for i, keyword in enumerate(keywords):
                    # Clean keyword
                    clean_kw = keyword.strip()
                    if not clean_kw:
                        continue

                    param_key = f"q_{i}"
                    # AND logic for each keyword: item must contain ALL keywords
                    query_str += f" AND (title LIKE :{param_key} OR md_content LIKE :{param_key})"
                    params[param_key] = f"%{clean_kw}%"

        if level:
            query_str += " AND level = :level"
            params["level"] = level

        if subject:
            query_str += " AND subject = :subject"
            params["subject"] = subject

        if set_name:
            query_str += " AND set_name = :set_name"
            params["set_name"] = set_name

        if type:
            query_str += " AND type = :type"
            params["type"] = type

        if lang:
            query_str += " AND lang = :lang"
            params["lang"] = lang

        query_str += " ORDER BY year DESC, id ASC LIMIT :limit"
        params["limit"] = limit

        result = await session.execute(text(query_str), params)
        rows = result.fetchall()

    items = []
    for row in rows:
        items.append({
            "id": row.id,
            "title": row.title,
            "type": row.type,
            "level": row.level,
            "subject": row.subject,
            "set": row.set_name,
            "year": row.year,
            "lang": row.lang
        })

    return items

async def get_content_raw(content_id: str) -> Optional[Dict[str, str]]:
    """
    جلب النص الخام (Markdown) لتمرين أو درس معين.
    """
    async with async_session_factory() as session:
        query_str = "SELECT md_content FROM content_items WHERE id = :id"
        result = await session.execute(text(query_str), {"id": content_id})
        row = result.fetchone()

    if not row:
        return None

    return {"content": row[0]}

async def get_solution_raw(content_id: str) -> Optional[Dict[str, Any]]:
    """
    جلب الحل الرسمي (Official Solution) لتمرين.
    """
    async with async_session_factory() as session:
        query_str = """
            SELECT solution_md, steps_json, final_answer
            FROM content_solutions
            WHERE content_id = :id
        """
        result = await session.execute(text(query_str), {"id": content_id})
        row = result.fetchone()

    if not row:
        return None

    return {
        "solution_md": row.solution_md,
        "steps_json": row.steps_json,
        "final_answer": row.final_answer
    }
