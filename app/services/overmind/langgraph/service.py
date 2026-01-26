from __future__ import annotations

import uuid

from app.core.ai_gateway import get_ai_client
from app.services.agent_tools import get_registry
from app.services.overmind.agents.architect import ArchitectAgent
from app.services.overmind.agents.auditor import AuditorAgent
from app.services.overmind.agents.operator import OperatorAgent
from app.services.overmind.agents.strategist import StrategistAgent
from app.services.overmind.domain.api_schemas import LangGraphRunData, LangGraphRunRequest
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.langgraph.engine import LangGraphOvermindEngine
from app.services.overmind.langgraph.state_manager import EphemeralMissionStateManager


class LangGraphAgentService:
    """
    خدمة تشغيل LangGraph للوكلاء المتعددين.

    تقوم هذه الخدمة بتجميع الوكلاء وإنشاء محرك LangGraph متسق مع
    مبادئ API First وبنية الخدمات المصغرة.
    """

    def __init__(self) -> None:
        ai_client = get_ai_client()
        registry = get_registry()
        state_manager = EphemeralMissionStateManager()
        executor = TaskExecutor(state_manager=state_manager, registry=registry)
        strategist = StrategistAgent(ai_client)
        architect = ArchitectAgent(ai_client)
        operator = OperatorAgent(executor, ai_client=ai_client)
        auditor = AuditorAgent(ai_client)
        self.engine = LangGraphOvermindEngine(
            strategist=strategist,
            architect=architect,
            operator=operator,
            auditor=auditor,
        )

    async def run(self, payload: LangGraphRunRequest) -> LangGraphRunData:
        """
        تشغيل LangGraph وإرجاع بيانات التشغيل.
        """
        run_id = str(uuid.uuid4())
        result = await self.engine.run(
            run_id=run_id,
            objective=payload.objective,
            context=payload.context,
            constraints=payload.constraints,
            priority=payload.priority.value,
        )
        state = result.state
        return LangGraphRunData(
            run_id=run_id,
            objective=payload.objective,
            plan=state.get("plan"),
            design=state.get("design"),
            execution=state.get("execution"),
            audit=state.get("audit"),
            timeline=state.get("timeline", []),
        )
