"""
Super Reasoner Node.
--------------------
A LangGraph node that orchestrates the "Deep Reasoning" workflow using LlamaIndex and the Knowledge Graph.
"""

from langchain_core.messages import AIMessage

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.services.chat.graph.state import AgentState
from app.services.reasoning.search_strategy import MathReasoningStrategy, RMCTSStrategy
from app.services.reasoning.workflow import SuperReasoningWorkflow

logger = get_logger("super-reasoner-node")


def _detect_math_intent(query: str) -> bool:
    """
    Simple heuristic to detect if the query requires the Math Reasoning Strategy.
    """
    keywords = [
        "probability",
        "chance",
        "odds",
        "calculate",
        "solve",
        "equation",
        "theorem",
        "integral",
        "derivative",
        "matrix",
        "urn",
        "dice",
        "coin",
    ]
    query_lower = query.lower()
    return any(k in query_lower for k in keywords)


async def super_reasoner_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    Super Reasoner Node: Executes the deep reasoning workflow.
    """
    logger.info("🧠 Super Reasoner Activated.")

    messages = state.get("messages", [])
    if not messages:
        logger.warning("No messages in state.")
        return {}

    last_message = messages[-1].content

    # Select Strategy based on content
    if _detect_math_intent(last_message):
        logger.info("Math/Probability context detected. Engaging MathReasoningStrategy.")
        strategy = MathReasoningStrategy(ai_client)
    else:
        logger.info("General context detected. Engaging RMCTSStrategy.")
        strategy = RMCTSStrategy(ai_client)

    # Instantiate workflow with selected strategy
    workflow = SuperReasoningWorkflow(client=ai_client, timeout=120, strategy=strategy)

    # Run workflow
    try:
        logger.info(f"Running workflow for query: {last_message[:50]}...")
        result = await workflow.run(query=last_message)
        response_text = str(result)
    except Exception as e:
        logger.error(f"Super Reasoner crashed: {e}")
        response_text = (
            "I apologize, but I encountered an internal error while accessing my knowledge graph."
        )

    # Return state update
    return {
        "messages": [AIMessage(content=response_text)],
        "current_step_index": state.get("current_step_index", 0) + 1,
    }
