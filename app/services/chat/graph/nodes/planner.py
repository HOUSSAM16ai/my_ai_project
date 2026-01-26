"""
عقدة المخطط (Planner Node).
---------------------------
تقوم بتحليل طلب المستخدم وبناء خطة مفصلة للحل باستخدام النموذج المدمج.
"""

import json
import logging
import os

import httpx

from app.core.ai_gateway import AIClient
from app.services.chat.graph.state import AgentState

logger = logging.getLogger(__name__)
PLANNING_SERVICE_URL = os.environ.get("PLANNING_SERVICE_URL", "http://localhost:8001/plans")


async def planner_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة التخطيط: تحلل الطلب وتضع خطة.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    logger.info("Planner Node: Analyzing request...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PLANNING_SERVICE_URL,
                json={"goal": last_message, "context": []},
                timeout=5.0,
            )
        if response.status_code == 200:
            payload = response.json()
            plan = payload.get("steps") or ["search", "explain"]
            return {"plan": plan, "current_step_index": 0, "next": "supervisor"}
        logger.warning("Planning service returned non-200 response.")
    except Exception as exc:
        logger.warning(f"Planning service unavailable, fallback to local logic: {exc}")

    # Local Logic (Monolith)
    system_prompt = (
        "أنت 'المهندس المخطط' (Planner Architect) في نظام تعليمي خارق.\n"
        "مهمتك: تحليل طلب الطالب وتقسيمه إلى خطوات منطقية دقيقة.\n"
        "المخرجات: JSON يحتوي على قائمة 'steps'.\n"
        "الخطوات المتاحة فقط:\n"
        "1. 'search': للبحث عن تمارين، دروس، أو معلومات بسيطة.\n"
        "2. 'reason': لاستخدام 'Super Reasoner' وحل التمارين المعقدة أو المسائل الرياضية بدقة عالية (Graph + Logic).\n"
        "3. 'analyze': لتحليل المحتوى المسترجع بشكل عام.\n"
        "4. 'explain': لكتابة الشرح النهائي.\n\n"
        "توجيه هام: إذا كان السؤال تمرين رياضي أو مسألة علمية دقيقة، استخدم 'reason' فوراً.\n"
        "مثال 1:\n"
        "User: 'أريد تمارين احتمالات بكالوريا 2024'\n"
        "Plan: ['reason']\n"
        "مثال 2:\n"
        "User: 'ما هي الفلسفة؟'\n"
        "Plan: ['search', 'explain']"
    )

    content = await ai_client.send_message(
        system_prompt=system_prompt, user_message=f"Request: {last_message}"
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
