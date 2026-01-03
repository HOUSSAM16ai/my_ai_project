"""
محلل المواقف (Situation Analyzer).

مسؤول عن تحليل المواقف وفهم السياق بشكل عميق.
"""

from datetime import datetime
from typing import Any

from app.core.di import get_logger

logger = get_logger(__name__)


class SituationAnalyzer:
    """
    محلل المواقف الذكي.
    """

    @staticmethod
    async def analyze(
        situation: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        تحليل الموقف بشكل شامل ومتعدد الأبعاد.

        Args:
            situation: وصف الموقف
            context: السياق والمعلومات الإضافية

        Returns:
            dict: تحليل شامل (SWOT متقدم)
        """
        logger.info(f"Analyzing situation: {situation[:50]}...")

        analysis = {
            "situation": situation,
            "timestamp": datetime.utcnow().isoformat(),
            "complexity_level": "medium",
            "urgency": "normal",
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
