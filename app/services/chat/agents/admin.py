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

        لديك الأدوات التالية (Tools) التي يمكنك استدعاؤها أو الاستدلال بنتائجها:
        1. LIST_USERS: عرض قائمة المستخدمين.
        2. COUNT_USERS: معرفة عدد المستخدمين.
        3. DB_SCHEMA: عرض مخطط جداول قاعدة البيانات.
        4. PROJECT_INFO: معلومات عن هيكل المشروع والملفات.
        5. MICROSERVICES_INFO: معلومات عن الخدمات المصغرة.
        6. CODE_SEARCH: البحث في الكود المصدري.
        7. DEEP_RESEARCH: بحث عميق في المعرفة والمستندات (استخدمه للأسئلة الأكاديمية أو البحثية المعقدة).
        8. COMPLEX_REASONING: تفكير منطقي معقد وحل مشكلات (استخدمه للتحليل العميق أو التخطيط).

        إذا كان السؤال غامضًا، حاول ربطه بأقرب أداة.
        إذا كان السؤال عن "الخدمات المصغرة" (microservices) استخدم MICROSERVICES_INFO.
        إذا كان السؤال عن "البنية" أو "هيكل المشروع"، استخدم PROJECT_INFO.
        إذا كان السؤال عن "أسماء المستخدمين" أو "الأعضاء"، استخدم LIST_USERS.
        إذا كان السؤال يتطلب بحثاً في مراجع أو تحليل موضوع معقد: استخدم DEEP_RESEARCH.
        إذا كان السؤال يتطلب خطة عمل أو تحليل منطقي متعدد الخطوات: استخدم COMPLEX_REASONING.

        يجب أن يكون ردك النهائي هو الإجابة الدقيقة بناءً على الأداة المناسبة.
        إذا كنت بحاجة لتنفيذ أداة، قم بذكر اسم الأداة بوضوح في سياق تفكيرك، وسأقوم أنا بتنفيذها لك (محاكاة).

        للحفاظ على البساطة في هذه المرحلة، إذا طابق السؤال إحدى الحالات التالية، أجب بنمط محدد:
        - إذا طلب قائمة مستخدمين: قل "EXECUTE_TOOL: list_users"
        - إذا طلب عدد مستخدمين: قل "EXECUTE_TOOL: get_user_count"
        - إذا طلب معلومات المشروع: قل "EXECUTE_TOOL: get_project_overview"
        - إذا طلب معلومات الخدمات المصغرة: قل "EXECUTE_TOOL: get_microservices_overview"
        - إذا تطلب بحثاً عميقاً: قل "EXECUTE_TOOL: deep_research"
        - إذا تطلب تفكيراً معقداً: قل "EXECUTE_TOOL: complex_reasoning"
        - غير ذلك: أجب كخبير نظام بناءً على معرفتك العامة بالسياق المرفق.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        full_response = ""
        # Note: We assume ai_client is available
        if self.ai_client:
            async for chunk in self.ai_client.stream_chat(messages):
                content = ""
                if hasattr(chunk, "choices"):
                    delta = chunk.choices[0].delta if chunk.choices else None
                    content = delta.content if delta else ""
                else:
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                full_response += content

        # Check for command
        # We recursively call run but we need to match the handler manually to avoid infinite loop
        # or just invoke the handler directly.

        if "EXECUTE_TOOL: list_users" in full_response:
            # Find UserListHandler
            h = next((x for x in self.handlers if isinstance(x, UserListHandler)), None)
            if h:
                yield await h.handle(question, question.lower())
            else:
                yield "Error: Handler not found."

        elif "EXECUTE_TOOL: get_user_count" in full_response:
            h = next((x for x in self.handlers if isinstance(x, UserCountHandler)), None)
            if h:
                yield await h.handle(question, question.lower())

        elif "EXECUTE_TOOL: get_project_overview" in full_response:
            h = next((x for x in self.handlers if isinstance(x, ProjectInfoHandler)), None)
            if h:
                yield await h.handle(question, question.lower())

        elif "EXECUTE_TOOL: get_microservices_overview" in full_response:
            h = next((x for x in self.handlers if isinstance(x, MicroservicesHandler)), None)
            if h:
                yield await h.handle(question, question.lower())

        elif "EXECUTE_TOOL: deep_research" in full_response and self.mcp:
            yield "جاري تنفيذ البحث العميق عبر MCP..."
            # Use MCP for semantic search
            result = await self.mcp.semantic_search(query=question, top_k=5)
            if result.get("success"):
                yield "\n\nنتائج البحث العميق:\n"
                for node in result.get("results", []):
                     yield f"- {node.text[:200]}...\n"
            else:
                yield f"حدث خطأ في البحث: {result.get('error')}"

        elif "EXECUTE_TOOL: complex_reasoning" in full_response and self.mcp:
            yield "جاري تنفيذ التفكير المعقد عبر MCP (LangGraph)..."
            # Use MCP to run LangGraph workflow
            result = await self.mcp.run_langgraph_workflow(goal=question)
            if result.get("success"):
                yield f"\n\nالنتيجة النهائية:\n{result.get('final_answer')}"
            else:
                yield f"حدث خطأ في المعالجة: {result.get('error')}"

        else:
            yield full_response
