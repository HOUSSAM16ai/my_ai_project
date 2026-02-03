"""
Admin Agent (Refactored for SOLID).
-----------------------------------
Acts as a Facade/Coordinator. Delegates logic to AdminRouter (Strategy).
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.core.ai_gateway import AIClient
from app.services.chat.agents.admin_handlers.base import AdminCommandHandler
from app.services.chat.agents.admin_handlers.code import (
    CodeSearchHandler,
    FileSnippetHandler,
    RouteHandler,
    SymbolHandler,
)
from app.services.chat.agents.admin_handlers.database import (
    DatabaseMapHandler,
    DatabaseQueryHandler,
)
from app.services.chat.agents.admin_handlers.project import (
    MicroservicesHandler,
    ProjectInfoHandler,
)
from app.services.chat.agents.admin_handlers.users import (
    UserCountHandler,
    UserListHandler,
    UserProfileHandler,
    UserStatsHandler,
)
from app.services.chat.agents.data_access import DataAccessAgent
from app.services.chat.agents.refactor import RefactorAgent
from app.services.chat.tools import ToolRegistry
from app.services.mcp.integrations import MCPIntegrations
from app.services.chat.agents.admin_components.router import AdminRouter
from app.services.chat.agents.admin_components.responder import FormalResponder

logger = logging.getLogger(__name__)


class AdminAgent:
    """
    وكيل المهام الإدارية (Admin Agent).

    المسؤوليات (بعد إعادة الهيكلة SOLID):
    - Facade: واجهة موحدة للتعامل مع النظام.
    - DI Container: تجميع المكونات (في حالة الاستخدام القديم).
    - Delegation: تفويض التنفيذ للموجه (Router).
    """

    def __init__(
        self,
        tools: ToolRegistry,
        ai_client: AIClient | None = None,
        router: AdminRouter | None = None
    ) -> None:
        self.tools = tools
        self.ai_client = ai_client

        # Dependency Injection or Composition Root Fallback
        if router:
            self.router = router
        else:
            # Legacy/Default Construction
            self.data_agent = DataAccessAgent()
            self.refactor_agent = RefactorAgent()

            # MCP Integration
            mcp_instance = None
            try:
                mcp_instance = MCPIntegrations()
            except Exception as e:
                logger.warning(f"Failed to initialize MCP integrations: {e}")
                mcp_instance = None

            # Register Handlers
            handlers_list: list[AdminCommandHandler] = [
                UserCountHandler(tools, self.data_agent, self.refactor_agent),
                UserListHandler(tools, self.data_agent, self.refactor_agent),
                UserProfileHandler(tools, self.data_agent, self.refactor_agent),
                UserStatsHandler(tools, self.data_agent, self.refactor_agent),
                DatabaseMapHandler(tools, self.data_agent, self.refactor_agent),
                DatabaseQueryHandler(tools, self.data_agent, self.refactor_agent),
                MicroservicesHandler(tools, self.data_agent, self.refactor_agent),
                ProjectInfoHandler(tools, self.data_agent, self.refactor_agent),
                CodeSearchHandler(tools, self.data_agent, self.refactor_agent),
                FileSnippetHandler(tools, self.data_agent, self.refactor_agent),
                RouteHandler(tools, self.data_agent, self.refactor_agent),
                SymbolHandler(tools, self.data_agent, self.refactor_agent),
            ]

            # Create Components
            responder = FormalResponder(ai_client) if ai_client else None

            # NOTE: If ai_client is None, Router will have limited functionality.
            # We assume ai_client implements LLMClient protocol if passed.
            self.router = AdminRouter(ai_client, handlers_list, mcp_instance, responder) # type: ignore

    async def run(
        self,
        question: str,
        context: dict[str, object] | None = None,
    ) -> AsyncGenerator[str, None]:
        """معالجة الطلب الإداري وتوليد الاستجابة عبر الموجه."""
        try:
            async for chunk in self.router.route_and_execute(question, context):
                yield chunk
        except Exception as e:
            logger.error(f"AdminAgent failed: {e}", exc_info=True)
            yield f"حدث خطأ أثناء تنفيذ الأمر الإداري: {e}"

    # Expose handlers property for legacy tests that inspect it
    @property
    def handlers(self):
        return self.router.handlers

    @handlers.setter
    def handlers(self, value):
        self.router.handlers = value

    # Expose mcp property for legacy tests
    @property
    def mcp(self):
        return self.router.mcp

    @mcp.setter
    def mcp(self, value):
        self.router.mcp = value
