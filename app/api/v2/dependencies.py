"""
FastAPI dependencies for dependency injection.
"""
from typing import Any as AIClient

from app.services.agent_tools.registry import ToolRegistry, get_tool_registry
from app.services.chat.orchestrator import ChatOrchestrator


def get_ai_client():
    """Get AI client (placeholder)."""
    return


async def get_current_user_id() -> int:
    """Get current authenticated user ID."""
    return 1


async def get_chat_orchestrator() -> ChatOrchestrator:
    """Get chat orchestrator instance."""
    return ChatOrchestrator()


async def get_ai_client_dependency() -> AIClient:
    """Get AI client instance."""
    return get_ai_client()


async def get_tool_registry_dependency() -> ToolRegistry:
    """Get tool registry instance."""
    return get_tool_registry()
