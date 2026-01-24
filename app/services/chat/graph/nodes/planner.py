"""
عقدة المخطط (Planner Node).
---------------------------
تقوم بتحليل طلب المستخدم وبناء خطة مفصلة للحل باستخدام النموذج المدمج.
"""

import json
import logging
from app.services.chat.graph.state import AgentState
from app.core.ai_gateway import AIClient

logger = logging.getLogger(__name__)

async def planner_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة التخطيط: تحلل الطلب وتضع خطة.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    logger.info("Planner Node: Analyzing request...")

    # Local Logic (Monolith)
    system_prompt = (
        "أنت 'المهندس المخطط' (Planner Architect) في نظام تعليمي خارق.\n"
        "مهمتك: تحليل طلب الطالب وتقسيمه إلى خطوات منطقية دقيقة.\n"
        "المخرجات: JSON يحتوي على قائمة 'steps'.\n"
        "الخطوات المتاحة فقط:\n"
        "1. 'search': للبحث عن تمارين، دروس، أو معلومات.\n"
        "2. 'analyze': لتحليل المحتوى المسترجع أو حل مسألة.\n"
        "3. 'explain': لكتابة الشرح النهائي.\n\n"
        "مثال:\n"
        "User: 'أريد تمارين احتمالات بكالوريا 2024'\n"
        "Plan: ['search', 'explain']"
    )

    content = await ai_client.send_message(
        system_prompt=system_prompt,
        user_message=f"Request: {last_message}"
    )

    try:
        # Try to parse JSON. If the model returns markdown like ```json ... ```, we might need cleanup.
        clean_content = content.replace("```json", "").replace("```", "").strip()
        plan_data = json.loads(clean_content)
        plan = plan_data.get("steps", ["search", "explain"])
    except Exception as e:
        logger.warning(f"Failed to parse planner output: {content}. Error: {e}")
        plan = ["search", "explain"]

    logger.info(f"Generated Plan: {plan}")
    return {"plan": plan, "current_step_index": 0, "next": "supervisor"}
