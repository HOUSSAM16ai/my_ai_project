"""
محلل المواقف (Situation Analyzer).

مسؤول عن تحليل المواقف وفهم السياق بشكل عميق عبر إشارات كمية واضحة.
"""

from datetime import datetime

from app.core.di import get_logger

logger = get_logger(__name__)


class SituationAnalyzer:
    """
    محلل المواقف الذكي.
    """

    @staticmethod
    async def analyze(
        situation: str,
        context: dict[str, object],
    ) -> dict[str, object]:
        """
        تحليل الموقف بشكل شامل ومتعدد الأبعاد.

        Args:
            situation: وصف الموقف
            context: السياق والمعلومات الإضافية

        Returns:
            dict[str, object]: تحليل شامل (SWOT متقدم)
        """
        logger.info(f"Analyzing situation: {situation[:50]}...")

        signal_scores = SituationAnalyzer._calculate_signal_scores(situation)
        risk_index = SituationAnalyzer._aggregate_risk_index(signal_scores)
        strategic_value = SituationAnalyzer._estimate_strategic_value(signal_scores, context)
        depth_profile = SituationAnalyzer._build_depth_profile(situation, context, signal_scores)
        depth_score = depth_profile["depth_score"]

        analysis = {
            "situation": situation,
            "timestamp": datetime.utcnow().isoformat(),
            "complexity_level": "medium",
            "urgency": "normal",
            "complexity_score": signal_scores["complexity"],
            "urgency_score": signal_scores["urgency"],
            "novelty_score": signal_scores["novelty"],
            "risk_index": risk_index,
            "strategic_value_score": strategic_value,
            "depth_score": depth_score,
            "depth_profile": depth_profile,
            "stakeholders": [],
            "constraints": [],
            "opportunities": [],
            "threats": [],
        }

        # تحليل التعقيد (Complexity Analysis)
        complexity_keywords = ["complex", "difficult", "challenging", "معقد", "صعب"]
        complexity_score = sum(1 for keyword in complexity_keywords if keyword in situation.lower())

        # زيادة الدرجة في حال وجود مُعززات (Intensifiers)
        if "very complex" in situation.lower():
            complexity_score += 1

        if complexity_score >= 2:
            analysis["complexity_level"] = "high"
        elif complexity_score == 1:
            analysis["complexity_level"] = "medium"
        else:
            analysis["complexity_level"] = "low"

        # تحليل الإلحاح (Urgency Analysis)
        urgency_keywords = ["urgent", "critical", "immediate", "عاجل", "حرج", "فوري"]
        if any(keyword in situation.lower() for keyword in urgency_keywords):
            analysis["urgency"] = "high"

        # استخراج المعلومات من السياق
        if "constraints" in context:
            analysis["constraints"] = context["constraints"]
        if "opportunities" in context:
            analysis["opportunities"] = context["opportunities"]
        if "threats" in context:
            analysis["threats"] = context["threats"]

        # إضافة الأطراف المعنية
        analysis["stakeholders"] = ["system", "users", "developers", "overmind"]

        logger.info(
            f"Situation analyzed: complexity={analysis['complexity_level']}, "
            f"urgency={analysis['urgency']}"
        )

        return analysis

    @staticmethod
    def _calculate_signal_scores(situation: str) -> dict[str, float]:
        """
        استخراج درجات الإشارات الأساسية من وصف الموقف.

        Args:
            situation: وصف الموقف الخام

        Returns:
            dict[str, float]: درجات الإشارات (0.0 - 1.0)
        """
        normalized = situation.lower()
        complexity_keywords = ["complex", "difficult", "challenging", "معقد", "صعب"]
        urgency_keywords = ["urgent", "critical", "immediate", "عاجل", "حرج", "فوري"]
        novelty_keywords = ["new", "novel", "innovative", "غير مسبوق", "ابتكار"]

        complexity = min(
            sum(1 for keyword in complexity_keywords if keyword in normalized) / 3, 1.0
        )
        urgency = min(sum(1 for keyword in urgency_keywords if keyword in normalized) / 2, 1.0)
        novelty = min(sum(1 for keyword in novelty_keywords if keyword in normalized) / 2, 1.0)

        return {
            "complexity": round(complexity, 2),
            "urgency": round(urgency, 2),
            "novelty": round(novelty, 2),
        }

    @staticmethod
    def _aggregate_risk_index(signal_scores: dict[str, float]) -> float:
        """
        دمج الإشارات لإنتاج مؤشر مخاطرة موحد.

        Args:
            signal_scores: درجات الإشارات الأساسية

        Returns:
            float: مؤشر المخاطرة (0.0 - 1.0)
        """
        complexity = signal_scores.get("complexity", 0.0)
        urgency = signal_scores.get("urgency", 0.0)
        novelty = signal_scores.get("novelty", 0.0)

        risk_index = (complexity * 0.5) + (urgency * 0.3) + (novelty * 0.2)
        return round(min(risk_index, 1.0), 2)

    @staticmethod
    def _estimate_strategic_value(
        signal_scores: dict[str, float],
        context: dict[str, object],
    ) -> float:
        """
        تقدير القيمة الاستراتيجية استناداً إلى الإشارات والسياق.

        Args:
            signal_scores: درجات الإشارات الأساسية
            context: سياق إضافي للمهمة

        Returns:
            float: قيمة استراتيجية (0.0 - 1.0)
        """
        opportunity_bonus = 0.0
        opportunities = context.get("opportunities")
        if isinstance(opportunities, list):
            opportunity_bonus = min(len(opportunities) / 5, 1.0)

        novelty = signal_scores.get("novelty", 0.0)
        complexity = signal_scores.get("complexity", 0.0)

        strategic_value = (novelty * 0.6) + (opportunity_bonus * 0.4) + (complexity * 0.2)
        return round(min(strategic_value, 1.0), 2)

    @staticmethod
    def _build_depth_profile(
        situation: str,
        context: dict[str, object],
        signal_scores: dict[str, float],
    ) -> dict[str, float]:
        """
        قياس عمق التحليل وفقاً لغنى المعطيات والسياق.

        Args:
            situation: وصف الموقف
            context: سياق إضافي للمهمة
            signal_scores: درجات الإشارات الأساسية

        Returns:
            dict[str, float]: ملف عمق التحليل ومكوناته
        """
        constraints = context.get("constraints")
        opportunities = context.get("opportunities")
        threats = context.get("threats")

        constraint_count = len(constraints) if isinstance(constraints, list) else 0
        opportunity_count = len(opportunities) if isinstance(opportunities, list) else 0
        threat_count = len(threats) if isinstance(threats, list) else 0

        context_richness = min((constraint_count + opportunity_count + threat_count) / 6, 1.0)
        signal_diversity = (
            signal_scores.get("complexity", 0.0)
            + signal_scores.get("urgency", 0.0)
            + signal_scores.get("novelty", 0.0)
        ) / 3
        narrative_density = min(len(situation.split()) / 40, 1.0)

        depth_score = (
            (context_richness * 0.5) + (signal_diversity * 0.3) + (narrative_density * 0.2)
        )
        return {
            "context_richness": round(context_richness, 2),
            "signal_diversity": round(signal_diversity, 2),
            "narrative_density": round(narrative_density, 2),
            "depth_score": round(min(depth_score, 1.0), 2),
        }
