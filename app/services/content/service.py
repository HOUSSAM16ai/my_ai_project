from typing import List, Optional, Dict, Callable
import difflib
from app.core.database import async_session_factory as default_session_factory
from app.services.content.repository import ContentRepository
from app.services.content.domain import ContentFilter, ContentSummary, ContentDetail

class ContentService:
    """
    Service Layer for Content Management.
    Implements Business Logic (Normalization, Caching, etc.)
    and orchestrates Data Access.
    """

    # Dictionary of Canonical Key -> List of Variations
    BRANCH_MAP = {
        "experimental_sciences": [
            "experimental_sciences", "experimental sciences", "experimental",
            "علوم تجريبية", "تجريبية", "علوم تجريبة", "تجريبة", "science", "ex",
            "scien", "exp"
        ],
        "math_tech": [
            "math_tech", "math tech", "technical math", "تقني رياضي", "تقني",
            "math technique", "tm", "mt"
        ],
        "mathematics": [
            "mathematics", "mathematics_branch", "math branch", "رياضيات",
            "math", "m", "رياضي"
        ],
        "foreign_languages": [
            "foreign_languages", "languages", "لغات أجنبية", "لغات", "lang", "fl"
        ],
        "literature_philosophy": [
            "literature_philosophy", "literature", "آداب وفلسفة", "اداب وفلسفة",
            "اداب", "فلسفة", "lit", "philo", "lp"
        ]
    }

    SET_MAP = {
        "subject_1": [
            "subject 1", "subject1", "s1", "sub1", "subject_1",
            "الموضوع الأول", "الموضوع الاول", "الموضوع 1", "subject-1", "first subject"
        ],
        "subject_2": [
            "subject 2", "subject2", "s2", "sub2", "subject_2",
            "الموضوع الثاني", "الموضوع الثانى", "الموضوع 2", "subject-2", "second subject"
        ]
    }

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or default_session_factory

    @staticmethod
    def _fuzzy_match(val: str, mapping: Dict[str, List[str]], cutoff: float = 0.6) -> Optional[str]:
        """
        Fuzzy matches a value against a dictionary of variations using difflib.
        Returns the canonical key if a match is found.
        """
        if not val:
            return None

        val_lower = val.lower().strip()

        # 1. Exact match check (fast path)
        for key, variations in mapping.items():
            if val_lower in variations:
                return key

        # 2. Fuzzy match
        # Flatten the map to valid_variations -> key
        reverse_map = {}
        all_variations = []
        for key, variations in mapping.items():
            for v in variations:
                reverse_map[v] = key
                all_variations.append(v)

        matches = difflib.get_close_matches(val_lower, all_variations, n=1, cutoff=cutoff)
        if matches:
            best_match = matches[0]
            return reverse_map[best_match]

        return val # Return original if no match found (pass-through)

    def normalize_set_name(self, val: str) -> Optional[str]:
        """
        Normalizes 'Subject 1', 'S1', 'الموضوع الأول' -> 'subject_1'
        """
        # Specific overrides for very short strings that might fuzzy match poorly
        if val and val.strip() in ["1", "١"]: return "subject_1"
        if val and val.strip() in ["2", "٢"]: return "subject_2"

        return self._fuzzy_match(val, self.SET_MAP, cutoff=0.7)

    def normalize_branch(self, val: str) -> Optional[str]:
        """
        Normalizes branch codes to database slugs (e.g., 'experimental_sciences').
        """
        return self._fuzzy_match(val, self.BRANCH_MAP, cutoff=0.6)

    async def search_content(
        self,
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

        # Normalize Inputs
        norm_set = self.normalize_set_name(set_name)
        norm_branch = self.normalize_branch(branch)

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

        async with self.session_factory() as session:
            repo = ContentRepository(session)
            results = await repo.search(filters)

        # Convert to dicts for API/Tool compatibility
        return [
            {
                "id": item.id,
                "title": item.title,
                "type": item.type,
                "level": item.level,
                "subject": item.subject,
                "branch": item.branch, # Now available
                "set": item.set_name,
                "year": item.year,
                "lang": item.lang
            }
            for item in results
        ]

    async def get_content_raw(self, content_id: str) -> Optional[Dict[str, str]]:
        async with self.session_factory() as session:
            repo = ContentRepository(session)
            detail = await repo.get_content_detail(content_id)

        if not detail:
            return None

        data = {"content": detail.content_md}
        if detail.solution_md:
            data["solution"] = detail.solution_md

        return data

    async def get_curriculum_structure(self, level: Optional[str] = None) -> Dict[str, object]:
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
