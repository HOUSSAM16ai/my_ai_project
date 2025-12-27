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
from typing import Any

from app.core.ai_gateway import AIClient
from app.core.di import get_logger
from app.core.protocols import AgentReflector, CollaborationContext
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

    def detect_loop(self, history_hashes: list[str], current_plan: dict[str, Any]) -> None:
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

    def _compute_hash(self, data: dict[str, Any]) -> str:
        """حساب بصمة ثابتة للبيانات."""
        try:
            # ترتيب المفاتيح لضمان الثبات
            encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(encoded).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for loop detection: {e}")
            return "unknown_hash"

    async def review_work(
        self,
        result: dict[str, Any],
        original_objective: str,
        context: CollaborationContext
    ) -> dict[str, Any]:
        """
        مراجعة نتائج العمل ومقارنتها بالهدف الأصلي باستخدام الذكاء الاصطناعي.
        """
        logger.info("Auditor is reviewing the work using AI...")

        # 1. التحقق السريع (Fast Fail)
        result_str = str(result).lower()
        if "error" in result_str and len(result_str) < 200:
             # أخطاء قصيرة وواضحة نرفضها فوراً
            logger.warning("Auditor detected explicit errors (Fast Fail).")
            return {
                "approved": False,
                "feedback": "تم اكتشاف رسالة خطأ صريحة في التنفيذ. يرجى تحليل الخطأ ومحاولة استراتيجية بديلة.",
                "confidence": 0.9
            }

        # 2. المراجعة العميقة (Deep Review via AI)
        system_prompt = """
        أنت "المدقق" (The Auditor)، ضمير النظام الصارم.
        دورك هو مراجعة نتائج تنفيذ المهام للتأكد من أنها:
        1. حققت الهدف الأصلي بدقة.
        2. خالية من الأخطاء المنطقية أو الأمنية.
        3. كاملة وليست مجرد خطوات جزئية (إلا إذا كان المطلوب خطوة جزئية).

        يجب أن تكون نقدياً جداً. لا تقبل إجابات مثل "سأقوم بذلك لاحقاً". العمل يجب أن يكون قد تم.

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
                temperature=0.1 # درجة حرارة منخفضة للدقة
            )

            # تنظيف الرد من أي نصوص زائدة (Markdown fences)
            clean_json = response_json.replace("```json", "").replace("```", "").strip()
            review_data = json.loads(clean_json)

            return {
                "approved": review_data.get("approved", False),
                "feedback": review_data.get("feedback", "لم يتم تقديم ملاحظات."),
                "score": review_data.get("score", 0.0)
            }

        except Exception as e:
            logger.error(f"AI Auditor failed: {e}")
            # في حال فشل المدقق الذكي، نعود للمنطق الدفاعي (رفض لضمان الأمان)
            return {
                "approved": False,
                "feedback": f"فشل نظام التدقيق الذكي. يرجى إعادة المحاولة. الخطأ: {e!s}",
                "confidence": 0.0
            }
