from typing import List, Optional, Dict, Any, Callable
from app.core.database import async_session_factory as default_session_factory
from app.services.content.repository import ContentRepository
from app.services.content.domain import ContentFilter, ContentSummary, ContentDetail

class ContentService:
    """
    Service Layer for Content Management.
    Implements Business Logic (Normalization, Caching, etc.)
    and orchestrates Data Access.
    """

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or default_session_factory

    @staticmethod
    def normalize_set_name(val: str) -> Optional[str]:
        """
        Normalizes 'Subject 1', 'S1', 'الموضوع الأول' -> 'subject_1'
        """
        if not val:
            return None
        val_lower = val.lower().strip()
        if val_lower in ("subject 1", "subject1", "s1", "sub1", "subject_1", "الموضوع الأول", "الموضوع 1", "subject-1"):
            return "subject_1"
        if val_lower in ("subject 2", "subject2", "s2", "sub2", "subject_2", "الموضوع الثاني", "الموضوع 2", "subject-2"):
            return "subject_2"
        return val

    @staticmethod
    def normalize_branch(val: str) -> Optional[str]:
        """
        Normalizes branch codes to Arabic Title Keyword equivalents.
        """
        if not val:
            return None
        val_lower = val.lower().strip()

        if val_lower in ("experimental_sciences", "experimental sciences", "experimental", "علوم تجريبية", "تجريبية", "science"):
            return "علوم تجريبية"
        if val_lower in ("math_tech", "math tech", "technical math", "تقني رياضي", "تقني"):
            return "تقني رياضي"
        if val_lower in ("mathematics_branch", "math branch", "رياضيات"):
            return "رياضيات"
        if val_lower in ("foreign_languages", "languages", "لغات أجنبية", "لغات"):
            return "لغات أجنبية"
        if val_lower in ("literature_philosophy", "literature", "آداب وفلسفة"):
            return "آداب وفلسفة"

        return val

    async def search_content(
        self,
        filters: Optional[ContentFilter] = None,
        # Allow passing distinct args for backward compatibility if needed,
        # but pure signature is better.
        q: Optional[str] = None,
        level: Optional[str] = None,
        subject: Optional[str] = None,
        branch: Optional[str] = None,
        set_name: Optional[str] = None,
        year: Optional[int] = None,
        type: Optional[str] = None,
        lang: Optional[str] = None,
        limit: int = 10
    ) -> List[ContentSummary]:

        # If ContentFilter object passed, use it, else build from args
        if filters:
            use_filters = filters
        else:
            norm_set = self.normalize_set_name(set_name)
            norm_branch = self.normalize_branch(branch)
            use_filters = ContentFilter(
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
            results = await repo.search(use_filters)
            # Return Domain Objects directly for internal service usage
            return results

    async def search_content_dict(self, **kwargs) -> List[Dict[str, Any]]:
        """Legacy helper returning dicts"""
        results = await self.search_content(**kwargs)
        return [
            {
                "id": item.id,
                "title": item.title,
                "type": item.type,
                "level": item.level,
                "subject": item.subject,
                "branch": item.branch,
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

    async def get_curriculum_structure(self, level: Optional[str] = None) -> Dict[str, Any]:
        async with self.session_factory() as session:
            repo = ContentRepository(session)
            rows = await repo.get_tree_items(level)

        structure = {}
        for row in rows:
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

def get_content_service():
    return content_service
