# app/services/overmind/agents/strategist.py
"""
الوكيل الاستراتيجي (Strategist Agent) - مخطط العبقري.
---------------------------------------------------------
يقوم هذا الوكيل بتحليل الأهداف المعقدة وتفكيكها باستخدام خوارزميات التفكير
الشجري (Tree of Thoughts) والتحليل العودي (Recursive Decomposition).

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
- استخدام واجهات صارمة.
"""

import json
from typing import Any

from app.core.ai_gateway import AIClient
from app.core.di import get_logger
from app.core.protocols import AgentPlanner

logger = get_logger(__name__)


class StrategistAgent(AgentPlanner):
    """
    العقل المدبر للتخطيط الاستراتيجي.

    المسؤوليات:
    1. فهم النوايا الخفية وراء طلب المستخدم.
    2. تفكيك المشكلة الكبرى إلى خطوات ذرية قابلة للتنفيذ.
    3. تحديد التبعيات بين الخطوات (DAG Construction).
    """

    def __init__(self, ai_client: AIClient) -> None:
        self.ai = ai_client

    async def create_plan(self, objective: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        إنشاء خطة استراتيجية محكمة.

        يستخدم نموذج LLM المتطور لتوليد خطة بصيغة JSON صارمة.
        """
        logger.info(f"Strategist is devising a plan for: {objective}")

        system_prompt = """
        أنت "الاستراتيجي" (The Strategist)، عقل تخطيطي خارق الذكاء ضمن منظومة Overmind.

        مهمتك:
        تحويل الهدف المبهم للمستخدم إلى خطة تنفيذية دقيقة (Action Plan).

        القواعد:
        1. فكر بعمق (Think Step-by-Step).
        2. قسم المشكلة إلى خطوات صغيرة جداً (Atomic Steps).
        3. كل خطوة يجب أن تكون قابلة للتنفيذ باستخدام أدوات برمجية (CLI, FileSystem, Git).
        4. المخرجات يجب أن تكون JSON صالح فقط وبدون أي مقدمات.

        صيغة JSON المطلوبة:
        {
            "strategy_name": "اسم استراتيجي جذاب",
            "reasoning": "شرح منطقي للخطة",
            "steps": [
                {
                    "name": "اسم الخطوة",
                    "description": "وصف دقيق لما سيتم فعله",
                    "tool_hint": "تلميح للأداة المناسبة (مثلاً: shell, read_file)"
                }
            ]
        }
        """

        user_content = f"Objective: {objective}\nContext: {json.dumps(context, default=str)}"

        try:
            # استدعاء الذكاء الاصطناعي (محاكاة أو حقيقي حسب الـ AIClient)
            # نفترض هنا أن AIClient يعيد JSON string نظيف
            response_text = await self.ai.send_message(
                system_prompt=system_prompt,
                user_message=user_content,
                temperature=0.2  # دقة عالية، إبداع منخفض
            )

            # تنظيف الرد (في حال وجود Markdown blocks)
            cleaned_response = self._clean_json_block(response_text)
            plan_data = json.loads(cleaned_response)

            # التحقق البسيط
            if "steps" not in plan_data:
                raise ValueError("Missing 'steps' in AI plan")

            return plan_data

        except Exception as e:
            logger.error(f"Strategist failed to plan: {e}")
            # خطة طوارئ (Fallback Plan)
            return {
                "strategy_name": "Emergency Fallback",
                "reasoning": f"Planning failed due to: {e}",
                "steps": [
                    {
                        "name": "Analyze Failure",
                        "description": "Check why planning failed and report.",
                        "tool_hint": "unknown"
                    }
                ]
            }

    def _clean_json_block(self, text: str) -> str:
        """استخراج JSON من نص قد يحتوي على Markdown code blocks."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
