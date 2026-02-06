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
from app.services.kagent.interface import KagentMesh
from app.services.mcp.server import get_mcp_server
from app.services.overmind.executor import TaskExecutor
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

    # --- MCP & Kagent Integration ---
    mcp = get_mcp_server()
    await mcp.initialize()
    # Ensure Kagent is initialized
    _ = KagentMesh()

    # Register MCP tools into the registry
    for tool_name, tool in mcp.tool_registry.tools.items():
        if tool_name not in registry:
            # Register the raw handler to be awaited by executor
            registry[tool_name] = tool.handler

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

    # 5. The SuperBrain (Replaced by LangGraph Engine)
    engine = LangGraphOvermindEngine(
        strategist=strategist,
        architect=architect,
        operator=operator,
        auditor=auditor,
    )

    # 6. The Orchestrator
    # Refactoring: Using keyword arguments for Static Connascence
    return OvermindOrchestrator(state_manager=state_manager, executor=executor, brain=engine)
