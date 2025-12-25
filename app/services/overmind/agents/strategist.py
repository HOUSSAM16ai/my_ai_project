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
from app.core.protocols import AgentPlanner, CollaborationContext

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

    async def create_plan(self, objective: str, context: CollaborationContext) -> dict[str, Any]:
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

        # استخدام الذاكرة المشتركة لإثراء السياق
        shared_data = context.shared_memory
        user_content = f"Objective: {objective}\nContext: {json.dumps(shared_data, default=str)}"

        try:
            logger.info("Strategist: Calling AI for plan generation...")
            # استدعاء الذكاء الاصطناعي (محاكاة أو حقيقي حسب الـ AIClient)
            response_text = await self.ai.send_message(
                system_prompt=system_prompt,
                user_message=user_content,
                temperature=0.2  # دقة عالية، إبداع منخفض
            )
            logger.info(f"Strategist: Received AI response ({len(response_text)} chars)")

            # تنظيف الرد (في حال وجود Markdown blocks)
            cleaned_response = self._clean_json_block(response_text)
            plan_data = json.loads(cleaned_response)

            # التحقق البسيط
            if "steps" not in plan_data:
                raise ValueError("Missing 'steps' in AI plan")

            logger.info(f"Strategist: Plan created with {len(plan_data.get('steps', []))} steps")
            # تحديث الذاكرة المشتركة بالخطة
            context.update("last_plan", plan_data)
            return plan_data

        except json.JSONDecodeError as e:
            logger.error(f"Strategist JSON parsing error: {e}")
            logger.error(f"Raw response: {response_text[:500] if 'response_text' in locals() else 'N/A'}")

            # التحقق من رسالة Safety Net
            if 'response_text' in locals() and 'Unable to reach external intelligence' in response_text:
                logger.error("AI service unavailable - Safety Net activated")
                return {
                    "strategy_name": "AI Service Unavailable",
                    "reasoning": "Cannot proceed without AI service. Please configure OPENROUTER_API_KEY.",
                    "steps": [
                        {
                            "name": "Configuration Required",
                            "description": "OPENROUTER_API_KEY is not configured. Please set it in .env file.",
                            "tool_hint": "config"
                        }
                    ]
                }

            # خطة طوارئ (Fallback Plan)
            return {
                "strategy_name": "Emergency Fallback - JSON Error",
                "reasoning": f"Failed to parse AI response: {e}",
                "steps": [
                    {
                        "name": "Report JSON Error",
                        "description": f"AI response was not valid JSON. Error: {e}",
                        "tool_hint": "log"
                    }
                ]
            }
        except Exception as e:
            logger.exception(f"Strategist failed to plan: {e}")
            # خطة طوارئ (Fallback Plan)
            return {
                "strategy_name": "Emergency Fallback",
                "reasoning": f"Planning failed due to: {type(e).__name__}: {e}",
                "steps": [
                    {
                        "name": "Analyze Failure",
                        "description": f"Check why planning failed: {type(e).__name__}: {str(e)[:200]}",
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
