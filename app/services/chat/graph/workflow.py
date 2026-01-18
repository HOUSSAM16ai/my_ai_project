"""
سير العمل (Workflow Construction).
----------------------------------
تجميع العقد والحواف لبناء الرسم البياني (LangGraph).
"""

from typing import Any
from langgraph.graph import StateGraph, END
from app.services.chat.graph.state import AgentState
from app.services.chat.graph.nodes.planner import planner_node
from app.services.chat.graph.nodes.researcher import researcher_node
from app.services.chat.graph.nodes.writer import writer_node
from app.services.chat.graph.nodes.supervisor import supervisor_node
from app.core.ai_gateway import AIClient
from app.services.chat.tools import ToolRegistry

def create_multi_agent_graph(ai_client: AIClient, tools: ToolRegistry) -> Any:
    """
    بناء الرسم البياني للوكلاء المتعددين.
    """
    workflow = StateGraph(AgentState)

    # 1. Add Nodes (Wrapped with partials/lambdas to inject deps)
    async def call_planner(state):
        return await planner_node(state, ai_client)

    async def call_researcher(state):
        return await researcher_node(state, tools)

    async def call_writer(state):
        return await writer_node(state, ai_client)

    async def call_supervisor(state):
        return await supervisor_node(state)

    workflow.add_node("planner", call_planner)
    workflow.add_node("researcher", call_researcher)
    workflow.add_node("writer", call_writer)
    workflow.add_node("supervisor", call_supervisor)

    # 2. Add Edges
    # Entry point -> Supervisor (checks if we have a plan)
    # Actually, entry -> Supervisor is better to check if we need planning.

    workflow.set_entry_point("supervisor")

    # Conditional Edges from Supervisor
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "planner": "planner",
            "researcher": "researcher",
            "writer": "writer",
            "end": END
        }
    )

    # Edges back to Supervisor
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("writer", "supervisor")

    return workflow.compile()
