"""
Reasoning Service Adapter.
--------------------------
Adapts the SuperReasoningWorkflow to the Kagent Service Interface.
Allows the Reasoning Engine to be exposed as a service on the Mesh.
"""

from app.core.ai_gateway import AIClient
from app.core.interfaces import IKnowledgeRetriever
from app.core.logging import get_logger
from microservices.reasoning_agent.src.search_strategy import MathReasoningStrategy, RMCTSStrategy
from microservices.reasoning_agent.src.workflow import SuperReasoningWorkflow
from microservices.research_agent.src.search_engine.llama_retriever import KnowledgeGraphRetriever

logger = get_logger("reasoning-service")


class ReasoningService:
    """
    خدمة الاستنتاج (Reasoning Service).
    واجهة موحدة لتشغيل سير عمل الاستنتاج العميق عبر Kagent.
    """

    def __init__(self, ai_client: AIClient, retriever: IKnowledgeRetriever | None = None):
        self.ai_client = ai_client
        self.retriever = retriever or KnowledgeGraphRetriever(top_k=5)

    async def solve_deeply(self, query: str, strategy_type: str = "auto") -> str:
        """
        Action: solve_deeply.
        تنفيذ سير العمل الكامل (Expansion -> Evaluation -> Selection).
        """
        logger.info(
            f"Reasoning Service received query: {query[:50]}... (Strategy: {strategy_type})"
        )

        # 1. Strategy Selection
        if strategy_type == "math":
            strategy = MathReasoningStrategy(self.ai_client)
        elif strategy_type == "general":
            strategy = RMCTSStrategy(self.ai_client)
        elif any(
            k in query.lower()
            for k in ["urn", "probabilit", "math", "calculate", "solve", "equation"]
        ):
            # Auto-detection
            strategy = MathReasoningStrategy(self.ai_client)
        else:
            strategy = RMCTSStrategy(self.ai_client)

        # 2. Workflow Instantiation
        workflow = SuperReasoningWorkflow(
            client=self.ai_client, timeout=120, strategy=strategy, retriever=self.retriever
        )

        # 3. Execution
        try:
            result = await workflow.run(query=query)
            return str(result)
        except Exception as e:
            logger.error(f"Reasoning Service execution failed: {e}")
            raise e
