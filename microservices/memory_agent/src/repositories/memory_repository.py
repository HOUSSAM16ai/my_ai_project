"""
مستودع بيانات الذاكرة (Memory Repository).

يوفر طبقة الوصول للبيانات (Data Access Layer) لوكيل الذاكرة.
يطبق مبدأ Single Responsibility - المسؤولية الوحيدة هي التعامل مع قاعدة البيانات.

المبادئ:
- SOLID: Single Responsibility Principle
- SOLID: Dependency Inversion Principle (يعتمد على Protocol)
- Repository Pattern: فصل منطق الأعمال عن الوصول للبيانات
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from microservices.memory_agent.models import Memory, Tag


class MemoryRepository:
    """
    مستودع بيانات الذاكرة.

    يوفر عمليات CRUD للذاكرة والوسوم.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        تهيئة المستودع.

        Args:
            session: جلسة قاعدة البيانات.
        """
        self._session = session

    async def create_memory(self, content: str, tag_names: list[str]) -> Memory:
        """
        إنشاء عنصر ذاكرة جديد مع الوسوم.

        Args:
            content: محتوى الذاكرة.
            tag_names: أسماء الوسوم.

        Returns:
            Memory: عنصر الذاكرة المنشأ.
        """
        # Resolve or create tags
        db_tags = await self._resolve_tags(tag_names)

        # Create memory entry
        entry = Memory(content=content, tags=db_tags)
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry, attribute_names=["tags"])

        return entry

    async def search_by_query(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Memory]:
        """
        البحث عن عناصر ذاكرة بالاستعلام النصي.

        Args:
            query: نص البحث.
            limit: حد النتائج.

        Returns:
            list[Memory]: قائمة عناصر الذاكرة المطابقة.
        """
        normalized = query.strip().lower()

        statement = select(Memory).options(selectinload(Memory.tags))

        if normalized:
            statement = (
                statement.distinct()
                .outerjoin(Memory.tags)
                .where(
                    (col(Memory.content).ilike(f"%{normalized}%"))
                    | (col(Tag.name).ilike(f"%{normalized}%"))
                )
            )

        statement = statement.limit(limit)

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def search_with_filters(
        self,
        query: str,
        tags: list[str],
        limit: int = 10,
    ) -> list[Memory]:
        """
        البحث عن عناصر ذاكرة مع مرشحات الوسوم.

        Args:
            query: نص البحث.
            tags: وسوم التصفية.
            limit: حد النتائج.

        Returns:
            list[Memory]: قائمة عناصر الذاكرة المطابقة.
        """
        normalized = query.strip().lower()
        clean_tags = [tag.strip() for tag in tags if tag.strip()]

        statement = select(Memory).options(selectinload(Memory.tags))

        if normalized or clean_tags:
            statement = statement.distinct().outerjoin(Memory.tags)

        if normalized:
            statement = statement.where(
                (col(Memory.content).ilike(f"%{normalized}%"))
                | (col(Tag.name).ilike(f"%{normalized}%"))
            )

        if clean_tags:
            statement = statement.where(col(Tag.name).in_(clean_tags))

        statement = statement.limit(limit)

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, memory_id: UUID) -> Memory | None:
        """
        استرجاع ذاكرة بواسطة المعرف.

        Args:
            memory_id: معرف الذاكرة.

        Returns:
            Memory | None: عنصر الذاكرة أو None.
        """
        statement = select(Memory).options(selectinload(Memory.tags)).where(Memory.id == memory_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def _resolve_tags(self, tag_names: list[str]) -> list[Tag]:
        """
        استرجاع أو إنشاء الوسوم.

        Args:
            tag_names: أسماء الوسوم.

        Returns:
            list[Tag]: قائمة كائنات الوسوم.
        """
        db_tags = []
        for tag_name in tag_names:
            statement = select(Tag).where(Tag.name == tag_name)
            result = await self._session.execute(statement)
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                self._session.add(tag)
            db_tags.append(tag)
        return db_tags
