"""
عقدة المخطط (Planner Node).
---------------------------
تقوم بتحليل طلب المستخدم وبناء خطة مفصلة للحل.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from app.services.chat.graph.state import AgentState
from app.core.ai_gateway import AIClient
import json

async def planner_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة التخطيط: تحلل الطلب وتضع خطة.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

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

    # We use the generate method directly or a structured output if supported.
    # For now, we ask for JSON in the prompt.

    response = await ai_client.generate(
        model="gpt-4o", # Or capable model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Request: {last_message}"}
        ],
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    try:
        plan_data = json.loads(content)
        plan = plan_data.get("steps", ["search", "explain"])
    except:
        plan = ["search", "explain"] # Fallback

    return {"plan": plan, "current_step_index": 0, "next": "supervisor"}
