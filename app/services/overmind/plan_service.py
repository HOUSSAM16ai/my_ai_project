"""
خدمة تخطيط الوكلاء (Agent Plan Service).
---------------------------------------
تنفذ هذه الخدمة منطق توليد الخطط وتطبيعها للاستهلاك عبر API،
مع فصل واضح بين المنطق المعرفي وعرض البيانات.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.ai_gateway import get_ai_client
from app.core.di import get_logger
from app.services.overmind.agents.strategist import StrategistAgent
from app.services.overmind.domain.api_schemas import (
    AgentPlanData,
    AgentPlanStepResponse,
    AgentsPlanRequest,
)
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.plan_registry import AgentPlanRecord

logger = get_logger(__name__)


class AgentPlanService:
    """
    منسق توليد خطط الوكلاء.

    يعتمد على وكيل الاستراتيجي لتوليد خطة أولية ثم يحولها إلى نموذج
    استجابة متوافق مع العقد.
    """

    def __init__(self, strategist: StrategistAgent | None = None) -> None:
        self._strategist = strategist or StrategistAgent(get_ai_client())

    async def create_plan(self, payload: AgentsPlanRequest) -> AgentPlanRecord:
        """
        إنشاء خطة وكيل جديدة.

        Args:
            payload: بيانات الطلب الواردة من API.

        Returns:
            AgentPlanRecord: السجل النهائي للخطة.
        """
        collab_context = InMemoryCollaborationContext(payload.context)
        collab_context.update("constraints", payload.constraints)
        collab_context.update("priority", payload.priority.value)

        plan_data = await self._strategist.create_plan(payload.objective, collab_context)
        steps = self._normalize_steps(plan_data)

        plan_id = f"plan_{uuid4().hex}"
        created_at = datetime.now(UTC)

        logger.info("Agent plan created", extra={"plan_id": plan_id})

        plan_data = AgentPlanData(
            plan_id=plan_id,
            objective=payload.objective,
            steps=steps,
            created_at=created_at,
        )

        return AgentPlanRecord(data=plan_data)

    def _normalize_steps(self, plan_data: dict[str, Any]) -> list[AgentPlanStepResponse]:
        """
        تطبيع خطوات الخطة القادمة من وكيل الاستراتيجي.

        Args:
            plan_data: البيانات الخام من نموذج الذكاء الاصطناعي.

        Returns:
            list[AgentPlanStepResponse]: خطوات منظمة وفق العقد.
        """
        raw_steps = plan_data.get("steps", [])
        steps: list[AgentPlanStepResponse] = []

        for index, step in enumerate(raw_steps, start=1):
            step_name = str(step.get("name") or step.get("title") or f"Step {index}")
            description = str(step.get("description") or "")
            dependencies = step.get("dependencies") or []
            if not isinstance(dependencies, list):
                dependencies = [str(dependencies)]
            dependencies = [str(dep) for dep in dependencies]
            estimated_effort = step.get("estimated_effort") or step.get("effort")

            steps.append(
                AgentPlanStepResponse(
                    step_id=f"step-{index:02d}",
                    title=step_name,
                    description=description,
                    dependencies=dependencies,
                    estimated_effort=str(estimated_effort)
                    if estimated_effort is not None
                    else None,
                )
            )

        return steps
