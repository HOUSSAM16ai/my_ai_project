"""
سير العمل (Workflow Construction).
----------------------------------
تجميع العقد والحواف لبناء الرسم البياني (LangGraph).
"""

from langgraph.graph import END, StateGraph

from app.core.ai_gateway import AIClient
from app.services.chat.graph.nodes.planner import planner_node
from app.services.chat.graph.nodes.researcher import researcher_node
from app.services.chat.graph.nodes.reviewer import reviewer_node
from app.services.chat.graph.nodes.super_reasoner import super_reasoner_node
from app.services.chat.graph.nodes.supervisor import supervisor_node
from app.services.chat.graph.nodes.writer import writer_node
from app.services.chat.graph.state import AgentState
from app.services.chat.tools import ToolRegistry


def create_multi_agent_graph(ai_client: AIClient, tools: ToolRegistry) -> object:
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

    async def call_super_reasoner(state):
        return await super_reasoner_node(state, ai_client)

    async def call_reviewer(state):
        return await reviewer_node(state, ai_client)

    async def call_supervisor(state):
        return await supervisor_node(state)

    workflow.add_node("planner", call_planner)
    workflow.add_node("researcher", call_researcher)
    workflow.add_node("writer", call_writer)
    workflow.add_node("super_reasoner", call_super_reasoner)
    workflow.add_node("reviewer", call_reviewer)
    workflow.add_node("supervisor", call_supervisor)

    # 2. Add Edges
    workflow.set_entry_point("supervisor")

    # Conditional Edges from Supervisor
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "planner": "planner",
            "researcher": "researcher",
            "writer": "writer",
            "super_reasoner": "super_reasoner",
            "end": END,
        },
    )

    # Routing Logic for Reviewer (Self-Correction Loop)
    def route_reviewer(state):
        # If score is high (>8.0) OR we've looped twice -> Move on (Supervisor)
        if state.get("review_score", 0) >= 8.0 or state.get("iteration_count", 0) >= 2:
            return "supervisor"
        # Otherwise, force correction (Loop back to Writer)
        return "writer"

    workflow.add_conditional_edges(
        "reviewer",
        route_reviewer,
        {
            "supervisor": "supervisor",
            "writer": "writer",
        },
    )

    # Direct Edges
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("researcher", "supervisor")
    # Writer & Reasoner now go to Reviewer first, not Supervisor
    workflow.add_edge("writer", "reviewer")
    workflow.add_edge("super_reasoner", "reviewer")

    return workflow.compile()
