from abc import ABC, abstractmethod
from typing import Any

from app.domain.models.agents import (
    Plan,
    SearchRequest,
    SearchResult,
)


class IResearchService(ABC):
    @abstractmethod
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        pass

    @abstractmethod
    async def refine_query(self, query: str, api_key: str | None = None) -> dict[str, Any]:
        pass

    @abstractmethod
    async def deep_research(self, query: str) -> str:
        """Returns a markdown report."""
        pass


class IPlanningService(ABC):
    @abstractmethod
    async def generate_plan(self, goal: str, context: list[str] | None = None) -> Plan:
        pass


class IReasoningService(ABC):
    @abstractmethod
    async def reason(self, query: str, context: str | None = None) -> dict[str, Any]:
        pass
