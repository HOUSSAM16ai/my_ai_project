"""
Agent Tools Module.
"""
# Import domain tools to ensure registration
from app.services.agent_tools.domain import fs
from app.services.agent_tools.infrastructure.registry import get_registry
from app.services.agent_tools.new_core import tool

__all__ = ["tool", "get_registry"]
