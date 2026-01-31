from llama_index.core.schema import NodeWithScore
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step

from app.core.gateway.simple_client import SimpleAIClient
from app.core.interfaces import IKnowledgeRetriever, IReasoningStrategy
from app.core.logging import get_logger
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
