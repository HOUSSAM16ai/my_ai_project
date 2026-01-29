from abc import ABC, abstractmethod

from llama_index.core.schema import NodeWithScore

from app.core.domain.chat import StudentProfile, WriterIntent
from app.services.reasoning.models import EvaluationResult, ReasoningNode


class IReasoningStrategy(ABC):
    @abstractmethod
    async def execute(self, root_content: str, context: str, depth: int = 2) -> ReasoningNode:
        pass

    @abstractmethod
    async def expand(self, parent: ReasoningNode, context: str) -> list[ReasoningNode]:
        pass

    @abstractmethod
    async def evaluate(self, node: ReasoningNode, context: str) -> EvaluationResult:
        pass


class IIntentDetector(ABC):
    @abstractmethod
    def analyze(self, user_message: str) -> WriterIntent:
        pass


class IContextComposer(ABC):
    @abstractmethod
    def compose(self, search_results: list[dict[str, object]], intent: WriterIntent) -> str:
        pass


class IPromptStrategist(ABC):
    @abstractmethod
    def build_prompt(self, profile: StudentProfile, intent: WriterIntent) -> str:
        pass


class IKnowledgeRetriever(ABC):
    @abstractmethod
    async def aretrieve(self, query: str) -> list[NodeWithScore]:
        pass
