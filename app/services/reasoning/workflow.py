from llama_index.core.schema import NodeWithScore
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step

from app.core.gateway.simple_client import SimpleAIClient
from app.core.logging import get_logger
from app.services.search_engine.llama_retriever import KnowledgeGraphRetriever

logger = get_logger("super-reasoner")


class RetrievalEvent(Event):
    nodes: list[NodeWithScore]
    query: str


class SuperReasoningWorkflow(Workflow):
    def __init__(self, client: SimpleAIClient, timeout: int = 120, verbose: bool = True):
        super().__init__(timeout=timeout, verbose=verbose)
        self.client = client
        self.retriever = KnowledgeGraphRetriever(top_k=5)

    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrievalEvent:
        query = ev.get("query")
        if not query:
            # Should not happen if called correctly
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
    async def synthesize(self, ctx: Context, ev: RetrievalEvent) -> StopEvent:
        nodes = ev.nodes
        query = ev.query

        if not nodes:
            logger.warning("No nodes retrieved. Falling back to general knowledge.")
            # We can return a specific message or let the LLM try without context
            context_str = "No specific knowledge graph nodes found."
        else:
            context_str = "\n\n".join(
                [f"Node [{n.metadata['label']}] ({n.metadata['name']}): {n.text}" for n in nodes]
            )

        system_prompt = (
            "You are the Overmind Super Reasoner, an advanced AI connected to a dedicated Knowledge Graph.\n"
            "Your Goal: Provide a 'terribly good' (extremely high quality), deep, and intelligent answer.\n"
            "Instructions:\n"
            "1. Analyze the provided Context Nodes (if any). They represent the Ground Truth.\n"
            "2. If the context contains an exercise (e.g., Baccalaureate Probability), solve it step-by-step with mathematical precision.\n"
            "3. Use LaTeX for math (e.g., $P(A)$).\n"
            "4. If the context is missing, apologize and define the concept generally, but admit you don't have the specific file.\n"
            "5. Structure: Use Headers, Bullet points, and bold text for clarity.\n"
            "6. Tone: Authoritative, Encouraging, and Academic."
        )

        logger.info("Synthesizing answer...")

        try:
            response = await self.client.generate_text(
                prompt=f"Context from Knowledge Graph:\n{context_str}\n\nUser Question: {query}",
                system_prompt=system_prompt,
            )
            content = response.content
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            content = "I encountered an error while processing the knowledge graph."

        return StopEvent(result=content)
