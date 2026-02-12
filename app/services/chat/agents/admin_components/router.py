"""
موجّه النوايا الإداري (OCP/SRP).
--------------------------------
يتولى تصنيف النوايا وتوجيهها إلى المعالجات المناسبة.
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Protocol

from app.core.interfaces.llm import LLMClient
from app.core.interfaces.router import IntentRouter
from app.services.chat.agents.admin_components.responder import FormalResponder
from app.services.chat.agents.admin_handlers.base import AdminCommandHandler
from app.services.chat.agents.admin_handlers.project import MicroservicesHandler, ProjectInfoHandler
from app.services.chat.agents.admin_handlers.users import UserCountHandler, UserListHandler
from app.services.chat.agents.base import FORMAL_ARABIC_STYLE_PROMPT

logger = logging.getLogger(__name__)


class MCPService(Protocol):
    """Protocol for MCP Integrations to avoid hard dependency here."""

    async def semantic_search(self, query: str, top_k: int = 5) -> dict[str, object]: ...

    async def run_langgraph_workflow(self, goal: str) -> dict[str, object]: ...


class AdminRouter(IntentRouter):
    """
    Routes user questions to the correct handler or MCP service.
    """

    def __init__(
        self,
        ai_client: LLMClient,
        handlers: list[AdminCommandHandler],
        mcp: MCPService | None,
        responder: FormalResponder,
    ):
        self.ai_client = ai_client
        self.handlers = handlers
        self.mcp = mcp
        self.responder = responder

    async def route_and_execute(
        self, question: str, context: dict[str, object] | None = None
    ) -> AsyncGenerator[str, None]:
        lowered = question.lower().strip()

        # 1. Fast Path (Regex/Keyword Strategy)
        for h in self.handlers:
            if await h.can_handle(lowered):
                yield await h.handle(question, lowered)
                return

        # 2. LLM Classification Strategy
        if not self.ai_client:
            yield "عذرًا، خدمة الذكاء الاصطناعي غير متاحة للتوجيه الذكي."
            return

        intent = await self._classify_intent(question)
        tool_name = intent.get("tool", "GENERAL_ANSWER")
        reason = intent.get("reason", "")

        logger.info(f"Admin Router Decision: {tool_name} ({reason})")

        # 3. Dispatch
        if tool_name == "GENERAL_ANSWER":
            if reason:
                yield f"التحليل: {reason}\n"
            async for chunk in self.responder.generate(question):
                yield chunk
            return

        # Map tools to handlers
        handler_map = {
            "LIST_USERS": UserListHandler,
            "COUNT_USERS": UserCountHandler,
            "PROJECT_INFO": ProjectInfoHandler,
            "MICROSERVICES_INFO": MicroservicesHandler,
        }

        if tool_name in handler_map:
            handler_type = handler_map[tool_name]
            handler = next((h for h in self.handlers if isinstance(h, handler_type)), None)
            if handler:
                yield await handler.handle(question, lowered)
                return
            else:
                yield f"خطأ: الأداة {tool_name} غير متاحة."
                return

        # MCP Tools
        if tool_name == "DEEP_RESEARCH":
            async for chunk in self._handle_deep_research(question):
                yield chunk
            return

        if tool_name == "COMPLEX_REASONING":
            async for chunk in self._handle_complex_reasoning(question):
                yield chunk
            return

        # Unknown tool
        yield f"عذراً، الأداة المطلوبة '{tool_name}' غير مدعومة."

    async def _classify_intent(self, question: str) -> dict[str, object]:
        """Uses LLM to classify the intent."""
        system_prompt = """
        أنت وكيل إداري ذكي (Admin Agent). مهمتك هي مساعدة مسؤول النظام في فهم حالة النظام.

        يجب عليك تحليل طلب المستخدم وتحديد الأداة المناسبة للتنفيذ.
        الرد يجب أن يكون **فقط** بصيغة JSON وبدون أي نص إضافي، كالتالي:

        {
            "tool": "TOOL_NAME",
            "reason": "Why you chose this tool"
        }

        الأدوات المتاحة (Tools):
        - "LIST_USERS": عرض قائمة المستخدمين (users list, show users).
        - "COUNT_USERS": معرفة عدد المستخدمين (how many users).
        - "PROJECT_INFO": معلومات عن هيكل المشروع والملفات (structure, architecture).
        - "MICROSERVICES_INFO": معلومات عن الخدمات المصغرة (microservices).
        - "DEEP_RESEARCH": بحث عميق في المعرفة والمستندات (للمواضيع الأكاديمية أو البحثية).
        - "COMPLEX_REASONING": تفكير منطقي معقد وحل مشكلات (للتحليل أو التخطيط).
        - "GENERAL_ANSWER": للإجابة العامة التي لا تتطلب أدوات.

        تحذير: لا تضف أي نص خارج كائن JSON.
        """

        # Use simple send_message if available on client protocol
        full_response = await self.ai_client.send_message(system_prompt, question)

        clean_json = full_response.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            logger.warning("Admin Router Invalid JSON. Returning General Answer.")
            return {"tool": "GENERAL_ANSWER", "reason": "Failed to parse intent"}

    async def _handle_deep_research(self, question: str) -> AsyncGenerator[str, None]:
        if self.mcp:
            yield "جاري تنفيذ البحث العميق عبر MCP..."
            result = await self.mcp.semantic_search(query=question, top_k=5)
            if result.get("success"):
                yield "\n\n### نتائج البحث العميق:\n"
                for node in result.get("results", []):
                    text = node.text if hasattr(node, "text") else str(node)
                    yield f"- {text[:300]}...\n"
            else:
                yield f"حدث خطأ في البحث: {result.get('error')}"
        else:
            yield "عذراً، خدمة البحث العميق (MCP) غير متاحة حالياً."

    async def _handle_complex_reasoning(self, question: str) -> AsyncGenerator[str, None]:
        if self.mcp:
            yield "جاري تنفيذ التفكير المعقد عبر MCP (LangGraph)..."
            goal_with_style = f"{question}\n\n{FORMAL_ARABIC_STYLE_PROMPT}"
            result = await self.mcp.run_langgraph_workflow(goal=goal_with_style)
            if result.get("success"):
                yield f"\n\n### النتيجة النهائية:\n{result.get('final_answer')}"
            else:
                yield f"حدث خطأ في المعالجة: {result.get('error')}"
        else:
            yield "عذراً، خدمة التفكير المعقد (MCP) غير متاحة حالياً."
