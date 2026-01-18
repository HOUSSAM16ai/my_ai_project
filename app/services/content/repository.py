import logging
from typing import List, Optional, Tuple, Any

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.domain.content import ContentItem, ContentSearch, ContentSolution
from app.services.content.domain import ContentFilter, ContentSummary, ContentDetail

logger = logging.getLogger(__name__)

class ContentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, filters: ContentFilter) -> List[ContentSummary]:
        """
        Executes a search query against content_items and content_search.
        Uses Full Text Search if available (Postgres), otherwise falls back to LIKE.
        """
        # Base Query
        # We select distinct items
        query_str = """
            SELECT
                i.id, i.title, i.type, i.level, i.subject, i.branch, i.set_name, i.year, i.lang
            FROM content_items i
            LEFT JOIN content_search cs ON i.id = cs.content_id
            WHERE 1=1
        """
        params = {}

        # 1. Full Text / Keyword Search
        if filters.q:
            keywords = filters.q.strip()

            # Hybrid Approach:
            # - ILIKE for Title (High Precision)
            # - ILIKE for Body (High Recall fallback)

            terms = keywords.split()

            # Title Conditions
            title_conds = []
            for i, term in enumerate(terms):
                p_key = f"tq_{i}"
                title_conds.append(f"i.title LIKE :{p_key}")
                params[p_key] = f"%{term}%"
            title_clause = " AND ".join(title_conds)

            # Body Conditions
            body_conds = []
            for i, term in enumerate(terms):
                p_key = f"bq_{i}"
                body_conds.append(f"cs.plain_text LIKE :{p_key}")
                params[p_key] = f"%{term}%"
            body_clause = " AND ".join(body_conds)

            # Combine
            if title_clause and body_clause:
                 query_str += f" AND (({title_clause}) OR ({body_clause}))"
            elif title_clause:
                 query_str += f" AND ({title_clause})"
            elif body_clause:
                 query_str += f" AND ({body_clause})"

        # 2. Metadata Filters
        if filters.level:
            query_str += " AND i.level = :level"
            params["level"] = filters.level

        if filters.subject:
            query_str += " AND i.subject = :subject"
            params["subject"] = filters.subject

        if filters.branch:
            # EXACT MATCH on the new column
            query_str += " AND i.branch = :branch"
            params["branch"] = filters.branch

        if filters.set_name:
            query_str += " AND i.set_name = :set_name"
            params["set_name"] = filters.set_name

        if filters.year:
            query_str += " AND i.year = :year"
            params["year"] = filters.year

        if filters.type:
            query_str += " AND i.type = :type"
            params["type"] = filters.type

        if filters.lang:
            query_str += " AND i.lang = :lang"
            params["lang"] = filters.lang

        # Ordering and Limiting
        query_str += " ORDER BY i.year DESC NULLS LAST, i.id ASC LIMIT :limit"
        params["limit"] = filters.limit

        try:
            result = await self.session.execute(text(query_str), params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Repository Search Failed: {e}")
            return []

        # Map to Domain Objects
        items = []
        seen = set()
        for row in rows:
            if row.id in seen:
                continue
            seen.add(row.id)
            items.append(ContentSummary(
                id=row.id,
                title=row.title,
                type=row.type,
                level=row.level,
                subject=row.subject,
                branch=row.branch,
                set_name=row.set_name,
                year=row.year,
                lang=row.lang
            ))

        return items

    async def get_content_detail(self, content_id: str) -> Optional[ContentDetail]:
        """
        Retrieves raw markdown content and solution.
        """
        query_str = """
            SELECT i.id, i.md_content, s.solution_md, i.title
            FROM content_items i
            LEFT JOIN content_solutions s ON i.id = s.content_id
            WHERE i.id = :id
        """
        try:
            result = await self.session.execute(text(query_str), {"id": content_id})
            row = result.fetchone()
        except Exception as e:
            logger.error(f"Get Content Detail Failed: {e}")
            return None

        if not row:
            return None

        return ContentDetail(
            id=row.id,
            content_md=row.md_content,
            solution_md=row.solution_md,
            metadata={"title": row.title}
        )

    async def get_tree_items(self, level: Optional[str] = None) -> List[Any]:
        """
        Fetch items for curriculum tree construction.
        """
        query_str = """
            SELECT id, title, type, level, subject, branch, set_name, year
            FROM content_items
            WHERE 1=1
        """
        params = {}
        if level:
            query_str += " AND level = :level"
            params["level"] = level

        query_str += " ORDER BY subject, level, set_name, id"

        try:
            result = await self.session.execute(text(query_str), params)
            return result.fetchall()
        except Exception as e:
            logger.error(f"Get Tree Items Failed: {e}")
            return []
