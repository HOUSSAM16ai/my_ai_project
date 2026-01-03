"""
نظام الذكاء الجماعي الفائق (Super Collective Intelligence System).

الواجهة الرئيسية (Facade) للنظام.
"""

from datetime import datetime
from typing import Any
import random

from app.core.di import get_logger
from app.services.overmind.agents import AgentCouncil
from app.services.overmind.collaboration import CollaborationHub
from app.services.overmind.domain.super_intelligence.models import Decision
from app.services.overmind.domain.super_intelligence.analyzer import SituationAnalyzer
from app.services.overmind.domain.super_intelligence.synthesizer import DecisionSynthesizer

logger = get_logger(__name__)


class SuperCollectiveIntelligence:
    """
    الذكاء الجماعي الفائق.

    يوفر نقطة دخول موحدة (Facade) لعمليات اتخاذ القرار المعقدة.
    """

    def __init__(
        self,
        agent_council: AgentCouncil,
        collaboration_hub: CollaborationHub,
    ) -> None:
        self.council = agent_council
        self.hub = collaboration_hub

        # الحالة
        self.decision_history: list[Decision] = []
        self.total_decisions = 0
        self.successful_decisions = 0
        self.failed_decisions = 0

        logger.info("Super Collective Intelligence initialized (Refactored)")

    async def make_autonomous_decision(
        self,
        situation: str,
        context: dict[str, Any] | None = None,
    ) -> Decision:
        """
        اتخاذ قرار مستقل بشكل كامل.
        """
        logger.info("=== Making Autonomous Decision ===")
        context = context or {}

        # 1. التحليل
        analysis = await SituationAnalyzer.analyze(situation, context)

        # 2. الاستشارة (Delegate to internal method for now, can be extracted later)
        consultations = await self._consult_agents(situation, analysis)

        # 3. التركيب
        decision = await DecisionSynthesizer.synthesize(situation, analysis, consultations)

        # 4. التسجيل
        if self.hub:
            # Check if store_data is async or sync. Assuming sync based on previous code,
            # but usually I/O is async. If it fails, wrap in try/except.
            try:
                self.hub.store_data("last_autonomous_decision", decision.model_dump())
            except Exception as e:
                logger.warning(f"Failed to store decision in hub: {e}")

        self.decision_history.append(decision)
        self.total_decisions += 1

        return decision

    async def _consult_agents(
        self,
        situation: str,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        استشارة الوكلاء (محاكاة حالياً، يجب ربطها بالوكلاء الحقيقيين لاحقاً).
        """
        logger.info("Consulting agents...")
        # TODO: Replace with actual calls to self.council.agents

        consultations = {
            "strategist": {"recommendation": "Strategic approach needed", "confidence": random.uniform(80, 95)},
            "architect": {"recommendation": "Ensure scalability", "confidence": random.uniform(75, 90)},
            "operator": {"recommendation": "Check resources", "confidence": random.uniform(70, 85)},
            "auditor": {"recommendation": "Verify safety", "confidence": random.uniform(85, 98)},
        }

        if self.hub:
            for agent, data in consultations.items():
                self.hub.record_contribution(
                    agent_name=agent,
                    action="consultation",
                    input_data={"situation": situation[:50]},
                    output_data=data,
                    success=True,
                )

        return consultations

    async def execute_decision(self, decision: Decision) -> dict[str, Any]:
        """
        تنفيذ القرار.
        """
        logger.info(f"Executing decision: {decision.id}")

        decision.executed = True
        execution_success = decision.confidence_score > 70

        result = {
            "decision_id": decision.id,
            "executed": True,
            "success": execution_success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if execution_success:
            self.successful_decisions += 1
            decision.outcome = "success"
        else:
            self.failed_decisions += 1
            decision.outcome = "failed"

        return result

    def get_statistics(self) -> dict[str, Any]:
        """
        إحصائيات النظام.
        """
        success_rate = 0.0
        if self.total_decisions > 0:
            success_rate = (self.successful_decisions / self.total_decisions) * 100

        return {
            "total_decisions": self.total_decisions,
            "successful": self.successful_decisions,
            "failed": self.failed_decisions,
            "success_rate": success_rate,
        }
