"""
Overmind Factory.
Constructs the Super Agent with all dependencies injected.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.state import MissionStateManager
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.agents.strategist import StrategistAgent
from app.services.overmind.agents.architect import ArchitectAgent
from app.services.overmind.agents.operator import OperatorAgent
from app.services.overmind.agents.auditor import AuditorAgent
from app.core.ai_gateway import get_ai_client
# Assuming tool registry is available or we use a placeholder
from app.services.agent_tools import get_registry

def create_overmind(db: AsyncSession) -> OvermindOrchestrator:
    """
    Factory to assemble the Overmind with the Council of Wisdom.
    """
    state_manager = MissionStateManager(db)

    # Tools & Executors
    registry = get_registry()
    # Note: TaskExecutor might need updates to accept registry if not already
    executor = TaskExecutor(state_manager)

    # AI Client
    ai_client = get_ai_client()

    # The Council
    strategist = StrategistAgent(ai_client)
    architect = ArchitectAgent(ai_client)
    operator = OperatorAgent(executor)
    auditor = AuditorAgent(ai_client)

    # The Brain
    brain = SuperBrain(strategist, architect, operator, auditor)

    # The Orchestrator
    return OvermindOrchestrator(state_manager, executor, brain)
