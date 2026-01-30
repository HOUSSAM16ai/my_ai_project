"""
Super Reasoner Node.
--------------------
A LangGraph node that orchestrates the "Deep Reasoning" workflow using LlamaIndex and the Knowledge Graph.
"""

from langchain_core.messages import AIMessage

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.services.chat.graph.state import AgentState
from app.services.reasoning.workflow import SuperReasoningWorkflow

logger = get_logger("super-reasoner-node")


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

    # Instantiate workflow
    # We assume ai_client is compatible (has generate_text)
    workflow = SuperReasoningWorkflow(client=ai_client, timeout=120)

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
    # We append the result as an AI Message
    return {
        "messages": [AIMessage(content=response_text)],
        # Increment step index assuming this fulfills one plan step (e.g., 'reason')
        "current_step_index": state.get("current_step_index", 0) + 1,
        "final_response": response_text,
    }
