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
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.langgraph.context_enricher import ContextEnricher
from app.services.overmind.langgraph.engine import LangGraphOvermindEngine
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

    # Register Content tools dynamically to avoid circular dependency
    from app.services.chat.tools.content import register_content_tools
    from app.services.chat.tools.retrieval import search_educational_content

    register_content_tools(registry)
    registry["search_educational_content"] = search_educational_content

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
    operator = OperatorAgent(executor, ai_client=ai_client)
    auditor = AuditorAgent(ai_client)
    # memory_agent is initialized but not used in the new architecture, ensuring we don't trigger F841

    # 5. The SuperBrain (Legacy) & LangGraph Engine (New)
    # We now default to the LangGraph Engine for "Super Mission" capabilities
    context_enricher = ContextEnricher()

    # Initialize the LangGraph Engine
    langgraph_brain = LangGraphOvermindEngine(
        strategist=strategist,
        architect=architect,
        operator=operator,
        auditor=auditor,
        context_enricher=context_enricher,
    )

    # 6. The Orchestrator
    # Passing the LangGraph Engine as the primary brain
    return OvermindOrchestrator(
        state_manager=state_manager, executor=executor, brain=langgraph_brain
    )
