"""
خدمة الذاكرة (Memory Service).

يحتوي على منطق الأعمال (Business Logic) لوكيل الذاكرة.
يطبق مبدأ Single Responsibility - المسؤولية الوحيدة هي منطق الأعمال.

المبادئ:
- SOLID: Single Responsibility Principle
- SOLID: Dependency Inversion Principle (يعتمد على Repository Protocol)
- Clean Architecture: فصل طبقة الأعمال عن البنية التحتية
"""

import logging

from microservices.memory_agent.src.repositories.memory_repository import (
    MemoryRepository,
)
from microservices.memory_agent.src.schemas.memory_schemas import (
    MemoryCreateRequest,
    MemoryResponse,
    MemorySearchRequest,
)

logger = logging.getLogger("memory-agent")


class MemoryService:
    """
    خدمة الذاكرة.

    مسؤولة عن تنسيق عمليات الذاكرة وتطبيق منطق الأعمال.
    """

    def __init__(self, repository: MemoryRepository) -> None:
        """
        تهيئة الخدمة.

        Args:
            repository: مستودع البيانات.
        """
        self._repository = repository

    async def create_memory(self, request: MemoryCreateRequest) -> MemoryResponse:
        """
        إنشاء عنصر ذاكرة جديد.

        Args:
            request: حمولة الإنشاء.

        Returns:
            MemoryResponse: بيانات الذاكرة المنشأة.
        """
        logger.info("إنشاء ذاكرة", extra={"tags": request.tags})

        entry = await self._repository.create_memory(
            content=request.content,
            tag_names=request.tags,
        )

        return MemoryResponse(
            entry_id=entry.id,
            content=entry.content,
            tags=[tag.name for tag in entry.tags],
        )

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
    ) -> list[MemoryResponse]:
        """
        البحث عن عناصر ذاكرة.

        Args:
            query: نص البحث.
            limit: حد النتائج.

        Returns:
            list[MemoryResponse]: قائمة النتائج.
        """
        logger.info("بحث بالاستعلام", extra={"query": query, "limit": limit})

        memories = await self._repository.search_by_query(query, limit)

        return [
            MemoryResponse(
                entry_id=m.id,
                content=m.content,
                tags=[t.name for t in m.tags],
            )
            for m in memories
        ]

    async def search_memories_with_filters(
        self,
        request: MemorySearchRequest,
    ) -> list[MemoryResponse]:
        """
        البحث عن عناصر ذاكرة مع مرشحات.

        Args:
            request: حمولة البحث الموسعة.

        Returns:
            list[MemoryResponse]: قائمة النتائج.
        """
        logger.info(
            "بحث عبر حمولة",
            extra={
                "query": request.query,
                "tags": request.filters.tags,
                "limit": request.limit,
            },
        )

        memories = await self._repository.search_with_filters(
            query=request.query,
            tags=request.filters.tags,
            limit=request.limit,
        )

        return [
            MemoryResponse(
                entry_id=m.id,
                content=m.content,
                tags=[t.name for t in m.tags],
            )
            for m in memories
        ]
