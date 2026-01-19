"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر (Semantic Search via ContentRepository).
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

from typing import List, Optional, Dict, Any
import os
from sqlalchemy import text
from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.services.content.repository import ContentRepository
from app.services.content.domain import ContentFilter
from app.services.search_engine.query_refiner import get_refined_query
from app.core.config import get_settings

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
        repo = ContentRepository(session)
        rows = await repo.get_tree_items(level=level)

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
    USES DSPy (QueryRefiner) to optimize user queries.
    """
    async with async_session_factory() as session:
        repo = ContentRepository(session)

        # Normalize Filters
        norm_branch = _normalize_branch(branch)
        norm_set = _normalize_set_name(set_name)

        # --- DSPy INTELLIGENCE INJECTION ---
        refined_q = q
        if q and len(q.split()) > 1: # Only refine if enough context
            api_key = get_settings().OPENROUTER_API_KEY
            if api_key:
                try:
                    logger.info(f"DSPy Refining query: {q}")
                    refined_q = get_refined_query(q, api_key=api_key)
                    logger.info(f"DSPy Refined: {q} -> {refined_q}")
                except Exception as e:
                    logger.warning(f"DSPy failed, using original query: {e}")

        filters = ContentFilter(
            q=refined_q, # Pass the SMART query
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
                "lang": item.lang,
            })

        return items

async def get_content_raw(content_id: str) -> Optional[Dict[str, str]]:
    """
    جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر.
    """
    async with async_session_factory() as session:
        # We need raw SQL to fetch source_path because repository detail DTO might not have it exposed yet.
        # But wait, we should respect the repo pattern.
        # Let's check ContentDetail in Repo.

        query_str = """
            SELECT i.md_content, i.source_path, s.solution_md
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

        # Add Source URL for image/pdf access
        if row.source_path:
             # Convert local source path to accessible URL
             # Assuming 'content/' is mounted at root
             # Path: content/packs/bac2024/math.md
             # URL: /content/packs/bac2024/math.md
             # We need to strip 'content/' prefix from path if it exists, or just ensure relative path.

             rel_path = row.source_path
             if os.path.isabs(rel_path):
                 # Try to make it relative to CWD
                 try:
                     rel_path = os.path.relpath(rel_path, os.getcwd())
                 except ValueError:
                     pass # keep as is

             # Ensure URL compatible slashes
             rel_path = rel_path.replace("\\", "/")

             # If it starts with content/, the mount is at /content
             if not rel_path.startswith("/"):
                 rel_path = "/" + rel_path

             data["source_url"] = rel_path

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
