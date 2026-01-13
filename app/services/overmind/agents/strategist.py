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

    async def create_plan(self, objective: str, context: CollaborationContext) -> dict[str, object]:
        """
        إنشاء خطة استراتيجية محكمة.

        يستخدم نموذج LLM المتطور لتوليد خطة بصيغة JSON صارمة.
        """
        logger.info("Strategist is devising a plan for: %s", objective)

        try:
            # إنشاء الخطة باستخدام الذكاء الاصطناعي
            plan_data = await self._generate_plan_with_ai(objective, context)

            # تحديث الذاكرة المشتركة
            self._record_plan_in_context(context, plan_data)
            logger.info("Strategist: Plan created with %s steps", _count_steps(plan_data))

            return plan_data

        except json.JSONDecodeError as e:
            return self._handle_json_decode_error(e, locals().get("response_text"))
        except Exception as e:
            return self._handle_general_error(e)

    async def _generate_plan_with_ai(
        self, objective: str, context: CollaborationContext
    ) -> dict[str, object]:
        """
        توليد الخطة باستخدام الذكاء الاصطناعي.

        Generate plan using AI.

        Args:
            objective: الهدف المطلوب
            context: سياق التعاون

        Returns:
            بيانات الخطة
        """
        system_prompt = self._build_system_prompt()
        user_content = self._build_user_content(objective, context)

        logger.info("Strategist: Calling AI for plan generation...")
        response_text = await self.ai.send_message(
            system_prompt=system_prompt,
            user_message=user_content,
            temperature=0.2,  # دقة عالية، إبداع منخفض
        )
        logger.info(f"Strategist: Received AI response ({len(response_text)} chars)")

        # تنظيف وتحليل الرد
        plan_data = self._parse_json_response(response_text)

        # التحقق من الصحة
        self._validate_plan(plan_data)

        return plan_data

    def _build_system_prompt(self) -> str:
        """
        بناء نص التعليمات للنظام.

        Build system prompt.

        Returns:
            نص التعليمات
        """
        return """
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

    def _build_user_content(self, objective: str, context: CollaborationContext) -> str:
        """
        بناء محتوى رسالة المستخدم.

        Build user message content.

        Args:
            objective: الهدف
            context: السياق

        Returns:
            محتوى الرسالة
        """
        shared_data = context.shared_memory
        return f"Objective: {objective}\nContext: {json.dumps(shared_data, default=str)}"

    def _parse_json_response(self, response_text: str) -> dict[str, object]:
        """
        تحليل رد الذكاء الاصطناعي كـ JSON منظم.

        Args:
            response_text: نص الرد

        Returns:
            بيانات الخطة
        """
        cleaned_response = self._clean_json_block(response_text)
        parsed = json.loads(cleaned_response)
        if not isinstance(parsed, dict):
            raise ValueError("AI response did not contain a JSON object")
        return parsed

    def _validate_plan(self, plan_data: dict[str, object]) -> None:
        """
        التحقق من صحة بيانات الخطة.

        Validate plan data.

        Args:
            plan_data: بيانات الخطة

        Raises:
            ValueError: إذا كانت البيانات غير صحيحة
        """
        if "steps" not in plan_data:
            raise ValueError("Missing 'steps' in AI plan")

    def _handle_json_decode_error(
        self, error: json.JSONDecodeError, response_text: str | None
    ) -> dict[str, object]:
        """
        معالجة خطأ تحليل JSON.

        Handle JSON decode error.

        Args:
            error: خطأ التحليل
            response_text: نص الرد (إن وجد)

        Returns:
            خطة طوارئ
        """
        logger.error(f"Strategist JSON parsing error: {error}")
        logger.error(f"Raw response: {response_text[:500] if response_text else 'N/A'}")

        # التحقق من رسالة Safety Net
        if response_text and "Unable to reach external intelligence" in response_text:
            logger.error("AI service unavailable - Safety Net activated")
            return self._create_ai_unavailable_plan()

        # خطة طوارئ (Fallback Plan)
        return {
            "strategy_name": "Emergency Fallback - JSON Error",
            "reasoning": f"Failed to parse AI response: {error}",
            "steps": [
                {
                    "name": "Report JSON Error",
                    "description": f"AI response was not valid JSON. Error: {error}",
                    "tool_hint": "log",
                }
            ],
        }

    def _handle_general_error(self, error: Exception) -> dict[str, object]:
        """
        معالجة الأخطاء العامة.

        Handle general errors.

        Args:
            error: الخطأ

        Returns:
            خطة طوارئ
        """
        logger.exception(f"Strategist failed to plan: {error}")
        return {
            "strategy_name": "Emergency Fallback",
            "reasoning": f"Planning failed due to: {type(error).__name__}: {error}",
            "steps": [
                {
                    "name": "Analyze Failure",
                    "description": f"Check why planning failed: {type(error).__name__}: {str(error)[:200]}",
                    "tool_hint": "unknown",
                }
            ],
        }

    def _create_ai_unavailable_plan(self) -> dict[str, object]:
        """
        إنشاء خطة لحالة عدم توفر خدمة AI.

        Create plan for AI service unavailable.

        Returns:
            خطة طوارئ
        """
        return {
            "strategy_name": "AI Service Unavailable",
            "reasoning": "Cannot proceed without AI service. Please configure OPENROUTER_API_KEY.",
            "steps": [
                {
                    "name": "Configuration Required",
                    "description": "OPENROUTER_API_KEY is not configured. Please set it in .env file.",
                    "tool_hint": "config",
                }
            ],
        }

    def _clean_json_block(self, text: str) -> str:
        """استخراج JSON من نص قد يحتوي على Markdown code blocks."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()

    async def consult(self, situation: str, analysis: dict[str, object]) -> dict[str, object]:
        """
        تقديم استشارة استراتيجية.
        Provide strategic consultation on the situation.

        Args:
            situation: وصف الموقف
            analysis: تحليل الموقف

        Returns:
            dict: التوصية والثقة
        """
        logger.info("Strategist is being consulted...")

        system_prompt = self._build_consult_system_prompt()
        user_message = self._build_consult_user_message(situation, analysis)

        try:
            response_text = await self.ai.send_message(
                system_prompt=system_prompt, user_message=user_message, temperature=0.3
            )

            return self._parse_json_response(response_text)
        except Exception as exc:
            return self._handle_consult_error(exc)

    def _record_plan_in_context(
        self,
        context: CollaborationContext,
        plan_data: dict[str, object],
    ) -> None:
        """
        تسجيل الخطة في سياق التعاون.

        Args:
            context: سياق التعاون
            plan_data: بيانات الخطة
        """
        context.update("last_plan", plan_data)

    def _build_consult_system_prompt(self) -> str:
        """
        بناء تعليمات الاستشارة الاستراتيجية للنظام.
        """
        return """
        أنت "الاستراتيجي" (The Strategist).
        دورك هو تحليل الموقف من منظور استراتيجي بعيد المدى.

        النقاط الأساسية:
        1. التوافق مع الأهداف العليا.
        2. تحليل الفرص والتهديدات الاستراتيجية.
        3. اقتراح نهج عام للحل.

        قدم توصية موجزة ومباشرة.
        الرد يجب أن يكون JSON فقط:
        {
            "recommendation": "string (english)",
            "confidence": float (0-100)
        }
        """

    def _build_consult_user_message(
        self, situation: str, analysis: dict[str, object]
    ) -> str:
        """
        بناء رسالة المستخدم للاستشارة الاستراتيجية.
        """
        return f"Situation: {situation}\nAnalysis: {json.dumps(analysis, default=str)}"

    def _handle_consult_error(self, error: Exception) -> dict[str, object]:
        """
        معالجة أخطاء الاستشارة وإرجاع توصية احتياطية.
        """
        logger.warning("Strategist consultation failed: %s", error)
        return {
            "recommendation": "Adopt a cautious strategic approach (AI consultation failed).",
            "confidence": 50.0,
        }


def _count_steps(plan_data: dict[str, object]) -> int:
    """يحسب عدد خطوات الخطة بشكل آمن."""

    steps = plan_data.get("steps")
    return len(steps) if isinstance(steps, list) else 0
