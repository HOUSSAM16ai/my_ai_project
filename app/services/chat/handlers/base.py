from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.core.resilience import CircuitBreaker

logger = logging.getLogger(__name__)


class AsyncToolsProtocol(Protocol):
    @property
    def available(self) -> bool: ...
    async def read_file(self, path: str, max_bytes: int = 50000) -> dict: ...
    async def write_file(self, path: str, content: str) -> dict: ...
    async def code_search_lexical(
        self, query: str, limit: int = 10, context_radius: int = 3
    ) -> dict: ...
    async def code_index_project(self, root: str, max_files: int = 500) -> dict: ...


class AsyncOvermindProtocol(Protocol):
    @property
    def available(self) -> bool: ...
    async def start_mission(self, objective: str, user_id: int) -> dict: ...
    async def get_mission_status(self, mission_id: int) -> dict: ...


class RateLimiterProtocol(Protocol):
    def check(self, user_id: int, key: str) -> tuple[bool, str]: ...


class ChatContext:
    """Context object holding dependencies for chat handlers."""

    def __init__(
        self,
        async_tools: AsyncToolsProtocol | None = None,
        async_overmind: AsyncOvermindProtocol | None = None,
        rate_limiter: RateLimiterProtocol | None = None,
    ):
        self.async_tools = async_tools
        self.async_overmind = async_overmind
        self.rate_limiter = rate_limiter

    async def check_rate_limit(self, user_id: int, tool_name: str) -> tuple[bool, str]:
        if not self.rate_limiter:
            return True, "ok"
        return self.rate_limiter.check(user_id, tool_name)
