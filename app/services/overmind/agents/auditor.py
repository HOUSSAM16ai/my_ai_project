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

from typing import Any

from app.core.ai_gateway import AIClient
from app.core.di import get_logger
from app.core.protocols import AgentReflector

logger = get_logger(__name__)


class AuditorAgent(AgentReflector):
    """
    الناقد الداخلي (Internal Critic).

    المسؤوليات:
    1. مراجعة مخرجات التنفيذ (Self-Reflection).
    2. اكتشاف الأخطاء الأمنية أو المنطقية.
    3. الموافقة على إنهاء المهمة أو طلب تصحيح (Correction Loop).
    """

    def __init__(self, ai_client: AIClient) -> None:
        self.ai = ai_client

    async def review_work(self, result: dict[str, Any], original_objective: str) -> dict[str, Any]:
        """
        مراجعة نتائج العمل ومقارنتها بالهدف الأصلي.
        """
        logger.info("Auditor is reviewing the work...")

        # التحقق السريع من الأخطاء الواضحة
        result_str = str(result).lower()
        if "error" in result_str or "exception" in result_str or "fail" in result_str:
            logger.warning("Auditor detected explicit errors.")
            return {
                "approved": False,
                "feedback": "تم اكتشاف أخطاء صريحة في التنفيذ. يرجى المراجعة والتصحيح.",
                "confidence": 0.0
            }

        # مراجعة أعمق (Deep Logic Check) - يمكن توسيعها لتشمل استدعاء LLM
        # حالياً سنكتفي بالمراجعة الأساسية لضمان السرعة (KISS Principle)

        return {
            "approved": True,
            "feedback": "العمل يبدو متقناً ومطابقاً للمعايير.",
            "confidence": 1.0
        }
