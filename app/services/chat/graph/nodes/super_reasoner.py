"""
Super Reasoner Node.
--------------------
A LangGraph node that orchestrates the "Deep Reasoning" workflow using LlamaIndex and the Knowledge Graph.
NOW INTEGRATED WITH KAGENT MESH.
"""

from langchain_core.messages import AIMessage

from app.core.logging import get_logger
from app.services.chat.graph.state import AgentState
from app.services.kagent import AgentRequest, KagentMesh

logger = get_logger("super-reasoner-node")


async def super_reasoner_node(state: AgentState, kagent: KagentMesh) -> dict:
    """
    Super Reasoner Node: Executes the deep reasoning workflow via Kagent Mesh.
    """
    logger.info("🧠 Super Reasoner Activated via Kagent Mesh.")

    messages = state.get("messages", [])
    if not messages:
        logger.warning("No messages in state.")
        return {}

    last_message = messages[-1].content

    # Prepare Kagent Request
    request = AgentRequest(
        caller_id="super_reasoner",
        target_service="reasoning_engine",
        action="solve_deeply",
        payload={"query": last_message},
        security_token="supervisor-sys-key"  # Simulating authorized token
    )

    # Execute via Mesh
    response = await kagent.execute_action(request)

    if response.status == "success":
        response_text = str(response.data)
        metrics = response.metrics
        logger.info(f"Reasoning completed in {metrics.get('duration_ms', 0):.2f}ms")
    else:
        logger.error(f"Kagent execution failed: {response.error}")
        response_text = "I apologize, but I encountered an internal error while accessing my reasoning engine."

    # Return state update
    return {
        "messages": [AIMessage(content=response_text)],
        "current_step_index": state.get("current_step_index", 0) + 1,
    }
