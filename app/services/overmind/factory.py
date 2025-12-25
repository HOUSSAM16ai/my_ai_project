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
from app.services.overmind.agents.operator import OperatorAgent
from app.services.overmind.agents.strategist import StrategistAgent
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
    # ملاحظة: TaskExecutor يحتاج إلى registry لتنفيذ الأدوات
    # سنفترض هنا أنه يقبله، أو سيتم تحديثه لاحقاً
    executor = TaskExecutor(state_manager)

    # 3. AI Gateway (Energy Engine)
    ai_client = get_ai_client()

    # 4. The Council of Wisdom (الوكلاء المتخصصون)
    strategist = StrategistAgent(ai_client)
    architect = ArchitectAgent(ai_client)
    operator = OperatorAgent(executor)
    auditor = AuditorAgent(ai_client)

    # 5. The SuperBrain (Cognitive Domain)
    brain = SuperBrain(
        strategist=strategist,
        architect=architect,
        operator=operator,
        auditor=auditor
    )

    # 6. The Orchestrator
    return OvermindOrchestrator(
        state_manager=state_manager,
        executor=executor,
        brain=brain
    )
