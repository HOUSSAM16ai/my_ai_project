import json
import logging
from collections.abc import AsyncGenerator

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

logger = logging.getLogger(__name__)


class AdminAgent:
    """
    وكيل المهام الإدارية (Admin Agent).

    المسؤوليات:
    - التعامل مع استفسارات إدارة المستخدمين (Count, List, Profile).
    - استعلامات قاعدة البيانات (Schema, Stats).
    - استكشاف بنية المشروع والشيفرة.
    - تنفيذ مهام بحث واستنتاج عميق عبر MCP.
    """

    def __init__(self, tools: ToolRegistry, ai_client: AIClient | None = None) -> None:
        self.tools = tools
        self.ai_client = ai_client
        self.data_agent = DataAccessAgent()
        self.refactor_agent = RefactorAgent()

        # MCP Integration for advanced capabilities
        try:
            self.mcp = MCPIntegrations()
        except Exception as e:
            logger.warning(f"Failed to initialize MCP integrations: {e}")
            self.mcp = None

        # Register Handlers (Order matters for priority)
        self.handlers: list[AdminCommandHandler] = [
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

    async def run(
        self,
        question: str,
        context: dict[str, object] | None = None,
    ) -> AsyncGenerator[str, None]:
        """معالجة الطلب الإداري وتوليد الاستجابة."""
        lowered = question.lower().strip()

        try:
            # 1. Strategy Pattern Match (Fast Path)
            handler = None
            for h in self.handlers:
                if await h.can_handle(lowered):
                    handler = h
                    break

            if handler:
                result = await handler.handle(question, lowered)
                yield result

            # 2. Dynamic Router (LLM Fallback)
            elif self.ai_client:
                async for chunk in self._handle_dynamic_router(question, context):
                    yield chunk

            # 3. Fallback
            else:
                yield "عذرًا، لم أتمكن من تحديد نوع الطلب الإداري بدقة. يرجى التوضيح (مثال: 'عدد المستخدمين'، 'هيكل المشروع')."

        except Exception as e:
            logger.error(f"AdminAgent failed: {e}", exc_info=True)
            yield f"حدث خطأ أثناء تنفيذ الأمر الإداري: {e}"

    async def _handle_dynamic_router(
        self, question: str, context: dict | None
    ) -> AsyncGenerator[str, None]:
        """استخدام الذكاء الاصطناعي لفهم الطلبات الإدارية المعقدة وتوجيهها للأدوات."""

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        full_response = ""
        # Accumulate response
        if self.ai_client:
            async for chunk in self.ai_client.stream_chat(messages):
                content = ""
                if hasattr(chunk, "choices"):
                    delta = chunk.choices[0].delta if chunk.choices else None
                    content = delta.content if delta else ""
                else:
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                full_response += content

        # Clean JSON (remove markdown blocks if present)
        clean_json = full_response.replace("```json", "").replace("```", "").strip()

        try:
            decision = json.loads(clean_json)
            tool_name = decision.get("tool", "GENERAL_ANSWER")
            reason = decision.get("reason", "")
            logger.info(f"Admin Dynamic Router: {tool_name} ({reason})")

            if tool_name == "LIST_USERS":
                h = next((x for x in self.handlers if isinstance(x, UserListHandler)), None)
                if h:
                    yield await h.handle(question, question.lower())
                else:
                    yield "خطأ: تعذر الوصول لخدمة المستخدمين."

            elif tool_name == "COUNT_USERS":
                h = next((x for x in self.handlers if isinstance(x, UserCountHandler)), None)
                if h:
                    yield await h.handle(question, question.lower())

            elif tool_name == "PROJECT_INFO":
                h = next((x for x in self.handlers if isinstance(x, ProjectInfoHandler)), None)
                if h:
                    yield await h.handle(question, question.lower())

            elif tool_name == "MICROSERVICES_INFO":
                h = next((x for x in self.handlers if isinstance(x, MicroservicesHandler)), None)
                if h:
                    yield await h.handle(question, question.lower())

            elif tool_name == "DEEP_RESEARCH":
                if self.mcp:
                    yield "جاري تنفيذ البحث العميق عبر MCP..."
                    result = await self.mcp.semantic_search(query=question, top_k=5)
                    if result.get("success"):
                        yield "\n\n### نتائج البحث العميق:\n"
                        for node in result.get("results", []):
                            yield f"- {node.text[:300]}...\n"
                    else:
                        yield f"حدث خطأ في البحث: {result.get('error')}"
                else:
                    yield "عذراً، خدمة البحث العميق (MCP) غير متاحة حالياً."

            elif tool_name == "COMPLEX_REASONING":
                if self.mcp:
                    yield "جاري تنفيذ التفكير المعقد عبر MCP (LangGraph)..."
                    result = await self.mcp.run_langgraph_workflow(goal=question)
                    if result.get("success"):
                        yield f"\n\n### النتيجة النهائية:\n{result.get('final_answer')}"
                    else:
                        yield f"حدث خطأ في المعالجة: {result.get('error')}"
                else:
                    yield "عذراً، خدمة التفكير المعقد (MCP) غير متاحة حالياً."

            else:
                # Fallback to General Answer (which ideally would be the reasoning in the JSON, but here we might need to re-ask or just return the reason)
                # Since the model only outputted JSON, we don't have a conversational answer.
                # We should probably ask it to answer now.
                yield f"التحليل: {reason}\n(لم يتم تحديد أداة خاصة لهذا الطلب، يرجى التوضيح)."

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from Admin Router: {full_response}")
            # Fallback: Just yield the raw text if it wasn't JSON
            yield full_response
