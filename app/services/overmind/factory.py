"""
مصنع العقل المدبر (Overmind Factory).

يقوم هذا المصنع بتجميع الوكيل الخارق (Super Agent) وحقن كافة التبعيات اللازمة.
يضمن هذا الملف تطبيق مبدأ انقلاب التبعية (Dependency Inversion).

المعايير:
- CS50 2025: توثيق عربي، صرامة في النوع.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_gateway import get_ai_client

# استيراد الأدوات (يجب ضمان وجود هذا المسار أو استخدام واجهة بديلة)
from app.services.agent_tools import get_registry
from app.services.overmind.agents.architect import ArchitectAgent
from app.services.overmind.agents.auditor import AuditorAgent
from app.services.overmind.agents.memory import MemoryAgent
from app.services.overmind.agents.operator import OperatorAgent
from app.services.overmind.agents.strategist import StrategistAgent
from app.services.overmind.collaboration import CollaborationHub
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.state import MissionStateManager

__all__ = ["create_overmind"]


async def create_overmind(db: AsyncSession) -> OvermindOrchestrator:
    """
    دالة المصنع لتجميع العقل المدبر مع مجلس الحكمة.

    Args:
        db (AsyncSession): جلسة قاعدة البيانات.

    Returns:
        OvermindOrchestrator: مثيل جاهز للعمل.
    """
    # 1. State Layer
    state_manager = MissionStateManager(db)

    # 2. Execution Layer
    registry = get_registry()
    # تم تحديث TaskExecutor ليقبل السجل صراحةً (Dependency Injection)
    # Refactoring: Using keyword arguments for Static Connascence
    executor = TaskExecutor(state_manager=state_manager, registry=registry)

    # 3. AI Gateway (Energy Engine)
    ai_client = get_ai_client()

    # 4. The Council of Wisdom (الوكلاء المتخصصون)
    # Assuming agents are still positional or simple enough, but best practice:
    # We will verify their signatures if needed, but for now we focus on the core chain.
    strategist = StrategistAgent(ai_client)
    architect = ArchitectAgent(ai_client)
    operator = OperatorAgent(executor)
    auditor = AuditorAgent(ai_client)
    memory_agent = MemoryAgent()

    # 5. The SuperBrain (Cognitive Domain)
    # Refactoring: Using keyword arguments for Static Connascence
    collaboration_hub = CollaborationHub()
    brain = SuperBrain(
        strategist=strategist,
        architect=architect,
        operator=operator,
        auditor=auditor,
        collaboration_hub=collaboration_hub,
        memory_agent=memory_agent,
    )

    # 6. The Orchestrator
    # Refactoring: Using keyword arguments for Static Connascence
    return OvermindOrchestrator(state_manager=state_manager, executor=executor, brain=brain)
