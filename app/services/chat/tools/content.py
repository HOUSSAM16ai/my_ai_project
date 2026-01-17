"""
أدوات إدارة المحتوى التعليمي (Content Tools).

تتيح للوكلاء:
1. استكشاف هيكلة المنهج (Subject -> Branch -> Topic).
2. البحث عن تمارين ومحتوى باستخدام الفلاتر.
3. استرجاع المحتوى الخام (Raw Content) والحلول الرسمية.
"""

import re
from typing import cast
from sqlalchemy import text
from app.core.database import async_session_factory
from app.core.logging import get_logger

logger = get_logger("content-tools")


def _is_postgres(session: object) -> bool:
    """
    يتحقق مما إذا كان المحرك المستخدم هو PostgreSQL.
    """
    try:
        bind = session.get_bind()
    except Exception:
        return False
    if not bind:
        return False
    return bind.dialect.name == "postgresql"


def _should_force_exercise_type(search_query: str, explicit_type: str | None) -> bool:
    """
    يحدد ما إذا كان ينبغي فرض نوع المحتوى كتمرين بناءً على نص البحث.
    """
    if explicit_type:
        return False
    triggers = ("تمرين", "تمارين", "exercise", "exercises")
    return any(trigger in search_query for trigger in triggers)


def _has_explicit_exercise_request(search_query: str) -> bool:
    """
    يتحقق مما إذا كان الاستعلام يطلب تمرينًا محددًا صراحة.
    """
    normalized = _normalize_query(search_query)
    triggers = ("تمرين", "التمرين", "exercise")
    return any(trigger in normalized for trigger in triggers)


def _normalize_query(search_query: str) -> str:
    """
    يطبع نص البحث لتقليل اختلافات الكتابة العربية البسيطة.
    """
    normalized = search_query.strip().lower()
    normalized = normalized.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    normalized = normalized.replace("ى", "ي").replace("ة", "ه")
    normalized = _normalize_digits(normalized)
    normalized = " ".join(normalized.split())
    return normalized


def _normalize_digits(text: str) -> str:
    """
    يحول الأرقام العربية إلى أرقام لاتينية لتوحيد المطابقة.
    """
    table = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(table)


def _extract_exercise_number(search_query: str) -> int | None:
    """
    يستخرج رقم التمرين من نص البحث إن وجد.
    """
    normalized = _normalize_query(search_query)
    if "التمرين الاول" in normalized or "exercise 1" in normalized or "تمرين 1" in normalized:
        return 1
    if "التمرين الثاني" in normalized or "exercise 2" in normalized or "تمرين 2" in normalized:
        return 2
    if "التمرين الثالث" in normalized or "exercise 3" in normalized or "تمرين 3" in normalized:
        return 3
    if "التمرين الرابع" in normalized or "exercise 4" in normalized or "تمرين 4" in normalized:
        return 4
    return None


def _extract_year(search_query: str) -> int | None:
    """
    يستخرج السنة من نص البحث إن وجدت.
    """
    match = re.search(r"\b(20\d{2})\b", search_query)
    if not match:
        return None
    return int(match.group(1))


def _infer_subject(search_query: str) -> str | None:
    """
    يستنتج المادة من نص البحث باستخدام قاموس بسيط للكلمات المفتاحية.
    """
    subject_map = {
        "Mathematics": ["math", "رياضيات", "رياضه", "maths", "mathematics"],
        "Physics": ["physics", "فيزياء"],
        "Experimental Sciences": ["علوم تجريبية", "علوم تجريبيه", "experimental sciences"],
    }
    for subject, keywords in subject_map.items():
        if any(keyword in search_query for keyword in keywords):
            return subject
    return None


def _extract_set_name(search_query: str) -> str | None:
    """
    يستخرج اسم الموضوع أو المرجع العام (مثل: الموضوع الأول) من نص البحث.
    """
    normalized = _normalize_query(search_query)
    if "الموضوع الاول" in normalized or "موضوع 1" in normalized or "subject 1" in normalized:
        return "Subject 1"
    if "الموضوع الثاني" in normalized or "موضوع 2" in normalized or "subject 2" in normalized:
        return "Subject 2"
    if "الموضوع الثالث" in normalized or "موضوع 3" in normalized or "subject 3" in normalized:
        return "Subject 3"
    return None


def _expand_terms(search_query: str, normalized_query: str) -> list[str]:
    """
    يوسع الكلمات المفتاحية بمرادفات شائعة لزيادة دقة الاسترجاع.
    """
    base_terms = set(search_query.split())
    base_terms.update(normalized_query.split())
    expansions = {
        "احتمالات": {"الاحتمالات", "احتمال", "probability", "probabilities"},
        "probability": {"احتمالات", "الاحتمالات", "احتمال", "probabilities"},
        "تمرين": {"تمارين", "exercise", "exercises"},
        "بكالوريا": {"bac", "baccalaureate", "بكالوريا"},
    }
    expanded = set(base_terms)
    for term in list(base_terms):
        for key, variants in expansions.items():
            if term == key:
                expanded.update(variants)
    return [term for term in expanded if term]


def _extract_topic_keywords(normalized_query: str) -> list[str]:
    """
    يستخرج كلمات موضوعية من الاستعلام لتقوية الترتيب الدلالي.
    """
    topic_map = {
        "احتمالات": ["احتمالات", "الاحتمالات", "احتمال", "probability", "probabilities"],
        "دوال": ["دوال", "الدوال", "functions", "function"],
        "متتاليات": ["متتاليات", "المتتاليات", "sequences", "sequence"],
        "هندسة": ["هندسة", "الهندسة", "geometry"],
        "اعداد مركبة": ["اعداد مركبة", "الأعداد المركبة", "complex numbers", "complex"],
        "تفاضل": ["تفاضل", "المعادلات التفاضلية", "differential", "differential equations"],
    }
    keywords: list[str] = []
    for variants in topic_map.values():
        if any(token in normalized_query for token in variants):
            keywords.extend(variants)
    return keywords


def _build_search_query(
    search_query: str,
    terms: list[str],
    params: dict[str, object],
    force_type: str | None,
    session: object,
) -> str:
    """
    يبني استعلام البحث مع ترتيب النتائج حسب أفضل تطابق.
    """
    is_postgres = _is_postgres(session)
    query_str = """
        SELECT i.id, i.title, i.type, i.level, i.subject, i.set_name, i.year, i.lang
        FROM content_items i
    """

    if search_query:
        query_str += " LEFT JOIN content_search cs ON i.id = cs.content_id"

    query_str += " WHERE 1=1"

    if search_query:
        normalized_query = _normalize_query(search_query)
        exercise_number = _extract_exercise_number(normalized_query)
        params["q_full"] = search_query
        title_terms: list[str] = []
        title_score_terms: list[str] = []
        for idx, term in enumerate(terms):
            title_key = f"tq_{idx}"
            params[title_key] = f"%{term}%"
            if is_postgres:
                title_terms.append(f"i.title ILIKE :{title_key}")
            else:
                title_terms.append(f"i.title LIKE :{title_key}")
            if is_postgres:
                title_score_terms.append(f"CASE WHEN i.title ILIKE :{title_key} THEN 1 ELSE 0 END")
            else:
                title_score_terms.append(f"CASE WHEN i.title LIKE :{title_key} THEN 1 ELSE 0 END")

        title_clause = " AND ".join(title_terms)
        title_score = " + ".join(title_score_terms) if title_score_terms else "0"
        exact_title_match = "CASE WHEN i.title = :exact_title THEN 3 ELSE 0 END"
        params["exact_title"] = search_query
        topic_keywords = _extract_topic_keywords(normalized_query)
        topic_score_terms: list[str] = []
        for idx, keyword in enumerate(topic_keywords):
            key = f"topic_{idx}"
            params[key] = f"%{keyword}%"
            if is_postgres:
                topic_score_terms.append(f"CASE WHEN i.title ILIKE :{key} THEN 1 ELSE 0 END")
            else:
                topic_score_terms.append(f"CASE WHEN i.title LIKE :{key} THEN 1 ELSE 0 END")
        topic_score = " + ".join(topic_score_terms) if topic_score_terms else "0"

        if is_postgres:
            body_clause = "cs.tsvector @@ websearch_to_tsquery('arabic', :q_full)"
            rank_expr = "ts_rank_cd(cs.tsvector, websearch_to_tsquery('arabic', :q_full))"
        else:
            body_terms: list[str] = []
            for idx, term in enumerate(terms):
                body_key = f"bq_{idx}"
                params[body_key] = f"%{term}%"
                body_terms.append(f"cs.plain_text LIKE :{body_key}")
            body_clause = " AND ".join(body_terms) if body_terms else ""
            rank_expr = "0"

        exercise_rank = "0"
        if exercise_number is not None:
            params["exercise_num"] = str(exercise_number)
            if is_postgres:
                exercise_rank = (
                    "CASE WHEN i.title ILIKE '%التمرين%' AND i.title LIKE '%' || :exercise_num || '%' "
                    "THEN 2 ELSE 0 END"
                )
            else:
                exercise_rank = (
                    "CASE WHEN i.title LIKE '%التمرين%' AND i.title LIKE '%' || :exercise_num || '%' "
                    "THEN 2 ELSE 0 END"
                )

        if title_clause and body_clause:
            query_str += f" AND (({title_clause}) OR ({body_clause}))"
        elif title_clause:
            query_str += f" AND ({title_clause})"
        elif body_clause:
            query_str += f" AND ({body_clause})"

        if _should_force_exercise_type(search_query, force_type):
            query_str += " AND i.type = :implicit_type"
            params["implicit_type"] = "exercise"

        query_str += (
            f" ORDER BY {exact_title_match} DESC, {exercise_rank} DESC, {topic_score} DESC, "
            f"{title_score} DESC, {rank_expr} DESC, i.year DESC, i.id ASC"
        )
    else:
        query_str += " ORDER BY i.year DESC, i.id ASC"

    return query_str


async def get_curriculum_structure(level: str | None = None, lang: str = "ar") -> dict[str, object]:
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
        params: dict[str, object] = {}

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

    structure: dict[str, object] = {}

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
            "year": year,
        }
        structure[subj]["levels"][lvl]["packs"][pack]["items"].append(item_data)

    return structure


async def search_content(
    q: str | None = None,
    level: str | None = None,
    subject: str | None = None,
    year: int | None = None,
    set_name: str | None = None,
    type: str | None = None,
    lang: str | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    """
    بحث متقدم عن المحتوى التعليمي.
    يرجع قائمة بالنتائج مع IDs لتمكين الوكيل من الاختيار.
    """
    async with async_session_factory() as session:
        params: dict[str, object] = {}
        search_query = (q or "").strip()
        normalized_query = _normalize_query(search_query)
        terms = _expand_terms(search_query, normalized_query)
        exercise_number = _extract_exercise_number(normalized_query)
        explicit_exercise_request = _has_explicit_exercise_request(search_query)
        query_str = _build_search_query(
            search_query=search_query,
            terms=terms,
            params=params,
            force_type=type,
            session=session,
        )

        inferred_year = _extract_year(normalized_query)
        inferred_subject = _infer_subject(normalized_query)
        inferred_set_name = _extract_set_name(normalized_query)

        if level:
            query_str += " AND i.level = :level"
            params["level"] = level

        if subject:
            query_str += " AND i.subject = :subject"
            params["subject"] = subject
        elif inferred_subject:
            query_str += " AND i.subject = :subject"
            params["subject"] = inferred_subject

        if year is not None:
            query_str += " AND i.year = :year"
            params["year"] = year
        elif inferred_year is not None:
            query_str += " AND i.year = :year"
            params["year"] = inferred_year

        if set_name:
            query_str += " AND i.set_name = :set_name"
            params["set_name"] = set_name
        elif inferred_set_name:
            if _is_postgres(session):
                query_str += " AND i.set_name ILIKE :set_name"
            else:
                query_str += " AND i.set_name LIKE :set_name"
            params["set_name"] = f"%{inferred_set_name}%"

        if type:
            query_str += " AND i.type = :type"
            params["type"] = type
        elif explicit_exercise_request:
            query_str += " AND i.type = :type"
            params["type"] = "exercise"

        if explicit_exercise_request and exercise_number is not None:
            params["exercise_num_exact"] = f"%{exercise_number}%"
            if _is_postgres(session):
                query_str += " AND i.title ILIKE '%التمرين%' AND i.title ILIKE :exercise_num_exact"
            else:
                query_str += " AND i.title LIKE '%التمرين%' AND i.title LIKE :exercise_num_exact"

        if lang:
            query_str += " AND i.lang = :lang"
            params["lang"] = lang

        query_str += " LIMIT :limit"
        params["limit"] = limit

        try:
            result = await session.execute(text(query_str), params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Search content failed: {e}")
            return []

    items: list[dict[str, object]] = []
    for row in rows:
        items.append(
            {
                "id": row.id,
                "title": row.title,
                "type": row.type,
                "level": row.level,
                "subject": row.subject,
                "set": row.set_name,
                "year": row.year,
                "lang": row.lang,
            }
        )

    # Deduplicate (JOIN might cause dupes if multiple matches in search table? No, 1:1)
    # But just in case
    seen: set[str] = set()
    unique_items: list[dict[str, object]] = []
    for item in items:
        item_id = cast(str, item["id"])
        if item_id not in seen:
            unique_items.append(item)
            seen.add(item_id)

    return unique_items


async def get_content_raw(content_id: str) -> dict[str, str] | None:
    """
    جلب النص الخام (Markdown) لتمرين أو درس معين، مع الحل إذا توفر.
    """
    async with async_session_factory() as session:
        # Fetch content and solution in one go (or separate queries)
        # Using LEFT JOIN to get solution if exists
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


async def get_solution_raw(content_id: str) -> dict[str, object] | None:
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
        "final_answer": row.final_answer,
    }
