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

        try:
            result = await session.execute(text(query_str), params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch curriculum structure: {e}")
            return {}

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
    """
    async with async_session_factory() as session:
        params = {}

        # Base Query
        # We select items.
        query_str = """
            SELECT i.id, i.title, i.type, i.level, i.subject, i.branch, i.set_name, i.year, i.lang
            FROM content_items i
            LEFT JOIN content_search cs ON i.id = cs.content_id
            WHERE 1=1
        """

        if q:
            # Use Hybrid Search: Title Matching + Full Text Search (FTS) / Like Fallback
            keywords = q.strip()
            terms = keywords.split()

            # Title Conditions (AND logic for terms)
            title_conds = []
            for i, term in enumerate(terms):
                p_key = f"tq_{i}"
                title_conds.append(f"i.title LIKE :{p_key}")
                params[p_key] = f"%{term}%"
            title_clause = " AND ".join(title_conds)

            # Body Conditions (Fallback ILIKE for robustness on SQLite/Postgres hybrid)
            body_conds = []
            for i, term in enumerate(terms):
                p_key = f"bq_{i}"
                body_conds.append(f"cs.plain_text LIKE :{p_key}")
                params[p_key] = f"%{term}%"
            body_clause = " AND ".join(body_conds)

            if title_clause and body_clause:
                 query_str += f" AND (({title_clause}) OR ({body_clause}))"
            elif title_clause:
                 query_str += f" AND ({title_clause})"
            elif body_clause:
                 query_str += f" AND ({body_clause})"

        if level:
            query_str += " AND i.level = :level"
            params["level"] = level

        if subject:
            query_str += " AND i.subject = :subject"
            params["subject"] = subject

        if set_name:
            # Normalize to ensure "Subject 1" matches "subject_1" in DB
            norm_set = _normalize_set_name(set_name)
            query_str += " AND i.set_name = :set_name"
            params["set_name"] = norm_set

        if year:
            query_str += " AND i.year = :year"
            params["year"] = year

        if branch:
            # STRICT Branch Filtering using the new 'branch' column
            branch_slug = _normalize_branch(branch)
            if branch_slug:
                query_str += " AND i.branch = :branch"
                params["branch"] = branch_slug

        if type:
            query_str += " AND i.type = :type"
            params["type"] = type

        if lang:
            query_str += " AND i.lang = :lang"
            params["lang"] = lang

        query_str += " ORDER BY i.year DESC, i.id ASC LIMIT :limit"
        params["limit"] = limit

        try:
            result = await session.execute(text(query_str), params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Search content failed: {e}")
            return []

    items = []
    for row in rows:
        items.append({
            "id": row.id,
            "title": row.title,
            "type": row.type,
            "level": row.level,
            "subject": row.subject,
            "branch": row.branch,
            "set": row.set_name,
            "year": row.year,
            "lang": row.lang
        })

    # Deduplicate
    seen = set()
    unique_items = []
    for item in items:
        if item['id'] not in seen:
            unique_items.append(item)
            seen.add(item['id'])

    return unique_items

async def get_content_raw(content_id: str) -> Optional[Dict[str, str]]:
    """
    جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر.
    """
    async with async_session_factory() as session:
        # Fetch content and solution in one go
        query_str = """
            SELECT i.md_content, s.solution_md
            FROM content_items i
            LEFT JOIN content_solutions s ON i.id = s.content_id
            WHERE i.id = :id
        """
        try:
            result = await session.execute(text(query_str), {"id": content_id})
            row = result.fetchone()
        except Exception as e:
            logger.error(f"Get content raw failed: {e}")
            return None

    if not row:
        return None

    data = {"content": row.md_content}

    if row.solution_md:
        data["solution"] = row.solution_md

    return data

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
