from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.core.integration_kernel.ir import WorkflowPlan, RetrievalQuery, PromptProgram, ScoringSpec, AgentAction

class WorkflowEngine(ABC):
    """
    Interface for executing agent workflows (e.g., LangGraph).
    """
    @abstractmethod
    async def run(self, plan: WorkflowPlan) -> Dict[str, Any]:
        """
        Executes a workflow plan.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the health status of the workflow engine.
        """
        pass

class RetrievalEngine(ABC):
    """
    Interface for semantic retrieval (e.g., LlamaIndex).
    """
    @abstractmethod
    async def search(self, query: RetrievalQuery) -> Dict[str, Any]:
        """
        Performs a semantic search.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the health status of the retrieval engine.
        """
        pass

class PromptEngine(ABC):
    """
    Interface for prompt optimization and reasoning (e.g., DSPy).
    """
    @abstractmethod
    async def optimize(self, program: PromptProgram) -> Dict[str, Any]:
        """
        Runs a prompt program or optimization routine.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the health status of the prompt engine.
        """
        pass

class RankingEngine(ABC):
    """
    Interface for re-ranking documents (e.g., CrossEncoder, Cohere).
    """
    @abstractmethod
    async def rank(self, spec: ScoringSpec) -> Dict[str, Any]:
        """
        Ranks a list of documents against a query.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the health status of the ranking engine.
        """
        pass

class ActionEngine(ABC):
    """
    Interface for executing agent actions (e.g., Kagent).
    """
    @abstractmethod
    async def execute(self, action: AgentAction) -> Dict[str, Any]:
        """
        Executes a defined action.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the health status of the action engine.
        """
        pass
