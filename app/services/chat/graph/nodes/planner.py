"""
عقدة المخطط (Planner Node).
---------------------------
تقوم بتحليل طلب المستخدم وبناء خطة مفصلة للحل باستخدام Planning Agent via Kagent.
Refactored for Unified Architecture.
"""

import logging

from app.services.chat.graph.state import AgentState
from app.services.kagent.domain import AgentRequest
from app.services.kagent.interface import KagentMesh

logger = logging.getLogger(__name__)


async def planner_node(state: AgentState, kagent: KagentMesh) -> dict:
    """
    عقدة التخطيط: تستدعي وكيل التخطيط لإنشاء خطوات الحل.
    """
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    logger.info("Planner Node: Requesting plan via Kagent...")

    request = AgentRequest(
        caller_id="planner_node",
        target_service="planning_agent",
        action="generate_plan",
        payload={"goal": last_message, "context": []},
    )

    response = await kagent.execute_action(request)

    # Default fallback plan if agent fails or returns empty
    plan = ["search", "explain"]

    if response.status == "success":
        data = response.data
        if isinstance(data, dict):
            plan = data.get("steps", plan)
            logger.info(f"Plan received: {plan}")
        else:
            logger.warning(f"Unexpected data format from planner: {data}")
    else:
        logger.error(f"Planning Agent failed: {response.error}. Using fallback.")

    return {"plan": plan, "current_step_index": 0, "next": "supervisor"}
