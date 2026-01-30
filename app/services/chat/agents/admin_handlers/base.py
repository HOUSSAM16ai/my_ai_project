from abc import ABC, abstractmethod
import re

from app.services.chat.agents.data_access import DataAccessAgent
from app.services.chat.agents.refactor import RefactorAgent
from app.services.chat.tools import ToolRegistry


class AdminCommandHandler(ABC):
    """Abstract base class for admin command handlers."""

    def __init__(
        self,
        tools: ToolRegistry,
        data_agent: DataAccessAgent,
        refactor_agent: RefactorAgent,
    ):
        self.tools = tools
        self.data_agent = data_agent
        self.refactor_agent = refactor_agent

    @abstractmethod
    async def can_handle(self, lowered: str) -> bool:
        """Check if this handler can handle the query."""

    @abstractmethod
    async def handle(self, question: str, lowered: str) -> str:
        """Execute the command."""

    # Common helpers
    def _extract_limit(self, s: str) -> int | None:
        m = re.search(r"(?:limit|أول)\s+(\d+)", s)
        return int(m.group(1)) if m else None

    def _extract_id(self, s: str) -> int | None:
        m = re.search(r"(\d+)", s)
        return int(m.group(1)) if m else None

    def _extract_quoted(self, s: str) -> str | None:
        m = re.search(r"['\"]([^'\"]+)['\"]", s)
        return m.group(1).strip() if m else None
