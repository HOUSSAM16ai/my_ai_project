from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

# Lazy import to avoid hard dependency on llama_index if possible, but keeping strictly for now
from llama_index.core.schema import NodeWithScore

# Decoupled from microservices - now using domain models
from app.domain.models.agents import EvaluationResult, ReasoningNode

if TYPE_CHECKING:
    from app.services.chat.graph.domain import StudentProfile, WriterIntent


class IReasoningStrategy(ABC):
    @abstractmethod
    async def execute(self, root_content: str, context: str, depth: int = 2) -> ReasoningNode:
        pass

    @abstractmethod
    async def expand(self, parent: ReasoningNode, context: str) -> List[ReasoningNode]:
        pass

    @abstractmethod
    async def evaluate(self, node: ReasoningNode, context: str) -> EvaluationResult:
        pass


class IIntentDetector(ABC):
    @abstractmethod
    def analyze(self, user_message: str) -> "WriterIntent":
        pass


class IContextComposer(ABC):
    @abstractmethod
    def compose(
        self,
        search_results: list[dict[str, object]],
        intent: "WriterIntent",
        user_message: str,
    ) -> str:
        pass


class IPromptStrategist(ABC):
    @abstractmethod
    def build_prompt(self, profile: "StudentProfile", intent: "WriterIntent") -> str:
        pass


class IKnowledgeRetriever(ABC):
    @abstractmethod
    async def aretrieve(self, query: str) -> list[NodeWithScore]:
        pass
