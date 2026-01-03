"""
مركب القرارات (Decision Synthesizer).

مسؤول عن تجميع الآراء وتركيب القرار النهائي.
"""

from typing import Any

from app.core.di import get_logger
from app.services.overmind.domain.super_intelligence.models import (
    Decision,
    DecisionCategory,
    DecisionImpact,
    DecisionPriority,
)

logger = get_logger(__name__)


class DecisionSynthesizer:
    """
    مركب القرارات الذكي.
    """

    @staticmethod
    async def synthesize(
        situation: str,
        analysis: dict[str, Any],
        consultations: dict[str, Any],
    ) -> Decision:
        """
        تركيب القرار النهائي من آراء الوكلاء.

        Args:
            situation: الموقف
            analysis: التحليل
            consultations: الاستشارات

        Returns:
            Decision: القرار النهائي
        """
        logger.info("Synthesizing final decision from consultations...")

        agents_involved = list(consultations.keys())

        # حساب متوسط الثقة
        avg_confidence = sum(
            c["confidence"] for c in consultations.values()
        ) / max(len(consultations), 1)

        # تحديد الأولويات والتأثير
        priority = DecisionPriority.MEDIUM
        if analysis.get("urgency") == "high":
            priority = DecisionPriority.CRITICAL

        complexity = analysis.get("complexity_level", "medium")
        impact = DecisionImpact.MEDIUM_TERM
        if complexity == "high":
            impact = DecisionImpact.LONG_TERM
        elif complexity == "low":
            impact = DecisionImpact.SHORT_TERM

        # إنشاء القرار
        decision = Decision(
            category=DecisionCategory.STRATEGIC,
            priority=priority,
            impact=impact,
            title=f"Autonomous Decision: {situation[:50]}",
            description=situation,
            reasoning=(
                "بعد استشارة جميع الوكلاء وتحليل الموقف بشكل شامل، "
                "تم التوصل إلى هذا القرار بناءً على الحكمة الجماعية. "
                f"مستوى التعقيد: {complexity}, "
                f"الإلحاح: {analysis.get('urgency', 'normal')}, "
                f"متوسط ثقة الوكلاء: {avg_confidence:.1f}%"
            ),
            agents_involved=agents_involved,
        )

        # إضافة البيانات الافتراضية للقرار (يمكن تحسينها لاحقاً لتكون ديناميكية)
        decision.alternatives_considered = [
            {
                "option": "Do nothing",
                "pros": ["No resource consumption", "No risk"],
                "cons": ["Problem persists", "Missed opportunity"],
                "rejected_because": "Passive approach doesn't align with improvement goals",
            },
            {
                "option": "Immediate action",
                "pros": ["Quick resolution"],
                "cons": ["May not be optimal"],
                "rejected_because": "Need thorough analysis first",
            },
        ]

        decision.expected_outcomes = [
            "Improved system performance",
            "Enhanced user experience",
            "Better long-term sustainability",
        ]

        decision.risks = [
            {"risk": "Unexpected side effects", "probability": "low", "impact": "medium"},
        ]

        decision.mitigation_strategies = [
            "Implement gradual rollout",
            "Monitor metrics closely",
        ]

        decision.success_criteria = [
            "System stability maintained",
            "Performance metrics improved",
        ]

        # حساب الثقة النهائية
        decision.calculate_confidence()

        logger.info(
            f"Decision synthesized: {decision.title} "
            f"(confidence: {decision.confidence_score:.1f}%)"
        )

        return decision
