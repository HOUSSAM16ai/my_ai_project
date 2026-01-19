"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر (Semantic Search via ContentRepository).
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.services.content.repository import ContentRepository
from app.services.content.domain import ContentFilter

logger = get_logger("content-tools")

def _normalize_set_name(val: str) -> Optional[str]:
    """
    Normalizes 'Subject 1', 'S1', 'الموضوع الأول' -> 'subject_1'
    Ensures strict semantic matching for exam sets.
    """
    if not val:
        return None

    val_lower = val.lower().strip()

    # Map variations for Subject 1
    if val_lower in ("subject 1", "subject1", "s1", "sub1", "subject_1", "الموضوع الأول", "الموضوع 1", "subject-1"):
        return "subject_1"

    # Map variations for Subject 2
    if val_lower in ("subject 2", "subject2", "s2", "sub2", "subject_2", "الموضوع الثاني", "الموضوع 2", "subject-2"):
        return "subject_2"

    return val

def _normalize_branch(val: str) -> Optional[str]:
    """
    Normalizes branch input to the canonical database slug.

    Returns the slug to search for (e.g. "experimental_sciences").
    """
    if not val:
        return None

    val_lower = val.lower().strip()

    # Experimental Sciences
    if val_lower in ("experimental_sciences", "experimental sciences", "experimental", "علوم تجريبية", "تجريبية", "science"):
        return "experimental_sciences"

    # Math Technical
    if val_lower in ("math_tech", "math tech", "technical math", "تقني رياضي", "تقني"):
        return "math_tech"

    # Mathematics (Branch)
    if val_lower in ("mathematics", "mathematics_branch", "math branch", "رياضيات"):
        return "mathematics"

    # Foreign Languages
    if val_lower in ("foreign_languages", "languages", "لغات أجنبية", "لغات"):
        return "foreign_languages"

    # Literature
    if val_lower in ("literature_philosophy", "literature", "آداب وفلسفة"):
        return "literature_philosophy"

    # Economics
    if val_lower in ("management_economics", "economics", "management", "تسيير واقتصاد"):
        return "management_economics"

    return val

async def get_curriculum_structure(level: Optional[str] = None, lang: str = "ar") -> Dict[str, Any]:
    """
    جلب شجرة المنهج الدراسي بالكامل أو لمستوى محدد.

    Structure: Subject -> Branch -> Set/Pack -> Lessons
    Returns IDs, titles, types, and counts.
    """
    # Use Repository if possible, or keep optimized SQL here.
    # Repository has `get_tree_items`. Let's use it for consistency.
    async with async_session_factory() as session:
        repo = ContentRepository(session)
        rows = await repo.get_tree_items(level=level)
        # rows are sqlalchemy rows (id, title, type, level, subject, branch, set_name, year)

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
    branch: Optional[str] = None,
    set_name: Optional[str] = None,
    year: Optional[int] = None,
    type: Optional[str] = None,
    lang: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    بحث متقدم عن المحتوى التعليمي.
    يرجع قائمة بالنتائج مع IDs لتمكين الوكيل من الاختيار.

    USES ContentRepository for Semantic + Metadata Search.
    """
    async with async_session_factory() as session:
        repo = ContentRepository(session)

        # Normalize Filters
        norm_branch = _normalize_branch(branch)
        norm_set = _normalize_set_name(set_name)

        filters = ContentFilter(
            q=q,
            level=level,
            subject=subject,
            branch=norm_branch,
            set_name=norm_set,
            year=year,
            type=type,
            lang=lang,
            limit=limit
        )

        # Execute Semantic/Hybrid Search
        results = await repo.search(filters)

        # Map Domain Objects to Dicts for Agent
        items = []
        for item in results:
            items.append({
                "id": item.id,
                "title": item.title,
                "type": item.type,
                "level": item.level,
                "subject": item.subject,
                "branch": item.branch,
                "set": item.set_name,
                "year": item.year,
                "lang": item.lang
            })

        return items

async def get_content_raw(content_id: str) -> Optional[Dict[str, str]]:
    """
    جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر.
    """
    async with async_session_factory() as session:
        repo = ContentRepository(session)
        detail = await repo.get_content_detail(content_id)

        if not detail:
            return None

        data = {"content": detail.content_md}
        if detail.solution_md:
            data["solution"] = detail.solution_md

        return data

async def get_solution_raw(content_id: str) -> Optional[Dict[str, Any]]:
    """
    جلب الحل الرسمي (Official Solution) لتمرين.
    """
    # Repository doesn't expose raw solution struct yet, so we keep this query or add to repo.
    # For now, let's keep it here to avoid changing Repository interface too much unless needed.
    # But `get_content_detail` returns solution_md.
    # If we need `steps_json`, we might need a new method in Repo.
    # Let's keep the existing implementation for `steps_json` if Repo doesn't have it.

    async with async_session_factory() as session:
        query_str = """
            SELECT solution_md, steps_json, final_answer
            FROM content_solutions
            WHERE content_id = :id
        """
        try:
            result = await session.execute(text(query_str), {"id": content_id})
            row = result.fetchone()
        except Exception as e:
            logger.error(f"Get solution raw failed: {e}")
            return None

    if not row:
        return None

    return {
        "solution_md": row.solution_md,
        "steps_json": row.steps_json,
        "final_answer": row.final_answer
    }
