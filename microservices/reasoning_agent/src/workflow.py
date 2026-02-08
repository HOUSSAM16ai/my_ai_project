import importlib
import importlib.util
from dataclasses import dataclass, field

from typing import Callable


def _load_llama_index() -> tuple[object | None, object | None]:
    """يحاول تحميل وحدات LlamaIndex اللازمة لسير العمل عند توفرها."""

    if importlib.util.find_spec("llama_index") is None:
        return None, None

    schema_spec = importlib.util.find_spec("llama_index.core.schema")
    workflow_spec = importlib.util.find_spec("llama_index.core.workflow")
    if schema_spec is None or workflow_spec is None:
        return None, None

    schema_module = importlib.import_module("llama_index.core.schema")
    workflow_module = importlib.import_module("llama_index.core.workflow")
    return schema_module, workflow_module


_schema_module, _workflow_module = _load_llama_index()

if _schema_module is None or _workflow_module is None:

    @dataclass
    class NodeWithScore:
        """تمثيل مبسط لعقدة معرفة مع نص وبيانات وصفية."""

        text: str = ""
        metadata: dict[str, str] = field(default_factory=dict)

    class Event:
        """حدث بسيط يدعم تخزين البيانات وقراءتها."""

        def __init__(self, **payload: object) -> None:
            self._payload = payload

        def get(self, key: str, default: object | None = None) -> object | None:
            return self._payload.get(key, default)

    class StartEvent(Event):
        """حدث البداية لسير العمل المبسط."""

    class StopEvent(Event):
        """حدث النهاية لسير العمل المبسط."""

    class Context:
        """سياق فارغ لسير العمل المبسط."""

    class Workflow:
        """قالب مبسط لسير العمل عند غياب LlamaIndex."""

        def __init__(self, timeout: int = 300, verbose: bool = True) -> None:
            self.timeout = timeout
            self.verbose = verbose

    def step(func: Callable[..., object]) -> Callable[..., object]:
        """ديكوريتر بديل لا يغير سلوك الدالة."""

        return func

else:
    NodeWithScore = _schema_module.NodeWithScore
    Context = _workflow_module.Context
    Event = _workflow_module.Event
    StartEvent = _workflow_module.StartEvent
    StopEvent = _workflow_module.StopEvent
    Workflow = _workflow_module.Workflow
    step = _workflow_module.step

from microservices.reasoning_agent.src.ai_client import SimpleAIClient
from microservices.reasoning_agent.src.interfaces import IKnowledgeRetriever, IReasoningStrategy
from microservices.reasoning_agent.src.logging import get_logger
from microservices.reasoning_agent.src.search_strategy import RMCTSStrategy
from microservices.research_agent.src.search_engine.llama_retriever import KnowledgeGraphRetriever

logger = get_logger("super-reasoner")


class RetrievalEvent(Event):
    nodes: list[NodeWithScore]
    query: str


class SuperReasoningWorkflow(Workflow):
    def __init__(
        self,
        client: SimpleAIClient,
        timeout: int = 300,
        verbose: bool = True,
        retriever: IKnowledgeRetriever | None = None,
        strategy: IReasoningStrategy | None = None,
    ):
        # Increased timeout for R-MCTS
        super().__init__(timeout=timeout, verbose=verbose)
        self.client = client

        if retriever:
            self.retriever = retriever
        else:
            self.retriever = KnowledgeGraphRetriever(top_k=5)

        if strategy:
            self.strategy = strategy
        else:
            self.strategy = RMCTSStrategy(client)

    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrievalEvent:
        query = ev.get("query")
        if not query:
            logger.warning("No query provided to SuperReasoningWorkflow")
            return RetrievalEvent(nodes=[], query="")

        logger.info(f"Retrieving for: {query}")

        try:
            nodes = await self.retriever.aretrieve(query)
            logger.info(f"Retrieved {len(nodes)} nodes.")
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            nodes = []

        return RetrievalEvent(nodes=nodes, query=query)

    @step
    async def reason_and_synthesize(self, ctx: Context, ev: RetrievalEvent) -> StopEvent:
        """
        Executes the R-MCTS strategy to find the best reasoning path, then synthesizes the final answer.
        """
        nodes = ev.nodes
        query = ev.query

        if not nodes:
            logger.warning("No nodes retrieved. Falling back to general knowledge.")
            context_str = "No specific knowledge graph nodes found."
        else:
            context_str = "\n\n".join(
                [
                    f"Node [{n.metadata.get('label', 'Data')}] ({n.metadata.get('name', 'Unknown')}): {n.text}"
                    for n in nodes
                ]
            )

        logger.info("Starting R-MCTS Reasoning Phase...")

        # 1. R-MCTS Execution
        best_thought_node = await self.strategy.execute(
            root_content=f"Analyze query: {query}",
            context=context_str,
            depth=2,  # Configurable depth
        )

        logger.info(
            f"R-MCTS Selected Path: {best_thought_node.content} (Score: {best_thought_node.value})"
        )

        # 2. Final Synthesis
        system_prompt = (
            "You are the Overmind Super Reasoner, an advanced AI connected to a dedicated Knowledge Graph.\n"
            "Your Goal: Provide a 'terribly good' (extremely high quality), deep, and intelligent answer.\n"
            "Instructions:\n"
            "1. Base your answer on the **Selected Reasoning Path** provided below.\n"
            "2. Use the **Context** as Ground Truth.\n"
            "3. If the context contains an exercise, solve it step-by-step with mathematical precision ($LaTeX$).\n"
            "4. Structure: Use Headers, Bullet points, and bold text for clarity.\n"
            "5. Tone: Authoritative, Encouraging, and Academic."
        )

        final_prompt = (
            f"Context from Knowledge Graph:\n{context_str}\n\n"
            f"### Selected Reasoning Path (Internal Monologue):\n{best_thought_node.content}\n\n"
            f"### User Question:\n{query}"
        )

        logger.info("Synthesizing final answer...")

        try:
            response = await self.client.generate_text(
                prompt=final_prompt,
                system_prompt=system_prompt,
            )
            content = response.content
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            content = "I encountered an error while processing the knowledge graph."

        return StopEvent(result=content)
