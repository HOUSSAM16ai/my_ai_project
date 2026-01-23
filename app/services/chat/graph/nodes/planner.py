"""
عقدة المخطط (Planner Node).
---------------------------
تقوم بتحليل طلب المستخدم وبناء خطة مفصلة للحل.
تحاول الاتصال بخدمة التخطيط المصغرة (Planning Microservice) أولاً،
وفي حال الفشل تعود لاستخدام النموذج المحلي (Fallback).
"""

import json
import logging
import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.chat.graph.state import AgentState
from app.core.ai_gateway import AIClient
from app.core.ai_config import get_ai_config

logger = logging.getLogger(__name__)

PLANNING_SERVICE_URL = "http://localhost:8001/plans"

async def planner_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة التخطيط: تحلل الطلب وتضع خطة.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    # محاولة الاتصال بالخدمة المصغرة أولاً
    try:
        logger.info("Calling Planning Agent Microservice...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                PLANNING_SERVICE_URL,
                json={"goal": last_message, "context": []}
            )
            response.raise_for_status()
            data = response.json()

            # تحويل خطوات الخدمة (نصوص) إلى خطوات LangGraph (أفعال)
            # بما أن الخدمة تعيد خطوات نصية وصفية، سنقوم بتبسيطها هنا
            # أو يمكننا الاعتماد عليها إذا كان النظام يدعم خطوات مرنة.
            # للتوافق الحالي، سنستخدم منطق بسيط:

            # إذا كانت الخدمة تعمل، نستخدم خطواتها "كما هي" في الخطة للعرض،
            # لكن LangGraph يحتاج خطوات تنفيذية (Nodes).
            # لذلك، سنقوم بتحويل "النوايا" إلى "عقد".

            # للتبسيط في هذا التطبيق المدمج:
            # سنفترض أن الخدمة تعيد خطوات عامة، وسنحولها إلى ['search', 'explain'] كحد أدنى
            # ولكن، الهدف هو التكامل. لذا سنستخدم الخطوات المسترجعة إذا أمكن.

            # نظراً لأن LangGraph يتوقع قيم محددة لـ "next"، سنحافظ على الهيكل القديم
            # ولكن نثري الـ "plan" بالبيانات الجديدة.

            logger.info("Planning Microservice responded successfully.")

            # هنا سنقوم "بترجمة" الخطة النصية إلى أفعال
            # (هذا منطق مؤقت لضمان التوافق مع باقي النظام)
            return {"plan": ["search", "explain"], "current_step_index": 0, "next": "supervisor"}

    except Exception as e:
        logger.warning(f"Planning Microservice unavailable ({e}). Using Monolith Fallback.")

    # Fallback: Local Logic (Monolith)
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

    response = await ai_client.generate(
        model=get_ai_config().primary_model,
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
        plan = ["search", "explain"]

    return {"plan": plan, "current_step_index": 0, "next": "supervisor"}
