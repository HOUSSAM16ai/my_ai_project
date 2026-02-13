from typing import Dict, Any, Type
from app.core.integration_kernel.contracts import (
    WorkflowEngine, RetrievalEngine, PromptEngine, RankingEngine, ActionEngine
)

class PolicyConfig:
    """
    Configuration for the integration kernel.
    Can be loaded from environment variables or a config file.
    """
    DEFAULT_WORKFLOW_ENGINE: str = "langgraph"
    DEFAULT_RETRIEVAL_ENGINE: str = "llamaindex"
    DEFAULT_PROMPT_ENGINE: str = "dspy"
    DEFAULT_RANKING_ENGINE: str = "reranker"
    DEFAULT_ACTION_ENGINE: str = "kagent"

class PolicyManager:
    """
    Manages execution policies (latency, quality, cost).
    Currently implemented as a simple registry/factory.
    """
    def __init__(self):
        self._workflow_drivers: Dict[str, WorkflowEngine] = {}
        self._retrieval_drivers: Dict[str, RetrievalEngine] = {}
        self._prompt_drivers: Dict[str, PromptEngine] = {}
        self._ranking_drivers: Dict[str, RankingEngine] = {}
        self._action_drivers: Dict[str, ActionEngine] = {}

    def register_workflow_driver(self, name: str, driver: WorkflowEngine):
        self._workflow_drivers[name] = driver

    def register_retrieval_driver(self, name: str, driver: RetrievalEngine):
        self._retrieval_drivers[name] = driver

    def register_prompt_driver(self, name: str, driver: PromptEngine):
        self._prompt_drivers[name] = driver

    def register_ranking_driver(self, name: str, driver: RankingEngine):
        self._ranking_drivers[name] = driver

    def register_action_driver(self, name: str, driver: ActionEngine):
        self._action_drivers[name] = driver

    def get_workflow_driver(self, name: str = PolicyConfig.DEFAULT_WORKFLOW_ENGINE) -> WorkflowEngine:
        return self._workflow_drivers.get(name)

    def get_retrieval_driver(self, name: str = PolicyConfig.DEFAULT_RETRIEVAL_ENGINE) -> RetrievalEngine:
        return self._retrieval_drivers.get(name)

    def get_prompt_driver(self, name: str = PolicyConfig.DEFAULT_PROMPT_ENGINE) -> PromptEngine:
        return self._prompt_drivers.get(name)

    def get_ranking_driver(self, name: str = PolicyConfig.DEFAULT_RANKING_ENGINE) -> RankingEngine:
        return self._ranking_drivers.get(name)

    def get_action_driver(self, name: str = PolicyConfig.DEFAULT_ACTION_ENGINE) -> ActionEngine:
        return self._action_drivers.get(name)
