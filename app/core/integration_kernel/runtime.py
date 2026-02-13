from typing import Any

from app.core.integration_kernel.ir import (
    AgentAction,
    PromptProgram,
    RetrievalQuery,
    ScoringSpec,
    WorkflowPlan,
)
from app.core.integration_kernel.policy import PolicyManager


class IntegrationKernel:
    """
    The Micro-Kernel for Agent Integrations.
    Orchestrates execution across different technologies (drivers) based on IR and Policies.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.policy_manager = PolicyManager()
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # Drivers are registered externally or via a bootstrap process.
        # For simplicity in this migration, we might lazily load them or rely on manual registration.

    def register_driver(self, category: str, name: str, driver: Any):
        """
        Registers a driver implementation.
        """
        if category == "workflow":
            self.policy_manager.register_workflow_driver(name, driver)
        elif category == "retrieval":
            self.policy_manager.register_retrieval_driver(name, driver)
        elif category == "prompt":
            self.policy_manager.register_prompt_driver(name, driver)
        elif category == "ranking":
            self.policy_manager.register_ranking_driver(name, driver)
        elif category == "action":
            self.policy_manager.register_action_driver(name, driver)
        else:
            raise ValueError(f"Unknown driver category: {category}")

    async def run_workflow(self, plan: WorkflowPlan, engine: str = "langgraph") -> dict[str, Any]:
        """Executes a workflow plan using the specified engine."""
        driver = self.policy_manager.get_workflow_driver(engine)
        if not driver:
            raise RuntimeError(f"Workflow engine '{engine}' not registered.")
        return await driver.run(plan)

    async def search(self, query: RetrievalQuery, engine: str = "llamaindex") -> dict[str, Any]:
        """Executes a semantic search using the specified engine."""
        driver = self.policy_manager.get_retrieval_driver(engine)
        if not driver:
            raise RuntimeError(f"Retrieval engine '{engine}' not registered.")
        return await driver.search(query)

    async def optimize(self, program: PromptProgram, engine: str = "dspy") -> dict[str, Any]:
        """Executes a prompt optimization or program using the specified engine."""
        driver = self.policy_manager.get_prompt_driver(engine)
        if not driver:
            raise RuntimeError(f"Prompt engine '{engine}' not registered.")
        return await driver.optimize(program)

    async def rank(self, spec: ScoringSpec, engine: str = "reranker") -> dict[str, Any]:
        """Ranks documents using the specified engine."""
        driver = self.policy_manager.get_ranking_driver(engine)
        if not driver:
            raise RuntimeError(f"Ranking engine '{engine}' not registered.")
        return await driver.rank(spec)

    async def act(self, action: AgentAction, engine: str = "kagent") -> dict[str, Any]:
        """Executes an action using the specified engine."""
        driver = self.policy_manager.get_action_driver(engine)
        if not driver:
            raise RuntimeError(f"Action engine '{engine}' not registered.")
        return await driver.execute(action)

    def get_system_status(self) -> dict[str, Any]:
        """Aggregates status from all registered drivers."""
        status = {}
        # This implementation is simplified; a real one would iterate over all registered drivers.
        # Here we just check the defaults.

        wf = self.policy_manager.get_workflow_driver()
        status["workflow"] = wf.get_status() if wf else {"status": "not_configured"}

        rt = self.policy_manager.get_retrieval_driver()
        status["retrieval"] = rt.get_status() if rt else {"status": "not_configured"}

        pm = self.policy_manager.get_prompt_driver()
        status["prompt"] = pm.get_status() if pm else {"status": "not_configured"}

        rk = self.policy_manager.get_ranking_driver()
        status["ranking"] = rk.get_status() if rk else {"status": "not_configured"}

        act = self.policy_manager.get_action_driver()
        status["action"] = act.get_status() if act else {"status": "not_configured"}

        return status
