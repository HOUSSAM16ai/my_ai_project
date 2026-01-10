from collections.abc import Callable
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.clients.user_client import user_client
from app.services.codebase.introspection import introspection_service

logger = get_logger("tool-registry")

class ToolRegistry:
    """
    Registry for tools available to the agents.
    Enforces "no hallucinated tools".
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("get_user_count", self._get_user_count)
        self.register("search_codebase", self._search_codebase)
        self.register("find_symbol", self._find_symbol)

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    async def execute(self, tool_name: str, args: dict[str, Any]) -> Any:
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found.")

        logger.info(f"Executing tool: {tool_name} with {args}")
        return await self._tools[tool_name](**args)

    # --- Tool Implementations ---

    async def _get_user_count(self) -> int:
        return await user_client.get_user_count()

    async def _search_codebase(self, query: str) -> list[dict[str, Any]]:
        # Map to CodeSearchService
        results = introspection_service.search_text(query)
        return [r.model_dump() for r in results]

    async def _find_symbol(self, symbol: str) -> list[dict[str, Any]]:
        results = introspection_service.find_symbol(symbol)
        return [r.model_dump() for r in results]
