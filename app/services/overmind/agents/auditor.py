# app/services/overmind/agents/auditor.py
"""
الوكيل المدقق (Auditor Agent) - ضمير النظام.
---------------------------------------------------------
يقوم هذا الوكيل بمراجعة المخرجات والخطط للتأكد من سلامتها وأمانها
ومطابقتها لمعايير الجودة الصارمة.

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
"""

import hashlib
import json
import re

from app.core.ai_gateway import AIClient
from app.core.di import get_logger
from app.core.protocols import AgentReflector, CollaborationContext
from app.services.overmind.dec_pomdp_proof import (
    build_dec_pomdp_consultation_payload,
    is_dec_pomdp_proof_question,
)
from app.services.overmind.domain.exceptions import StalemateError

logger = get_logger(__name__)


class AuditorAgent(AgentReflector):
    """
    الناقد الداخلي (Internal Critic).

    المسؤوليات:
    1. مراجعة مخرجات التنفيذ (Self-Reflection).
    2. اكتشاف الأخطاء الأمنية أو المنطقية.
    3. الموافقة على إنهاء المهمة أو طلب تصحيح (Correction Loop).
    4. اكتشاف حلقات الاستدلال المفرغة (Infinite Loops).
    """

    def __init__(self, ai_client: AIClient) -> None:
        self.ai = ai_client

    def detect_loop(self, history_hashes: list[str], current_plan: dict[str, object]) -> None:
        """
        اكتشاف التكرار المفرط (Infinite Loops).

        يقوم بحساب بصمة (Hash) للخطة الحالية ومقارنتها بالتاريخ.

        Args:
            history_hashes: قائمة البصمات السابقة.
            current_plan: الخطة الحالية المقترحة.

        Raises:
            StalemateError: إذا تم اكتشاف تكرار.
        """
        current_hash = self._compute_hash(current_plan)

        # إذا تكررت نفس الخطة بالضبط في آخر 3 محاولات، فهذه مشكلة
        # أو إذا تكررت بشكل عام أكثر من مرتين
        if history_hashes.count(current_hash) >= 2:
            logger.warning(f"Infinite loop detected! Hash {current_hash} repeated.")
            raise StalemateError(
                "تم اكتشاف حلقة استدلال مفرغة. الخطة المقترحة تكررت عدة مرات دون تقدم."
            )

    def compute_plan_hash(self, plan: dict[str, object]) -> str:
        """
        توليد بصمة ثابتة لخطة محددة بغرض تتبع التكرار.
        """
        return self._compute_hash(plan)

    def _compute_hash(self, data: dict[str, object]) -> str:
        """حساب بصمة ثابتة للبيانات."""
        try:
            # ترتيب المفاتيح لضمان الثبات
            encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(encoded).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for loop detection: {e}")
            return "unknown_hash"

    async def review_work(
        self, result: dict[str, object], original_objective: str, context: CollaborationContext
    ) -> dict[str, object]:
        """
        مراجعة نتائج العمل ومقارنتها بالهدف الأصلي باستخدام الذكاء الاصطناعي.
        """
        logger.info("Auditor is reviewing the work using AI...")

        # 0. اكتشاف نوع المدخلات (هل هي خطة أم نتيجة؟)
        if (
            isinstance(result, dict)
            and "steps" in result
            and isinstance(result["steps"], list)
            and "strategy_name" in result
        ):
            logger.info("Auditor detected a Plan. Switching to Plan Review mode.")
            return await self._review_plan(result, original_objective)

        # 1. التحقق السريع (Fast Fail)
        result_str = str(result).lower()
        if "error" in result_str and len(result_str) < 200:
            # أخطاء قصيرة وواضحة نرفضها فوراً
            logger.warning("Auditor detected explicit errors (Fast Fail).")
            return {
                "approved": False,
                "feedback": "تم اكتشاف رسالة خطأ صريحة في التنفيذ. يرجى تحليل الخطأ ومحاولة استراتيجية بديلة.",
                "confidence": 0.9,
            }

        # 2. المراجعة العميقة (Deep Review via AI)
        system_prompt = """
        أنت "المدقق" (The Auditor)، مراجع ذكي ومتفهم.
        دورك هو مراجعة نتائج تنفيذ المهام للتأكد من أنها:
        1. بدأت في تحقيق الهدف الأصلي (خطوات أولية مقبولة).
        2. خالية من الأخطاء الأمنية الخطيرة.
        3. تمثل تقدماً حقيقياً حتى لو كان جزئياً.

        كن متسامحاً مع الخطوات الجزئية إذا كانت صحيحة الاتجاه.
        الموافقة تعني: "نعم، هذا تقدم جيد ويمكننا البناء عليه".
        الرفض يعني فقط: "هناك خطأ جوهري يمنع التقدم".

        تنسيق الإجابة يجب أن يكون JSON فقط:
        {
            "approved": boolean,
            "feedback": "string (arabic)",
            "score": float (0.0 - 1.0)
        }
        """

        user_message = f"""
        الهدف الأصلي: {original_objective}

        نتائج التنفيذ (أو الخطة المقترحة):
        {json.dumps(result, ensure_ascii=False, default=str)}

        هل تم تحقيق الهدف بنجاح؟ قدم تحليلاً نقدياً.
        """

        try:
            response_json = await self.ai.send_message(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.1,  # درجة حرارة منخفضة للدقة
            )

            # استخدام دالة تنظيف أكثر قوة
            clean_json = self._clean_json_block(response_json)
            review_data = json.loads(clean_json)

            return {
                "approved": review_data.get("approved", False),
                "feedback": review_data.get("feedback", "لم يتم تقديم ملاحظات."),
                "score": review_data.get("score", 0.0),
            }

        except Exception as e:
            logger.error(f"AI Auditor failed: {e}")
            # في حال فشل المدقق الذكي، نعود للمنطق الدفاعي (رفض لضمان الأمان)
            return {
                "approved": False,
                "feedback": f"فشل نظام التدقيق الذكي. يرجى إعادة المحاولة. الخطأ: {e!s}",
                "confidence": 0.0,
            }

    async def _review_plan(self, plan: dict[str, object], objective: str) -> dict[str, object]:
        """
        مراجعة خطة العمل (وليس النتائج).
        Review the proposed plan logic.
        """
        system_prompt = """
        أنت "المدقق" (The Auditor).
        دورك هو مراجعة "خطة عمل" (Action Plan) مقترحة من الاستراتيجي.

        معايير قبول الخطة:
        1. هل الخطوات منطقية وتؤدي لتحقيق الهدف؟
        2. هل الخطة آمنة؟ (لا تتضمن حذف ملفات حساسة أو وصول غير مصرح).
        3. هل الأدوات المقترحة تبدو مناسبة؟

        إذا كانت الخطة جيدة، وافق عليها فوراً.
        لا ترفض الخطة لأنها "لم تنفذ بعد". هي مجرد خطة.

        تنسيق الإجابة JSON فقط:
        {
            "approved": boolean,
            "feedback": "string (arabic)",
            "score": float (0.0 - 1.0)
        }
        """

        user_message = f"""
        الهدف: {objective}

        الخطة المقترحة:
        {json.dumps(plan, ensure_ascii=False, default=str)}

        هل الخطة منطقية وآمنة للتنفيذ؟
        """

        try:
            response_json = await self.ai.send_message(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.1,
            )

            clean_json = self._clean_json_block(response_json)
            review_data = json.loads(clean_json)

            return {
                "approved": review_data.get("approved", False),
                "feedback": review_data.get("feedback", "لم يتم تقديم ملاحظات."),
                "score": review_data.get("score", 0.0),
            }

        except Exception as e:
            logger.error(f"AI Plan Auditor failed: {e}")
            return {
                "approved": False,
                "feedback": f"فشل تدقيق الخطة: {e}",
                "confidence": 0.0,
            }

    async def consult(self, situation: str, analysis: dict[str, object]) -> dict[str, object]:
        """
        تقديم استشارة رقابية.
        Provide audit and safety consultation.

        Args:
            situation: وصف الموقف
            analysis: تحليل الموقف

        Returns:
            dict: التوصية والثقة
        """
        logger.info("Auditor is being consulted...")

        if is_dec_pomdp_proof_question(situation):
            return build_dec_pomdp_consultation_payload("auditor")

        system_prompt = """
        أنت "المدقق" (The Auditor).
        دورك هو تحليل الموقف من منظور الأمان والجودة والمخاطر.

        النقاط الأساسية:
        1. المخاطر الأمنية (Security Risks).
        2. معايير الجودة (Quality Standards).
        3. الامتثال للسياسات (Compliance).

        قدم توصية موجزة ومباشرة.
        الرد يجب أن يكون JSON فقط:
        {
            "recommendation": "string (english)",
            "confidence": float (0-100)
        }
        """

        user_message = f"Situation: {situation}\nAnalysis: {json.dumps(analysis, default=str)}"

        try:
            response_text = await self.ai.send_message(
                system_prompt=system_prompt, user_message=user_message, temperature=0.3
            )

            clean_json = self._clean_json_block(response_text)
            return json.loads(clean_json)
        except Exception as e:
            logger.warning(f"Auditor consultation failed: {e}")
            return {
                "recommendation": "Maintain high safety standards and verify risks (AI consultation failed).",
                "confidence": 50.0,
            }

    def _clean_json_block(self, text: str) -> str:
        """استخراج JSON من نص قد يحتوي على Markdown code blocks."""
        text = text.strip()

        # 1. محاولة استخراج JSON من كتل الكود (Markdown)
        json_code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(json_code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 2. محاولة استخراج JSON من بين الأقواس (Outermost Braces)
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()

        # 3. في حال عدم العثور على أي هيكل JSON، نعيد كائن فارغ نصي لتجنب الانهيار
        # هذا سيؤدي إلى dictionary فارغ، مما يجعل review_work يعيد قيم افتراضية (False)
        return "{}"
