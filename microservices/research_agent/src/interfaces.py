"""واجهات مجردة محلية لخدمة البحث."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IKnowledgeRetriever(ABC):
    """واجهة مجردة لاسترجاع المعرفة."""

    @abstractmethod
    async def aretrieve(self, query: str) -> list[object]:
        pass
