"""واجهات مجردة محلية لخدمة الاستدلال."""

from __future__ import annotations

from abc import ABC, abstractmethod

from microservices.reasoning_agent.src.models import EvaluationResult, ReasoningNode


class IReasoningStrategy(ABC):
    """واجهة مجردة لاستراتيجيات الاستدلال."""

    @abstractmethod
    async def execute(self, root_content: str, context: str, depth: int = 2) -> ReasoningNode:
        pass

    @abstractmethod
    async def expand(self, parent: ReasoningNode, context: str) -> list[ReasoningNode]:
        pass

    @abstractmethod
    async def evaluate(self, node: ReasoningNode, context: str) -> EvaluationResult:
        pass


class IKnowledgeRetriever(ABC):
    """واجهة مجردة لاسترجاع المعرفة."""

    @abstractmethod
    async def aretrieve(self, query: str) -> list[object]:
        pass
