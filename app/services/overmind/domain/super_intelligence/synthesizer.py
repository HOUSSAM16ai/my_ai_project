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
        Synthesize final decision from agent consultations.

        Args:
            situation: الموقف
            analysis: التحليل
            consultations: الاستشارات

        Returns:
            Decision: القرار النهائي
        """
        logger.info("Synthesizing final decision from consultations...")

        # 1. استخراج المعلومات الأساسية | Extract basic info
        agents_involved = list(consultations.keys())
        avg_confidence = DecisionSynthesizer._calculate_average_confidence(consultations)

        # 2. تحديد الأولوية والتأثير | Determine priority and impact
        priority = DecisionSynthesizer._determine_priority(analysis)
        impact = DecisionSynthesizer._determine_impact(analysis)

        # 3. إنشاء القرار الأساسي | Create base decision
        decision = DecisionSynthesizer._create_base_decision(
            situation, analysis, avg_confidence, priority, impact, agents_involved
        )

        # 4. إضافة البيانات التفصيلية | Populate detailed data
        DecisionSynthesizer._populate_decision_details(decision)

        # 5. حساب الثقة النهائية | Calculate final confidence
        decision.calculate_confidence()

        logger.info(
            f"Decision synthesized: {decision.title} "
            f"(confidence: {decision.confidence_score:.1f}%)"
        )

        return decision

    @staticmethod
    def _calculate_average_confidence(consultations: dict[str, Any]) -> float:
        """
        حساب متوسط الثقة من الاستشارات.
        Calculate average confidence from consultations.
        """
        if not consultations:
            return 0.0
        return sum(c["confidence"] for c in consultations.values()) / len(consultations)

    @staticmethod
    def _determine_priority(analysis: dict[str, Any]) -> DecisionPriority:
        """
        تحديد أولوية القرار.
        Determine decision priority based on urgency.
        """
        urgency = analysis.get("urgency")
        urgency_score = analysis.get("urgency_score", 0.0)
        if isinstance(urgency_score, (int, float)) and urgency_score >= 0.8:
            return DecisionPriority.CRITICAL
        if isinstance(urgency_score, (int, float)) and urgency_score >= 0.5:
            return DecisionPriority.HIGH
        if urgency == "high":
            return DecisionPriority.CRITICAL
        return DecisionPriority.MEDIUM

    @staticmethod
    def _determine_impact(analysis: dict[str, Any]) -> DecisionImpact:
        """
        تحديد تأثير القرار.
        Determine decision impact based on complexity.
        """
        complexity = analysis.get("complexity_level", "medium")
        complexity_score = analysis.get("complexity_score", 0.0)
        if isinstance(complexity_score, (int, float)) and complexity_score >= 0.8:
            return DecisionImpact.GENERATIONAL
        if isinstance(complexity_score, (int, float)) and complexity_score >= 0.6:
            return DecisionImpact.LONG_TERM
        if complexity == "high":
            return DecisionImpact.LONG_TERM
        elif complexity == "low":
            return DecisionImpact.SHORT_TERM
        return DecisionImpact.MEDIUM_TERM

    @staticmethod
    def _create_base_decision(
        situation: str,
        analysis: dict[str, Any],
        avg_confidence: float,
        priority: DecisionPriority,
        impact: DecisionImpact,
        agents_involved: list[str],
    ) -> Decision:
        """
        إنشاء القرار الأساسي.
        Create base decision object with core information.
        """
        complexity = analysis.get("complexity_level", "medium")
        urgency = analysis.get("urgency", "normal")

        category = DecisionSynthesizer._determine_category(analysis)
        reasoning = DecisionSynthesizer._compose_reasoning(
            analysis=analysis,
            avg_confidence=avg_confidence,
        )

        return Decision(
            category=category,
            priority=priority,
            impact=impact,
            title=f"Autonomous Decision: {situation[:50]}",
            description=situation,
            reasoning=(
                "بعد استشارة جميع الوكلاء وتحليل الموقف بشكل شامل، "
                "تم التوصل إلى هذا القرار بناءً على الحكمة الجماعية. "
                f"مستوى التعقيد: {complexity}, "
                f"الإلحاح: {urgency}, "
                f"{reasoning}"
            ),
            agents_involved=agents_involved,
        )

    @staticmethod
    def _populate_decision_details(decision: Decision) -> None:
        """
        ملء تفاصيل القرار الإضافية.
        Populate additional decision details (alternatives, outcomes, risks).
        """
        decision.alternatives_considered = DecisionSynthesizer._get_default_alternatives()
        decision.expected_outcomes = DecisionSynthesizer._get_default_outcomes()
        decision.risks = DecisionSynthesizer._get_default_risks()
        decision.mitigation_strategies = DecisionSynthesizer._get_default_mitigations()
        decision.success_criteria = DecisionSynthesizer._get_default_success_criteria()

    @staticmethod
    def _get_default_alternatives() -> list[dict[str, Any]]:
        """
        الحصول على البدائل الافتراضية.
        Get default alternatives for decision.
        """
        return [
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

    @staticmethod
    def _get_default_outcomes() -> list[str]:
        """
        الحصول على النتائج المتوقعة الافتراضية.
        Get default expected outcomes.
        """
        return [
            "Improved system performance",
            "Enhanced user experience",
            "Better long-term sustainability",
        ]

    @staticmethod
    def _determine_category(analysis: dict[str, Any]) -> DecisionCategory:
        """
        تحديد فئة القرار باستخدام مؤشرات المخاطر والقيمة الاستراتيجية.
        """
        strategic_value = analysis.get("strategic_value_score", 0.0)
        risk_index = analysis.get("risk_index", 0.0)
        depth_score = analysis.get("depth_score", 0.0)

        if isinstance(strategic_value, (int, float)) and strategic_value >= 0.6:
            return DecisionCategory.STRATEGIC
        if isinstance(risk_index, (int, float)) and risk_index >= 0.7:
            return DecisionCategory.RISK_MANAGEMENT
        if isinstance(depth_score, (int, float)) and depth_score >= 0.7:
            return DecisionCategory.ARCHITECTURAL
        return DecisionCategory.TECHNICAL

    @staticmethod
    def _compose_reasoning(*, analysis: dict[str, Any], avg_confidence: float) -> str:
        """
        صياغة جزء منطق القرار اعتماداً على المؤشرات الكمية.
        """
        strategic_value = analysis.get("strategic_value_score")
        risk_index = analysis.get("risk_index")
        depth_score = analysis.get("depth_score")
        confidence = f"متوسط ثقة الوكلاء: {avg_confidence:.1f}%"

        parts = [confidence]
        if isinstance(strategic_value, (int, float)):
            parts.append(f"القيمة الاستراتيجية: {strategic_value:.2f}")
        if isinstance(risk_index, (int, float)):
            parts.append(f"مؤشر المخاطرة: {risk_index:.2f}")
        if isinstance(depth_score, (int, float)):
            parts.append(f"عمق التحليل: {depth_score:.2f}")

        return ", ".join(parts)

    @staticmethod
    def _get_default_risks() -> list[dict[str, str]]:
        """
        الحصول على المخاطر الافتراضية.
        Get default risks.
        """
        return [
            {"risk": "Unexpected side effects", "probability": "low", "impact": "medium"},
        ]

    @staticmethod
    def _get_default_mitigations() -> list[str]:
        """
        الحصول على استراتيجيات التخفيف الافتراضية.
        Get default mitigation strategies.
        """
        return [
            "Implement gradual rollout",
            "Monitor metrics closely",
        ]

    @staticmethod
    def _get_default_success_criteria() -> list[str]:
        """
        الحصول على معايير النجاح الافتراضية.
        Get default success criteria.
        """
        return [
            "System stability maintained",
            "Performance metrics improved",
        ]
