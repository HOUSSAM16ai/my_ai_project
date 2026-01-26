"""
عقدة المشرف (Supervisor Node).
------------------------------
تحدد الخطوة التالية بناءً على الخطة والحالة الحالية.
"""

from app.services.chat.graph.routing import determine_next_node
from app.services.chat.graph.state import AgentState


async def supervisor_node(state: AgentState) -> dict:
    """
    عقدة الإشراف: تقرر الوجهة التالية.
    """
    next_node, trace = determine_next_node(state)
    return {"next": next_node, "routing_trace": trace}
