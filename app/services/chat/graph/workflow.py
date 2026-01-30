"""
سير العمل (Workflow Construction).
----------------------------------
تجميع العقد والحواف لبناء الرسم البياني (LangGraph).
"""

from langgraph.graph import END, StateGraph

from app.core.ai_gateway import AIClient
from app.services.chat.graph.nodes.planner import planner_node
from app.services.chat.graph.nodes.procedural_auditor import procedural_auditor_node
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

    async def call_procedural_auditor(state):
        return await procedural_auditor_node(state, ai_client)

    async def call_supervisor(state):
        # Now passing ai_client to supervisor
        return await supervisor_node(state, ai_client)

    workflow.add_node("planner", call_planner)
    workflow.add_node("researcher", call_researcher)
    workflow.add_node("writer", call_writer)
    workflow.add_node("super_reasoner", call_super_reasoner)
    workflow.add_node("procedural_auditor", call_procedural_auditor)
    workflow.add_node("reviewer", call_reviewer)
    workflow.add_node("supervisor", call_supervisor)

    # 2. Add Edges
    workflow.set_entry_point("supervisor")

    # Conditional Edges from Supervisor
    # The Supervisor LLM decides exactly which node to go to next.
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "planner": "planner",
            "researcher": "researcher",
            "writer": "writer",
            "super_reasoner": "super_reasoner",
            "procedural_auditor": "procedural_auditor",
            "reviewer": "reviewer",
            "FINISH": END,
        },
    )

    # Direct Edges: All workers report back to Supervisor
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("super_reasoner", "supervisor")
    workflow.add_edge("procedural_auditor", "supervisor")
    workflow.add_edge("writer", "supervisor")
    workflow.add_edge("reviewer", "supervisor")

    return workflow.compile()
