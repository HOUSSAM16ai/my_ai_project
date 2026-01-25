"""
عقدة المشرف (Supervisor Node).
------------------------------
تحدد الخطوة التالية بناءً على الخطة والحالة الحالية.
"""

from app.services.chat.graph.state import AgentState
from langchain_core.messages import SystemMessage

async def supervisor_node(state: AgentState) -> dict:
    """
    عقدة الإشراف: تقرر الوجهة التالية.
    """
    plan = state.get("plan", [])
    idx = state.get("current_step_index", 0)

    # If no plan, go to planner
    if not plan:
        return {"next": "planner"}

    # If finished plan, end
    if idx >= len(plan):
        return {"next": "end"}

    next_step = plan[idx]

    # Map steps to nodes
    if next_step == "search":
        return {"next": "researcher"}
    elif next_step == "reason":
        return {"next": "super_reasoner"}
    elif next_step == "explain":
        return {"next": "writer"}
    elif next_step == "analyze":
        return {"next": "writer"} # Simplify for now

    return {"next": "end"}
