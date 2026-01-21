import difflib

from sqlalchemy import text

from app.core.database import async_session_factory as default_session_factory
from app.services.content.domain import ContentDetail
from app.services.content.repository import ContentRepository

class ContentService:
    """طبقة خدمة لإدارة المحتوى مع توحيد المدخلات وبناء الاستعلامات."""

    # Dictionary of Canonical English Slug -> List of Variations (Arabic & English)
    BRANCH_MAP: dict[str, list[str]] = {
        "experimental_sciences": [
            "experimental_sciences",
            "experimental sciences",
            "experimental",
            "علوم تجريبية",
            "تجريبية",
            "علوم تجريبة",
            "science",
            "ex",
            "scien",
            "exp",
        ],
        "math_tech": [
            "math_tech",
            "math tech",
            "technical math",
            "تقني رياضي",
            "تقني",
            "math technique",
            "tm",
            "mt",
        ],
        "mathematics": [
            "mathematics",
            "mathematics_branch",
            "math branch",
            "رياضيات",
            "math",
            "m",
            "رياضي",
        ],
        "foreign_languages": [
            "foreign_languages",
            "languages",
            "لغات أجنبية",
            "لغات",
            "lang",
            "fl",
        ],
        "literature_philosophy": [
            "literature_philosophy",
            "literature",
            "آداب وفلسفة",
            "اداب وفلسفة",
            "اداب",
            "فلسفة",
            "lit",
            "philo",
            "lp",
        ],
    }

    SET_MAP: dict[str, list[str]] = {
        "subject_1": [
            "subject 1",
            "subject1",
            "s1",
            "sub1",
            "subject_1",
            "الموضوع الأول",
            "الموضوع الاول",
            "الموضوع 1",
            "subject-1",
            "first subject",
        ],
        "subject_2": [
            "subject 2",
            "subject2",
            "s2",
            "sub2",
            "subject_2",
            "الموضوع الثاني",
            "الموضوع الثانى",
            "الموضوع 2",
            "subject-2",
            "second subject",
        ],
    }

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or default_session_factory

    @staticmethod
    def _fuzzy_match(
        val: str | None,
        mapping: dict[str, list[str]],
        cutoff: float = 0.6,
    ) -> str | None:
        """يطبق مطابقة تقريبية لإرجاع القيمة المعيارية إن أمكن."""
        if not val:
            return None

        val_lower = val.lower().strip()

        for key, variations in mapping.items():
            if val_lower in variations:
                return key

        reverse_map: dict[str, str] = {}
        all_variations: list[str] = []
        for key, variations in mapping.items():
            for variation in variations:
                reverse_map[variation] = key
                all_variations.append(variation)

        matches = difflib.get_close_matches(val_lower, all_variations, n=1, cutoff=cutoff)
        if matches:
            return reverse_map[matches[0]]

        for variation in all_variations:
            if len(variation) > 3 and variation in val_lower:
                return reverse_map[variation]

        return val

    def normalize_set_name(self, val: str | None) -> str | None:
        """توحيد اسم المجموعة إلى الصيغة القياسية."""
        if val and val.strip() in ["1", "١"]:
            return "subject_1"
        if val and val.strip() in ["2", "٢"]:
            return "subject_2"

        return self._fuzzy_match(val, self.SET_MAP, cutoff=0.7)

    def normalize_branch(self, val: str | None) -> str | None:
        """توحيد أسماء الشعب إلى التسميات العربية المعيارية."""
        return self._fuzzy_match(val, self.BRANCH_MAP, cutoff=0.6)

    async def search_content(
        self,
        q: str | None = None,
        level: str | None = None,
        subject: str | None = None,
        branch: str | None = None,
        set_name: str | None = None,
        year: int | None = None,
        type: str | None = None,
        lang: str | None = None,
        content_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """يبني استعلام بحث هجين مع فلاتر وصفية متوافقة مع الاختبارات."""

        norm_set = self.normalize_set_name(set_name)
        norm_branch = self.normalize_branch(branch)

        query_str = (
            "SELECT i.id, i.title, i.type, i.level, i.subject, i.branch, "
            "i.set_name, i.year, i.lang "
            "FROM content_items i "
            "LEFT JOIN content_search cs ON i.id = cs.content_id "
            "WHERE 1=1"
        )
        params: dict[str, object] = {}

        if q:
            terms = [term for term in q.split() if term.strip()]
            term_clauses: list[str] = []
            for index, term in enumerate(terms):
                title_key = f"tq_{index}"
                body_key = f"bq_{index}"
                term_clauses.append(f"(i.title LIKE :{title_key} OR cs.plain_text LIKE :{body_key})")
                like_value = f"%{term}%"
                params[title_key] = like_value
                params[body_key] = like_value
            if term_clauses:
                query_str += " AND " + " AND ".join(term_clauses)

        if content_ids:
            # If we have explicit IDs from vector search, filter by them
            placeholders: list[str] = []
            for index, content_id in enumerate(content_ids):
                key = f"cid_{index}"
                placeholders.append(f":{key}")
                params[key] = content_id
            query_str += f" AND i.id IN ({', '.join(placeholders)})"

        if level:
            query_str += " AND i.level = :level"
            params["level"] = level

        if subject:
            query_str += " AND i.subject = :subject"
            params["subject"] = subject

        if norm_branch:
            query_str += " AND i.branch = :branch"
            params["branch"] = norm_branch

        if norm_set:
            query_str += " AND i.set_name = :set_name"
            params["set_name"] = norm_set

        if year is not None:
            query_str += " AND i.year = :year"
            params["year"] = year

        if type:
            query_str += " AND i.type = :type"
            params["type"] = type

        if lang:
            query_str += " AND i.lang = :lang"
            params["lang"] = lang

        query_str += " ORDER BY i.year DESC NULLS LAST, i.id ASC LIMIT :limit"
        params["limit"] = limit

        async with self.session_factory() as session:
            result = await session.execute(text(query_str), params)
            rows = result.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "type": row[2],
                "level": row[3],
                "subject": row[4],
                "branch": row[5],
                "set": row[6],
                "year": row[7],
                "lang": row[8],
            }
            for row in rows
        ]

    async def get_content_raw(self, content_id: str) -> dict[str, str] | None:
        async with self.session_factory() as session:
            repo = ContentRepository(session)
            detail = await repo.get_content_detail(content_id)

        if not detail:
            return None

        data = {"content": detail.content_md}
        if detail.solution_md:
            data["solution"] = detail.solution_md

        return data

    async def get_curriculum_structure(self, level: str | None = None) -> dict[str, object]:
        async with self.session_factory() as session:
            repo = ContentRepository(session)
            rows = await repo.get_tree_items(level)

        structure = {}
        for row in rows:
            # row is a result proxy, access by name
            # id, title, type, level, subject, branch, set_name, year
            subj = row.subject or "Uncategorized"
            lvl = row.level or "General"
            pack = row.set_name or "Misc"

            if subj not in structure:
                structure[subj] = {"type": "subject", "levels": {}}
            if lvl not in structure[subj]["levels"]:
                structure[subj]["levels"][lvl] = {"type": "level", "packs": {}}
            if pack not in structure[subj]["levels"][lvl]["packs"]:
                structure[subj]["levels"][lvl]["packs"][pack] = {"type": "pack", "items": []}

            structure[subj]["levels"][lvl]["packs"][pack]["items"].append({
                "id": row.id,
                "title": row.title or "Untitled",
                "type": row.type or "exercise",
                "year": row.year
            })

        return structure

# Singleton Instance
content_service = ContentService()
