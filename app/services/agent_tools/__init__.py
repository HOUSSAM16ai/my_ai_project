"""
Agent Tools Module.
"""
from app.services.agent_tools.new_core import tool
from app.services.agent_tools.infrastructure.registry import get_registry

# Import domain tools to ensure registration
from app.services.agent_tools.domain import fs

__all__ = ["tool", "get_registry"]
