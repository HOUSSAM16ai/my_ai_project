from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from app.domain.models.agents import (
    ReasoningNode,
    EvaluationResult,
    Plan,
    SearchRequest,
    SearchResult
)

class IResearchService(ABC):
    @abstractmethod
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        pass

    @abstractmethod
    async def refine_query(self, query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def deep_research(self, query: str) -> str:
        """Returns a markdown report."""
        pass

class IPlanningService(ABC):
    @abstractmethod
    async def generate_plan(self, goal: str, context: Optional[List[str]] = None) -> Plan:
        pass

class IReasoningService(ABC):
    @abstractmethod
    async def reason(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        pass
