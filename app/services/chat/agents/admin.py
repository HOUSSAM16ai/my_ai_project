import logging
import re
from collections.abc import AsyncGenerator

from app.core.ai_gateway import AIClient
from app.services.chat.agents.data_access import DataAccessAgent
from app.services.chat.agents.refactor import RefactorAgent
from app.services.chat.tools import ToolRegistry

logger = logging.getLogger(__name__)


class AdminAgent:
    """
    وكيل المهام الإدارية (Admin Agent).

    المسؤوليات:
    - التعامل مع استفسارات إدارة المستخدمين (Count, List, Profile).
    - استعلامات قاعدة البيانات (Schema, Stats).
    - استكشاف بنية المشروع والشيفرة.
    """

    def __init__(self, tools: ToolRegistry, ai_client: AIClient | None = None) -> None:
        self.tools = tools
        self.ai_client = ai_client
        self.data_agent = DataAccessAgent()
        self.refactor_agent = RefactorAgent()

    async def run(
        self,
        question: str,
        context: dict[str, object] | None = None,
    ) -> AsyncGenerator[str, None]:
        """معالجة الطلب الإداري وتوليد الاستجابة."""
        lowered = question.lower().strip()
        handler = self._resolve_handler(lowered)

        try:
            # 1. Direct Regex Match (Fast Path)
            if handler != self._handle_unknown_admin_query:
                result = await handler(question, lowered)
                yield result
            # 2. Dynamic Router (LLM Fallback)
            # If we have AI Client, ask it to route or execute tools
            elif self.ai_client:
                async for chunk in self._handle_dynamic_router(question, context):
                    yield chunk
            else:
                yield await self._handle_unknown_admin_query(question, lowered)

        except Exception as e:
            logger.error(f"AdminAgent failed: {e}", exc_info=True)
            yield f"حدث خطأ أثناء تنفيذ الأمر الإداري: {e}"

    def _resolve_handler(self, lowered: str):
        """توجيه الطلب للمعالج الداخلي المناسب."""
        if self._is_user_count_query(lowered):
            return self._handle_user_count
        if self._is_user_list_query(lowered):
            return self._handle_user_list
        if self._is_user_profile_query(lowered):
            return self._handle_user_profile
        if self._is_user_stats_query(lowered):
            return self._handle_user_statistics
        if self._is_database_map_query(lowered):
            return self._handle_database_map
        if self._is_database_query(lowered):
            return self._handle_database_query
        if self._is_microservices_query(lowered):
            return self._handle_microservices_query
        if self._is_project_query(lowered):
            return self._handle_project_query
        if self._is_route_query(lowered):
            return self._handle_route_query
        if self._is_symbol_query(lowered):
            return self._handle_symbol_query
        if self._is_code_search_query(lowered):
            return self._handle_code_search
        if self._is_file_snippet_query(lowered):
            return self._handle_file_snippet

        return self._handle_unknown_admin_query

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

        إذا كان السؤال غامضًا، حاول ربطه بأقرب أداة.
        إذا كان السؤال عن "الخدمات المصغرة" (microservices) استخدم MICROSERVICES_INFO.
        إذا كان السؤال عن "البنية" أو "هيكل المشروع"، استخدم PROJECT_INFO.
        إذا كان السؤال عن "أسماء المستخدمين" أو "الأعضاء"، استخدم LIST_USERS.

        يجب أن يكون ردك النهائي هو الإجابة الدقيقة بناءً على الأداة المناسبة.
        إذا كنت بحاجة لتنفيذ أداة، قم بذكر اسم الأداة بوضوح في سياق تفكيرك، وسأقوم أنا بتنفيذها لك (محاكاة).

        للحفاظ على البساطة في هذه المرحلة، إذا طابق السؤال إحدى الحالات التالية، أجب بنمط محدد:
        - إذا طلب قائمة مستخدمين: قل "EXECUTE_TOOL: list_users"
        - إذا طلب عدد مستخدمين: قل "EXECUTE_TOOL: get_user_count"
        - إذا طلب معلومات المشروع: قل "EXECUTE_TOOL: get_project_overview"
        - إذا طلب معلومات الخدمات المصغرة: قل "EXECUTE_TOOL: get_microservices_overview"
        - غير ذلك: أجب كخبير نظام بناءً على معرفتك العامة بالسياق المرفق.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        # Use AI to decide
        # Note: We are using stream_chat, so we need to buffer the response to check for commands
        full_response = ""
        async for chunk in self.ai_client.stream_chat(messages):
            # Extract content from chunk structure
            content = ""
            if hasattr(chunk, "choices"):
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            else:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

            full_response += content

        # Check for command
        if "EXECUTE_TOOL: list_users" in full_response:
            yield await self._handle_user_list(question, question.lower())
        elif "EXECUTE_TOOL: get_user_count" in full_response:
            yield await self._handle_user_count(question, question.lower())
        elif "EXECUTE_TOOL: get_project_overview" in full_response:
            yield await self._handle_project_query(question, question.lower())
        elif "EXECUTE_TOOL: get_microservices_overview" in full_response:
            yield await self._handle_microservices_query(question, question.lower())
        else:
            # Yield the LLM explanation directly
            yield full_response

    # --- Matchers ---

    def _is_user_count_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "how many users",
                "count users",
                "عدد المستخدمين",
                "كم مستخدم",
                "عدد الحسابات",
            ]
        )

    def _is_user_list_query(self, lowered: str) -> bool:
        return any(
            x in lowered for x in ["list users", "all users", "قائمة المستخدمين", "عرض المستخدمين"]
        )

    def _is_user_profile_query(self, lowered: str) -> bool:
        return any(x in lowered for x in ["user profile", "تفاصيل المستخدم", "معلومات المستخدم"])

    def _is_user_stats_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in ["user stats", "user statistics", "إحصائيات المستخدم", "دردشات المستخدم"]
        )

    def _is_database_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in ["database", "schema", "tables", "قاعدة البيانات", "الجداول", "مخطط"]
        )

    def _is_database_map_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "database map",
                "relationships",
                "foreign keys",
                "خريطة قاعدة البيانات",
                "العلاقات",
            ]
        )

    def _is_project_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "project",
                "structure",
                "architecture",
                "المشروع",
                "بنية المشروع",
                "هيكل المشروع",
            ]
        )

    def _is_microservices_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "microservices",
                "microservice",
                "الخدمات المصغرة",
                "خدمات مصغرة",
                "عدد الخدمات",
                "خدمة مصغرة",
            ]
        )

    def _is_file_snippet_query(self, lowered: str) -> bool:
        return ".py" in lowered and ("line" in lowered or "سطر" in lowered or ":" in lowered)

    def _is_route_query(self, lowered: str) -> bool:
        return any(x in lowered for x in ["route", "endpoint", "api path", "مسار", "نقطة نهاية"])

    def _is_symbol_query(self, lowered: str) -> bool:
        return any(x in lowered for x in ["function", "class", "دالة", "كلاس", "class "])

    def _is_code_search_query(self, lowered: str) -> bool:
        return any(
            x in lowered
            for x in [
                "find",
                "locate",
                "search",
                "where",
                "file",
                "line",
                "أي ملف",
                "أين",
                "سطر",
                "ابحث",
            ]
        )

    # --- Handlers ---

    async def _handle_unknown_admin_query(self, question: str, lowered: str) -> str:
        return "عذرًا، لم أتمكن من تحديد نوع الطلب الإداري بدقة. يرجى التوضيح (مثال: 'عدد المستخدمين'، 'هيكل المشروع')."

    async def _handle_user_count(self, _: str, lowered: str) -> str:
        gov = await self.data_agent.process(
            {"entity": "user", "operation": "count", "access_method": "service_api"}
        )
        if not gov.success:
            return f"Governance Error: {gov.message}"

        count = await self.tools.execute("get_user_count", {})
        if count == 0:
            return "لا يوجد مستخدمون مسجلون حالياً. (0 users)"
        return f"عدد المستخدمين الحاليين: {count}. ({count} users)"

    async def _handle_user_list(self, question: str, lowered: str) -> str:
        gov = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "list",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"

        limit = self._extract_limit(lowered) or 20
        users = await self.tools.execute("list_users", {"limit": limit, "offset": 0})
        if not users:
            return "لا يوجد مستخدمون."

        lines = []
        for user in users:
            lines.append(
                f"- #{user['id']} | {user['full_name']} | {user['email']} | {user['status']}"
            )
        return "قائمة المستخدمين:\n" + "\n".join(lines)

    async def _handle_user_profile(self, question: str, lowered: str) -> str:
        user_id = self._extract_id(question)
        if not user_id:
            return "يرجى تزويدي بمعرّف المستخدم (ID)."

        gov = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "profile",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"

        profile = await self.tools.execute("get_user_profile", {"user_id": user_id})
        if profile.get("error"):
            return f"تعذر العثور على المستخدم #{user_id}."

        basic = profile.get("basic", {})
        stats = profile.get("statistics", {})
        return (
            f"ملف المستخدم #{user_id}:\n"
            f"- الاسم: {basic.get('full_name')}\n"
            f"- البريد: {basic.get('email')}\n"
            f"- الحالة: {basic.get('status')}\n"
            f"- الرسائل: {stats.get('total_chat_messages')}\n"
            f"- آخر نشاط: {stats.get('last_activity')}"
        )

    async def _handle_user_statistics(self, question: str, lowered: str) -> str:
        user_id = self._extract_id(question)
        if not user_id:
            return "يرجى تحديد رقم المستخدم."

        gov = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "statistics",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"

        stats = await self.tools.execute("get_user_statistics", {"user_id": user_id})
        if not stats:
            return f"لا توجد إحصائيات للمستخدم #{user_id}."

        return (
            f"إحصائيات #{user_id}:\n"
            f"- المهام: {stats.get('total_missions')} (مكتملة: {stats.get('completed_missions')})\n"
            f"- الرسائل: {stats.get('total_chat_messages')}"
        )

    async def _handle_database_query(self, question: str, lowered: str) -> str:
        table_name = self._extract_table_name(lowered)
        if table_name:
            if "count" in lowered or "عدد" in lowered:
                c = await self.tools.execute("get_table_count", {"table_name": table_name})
                return f"عدد السجلات في '{table_name}': {c}."

            schema = await self.tools.execute("get_table_schema", {"table_name": table_name})
            if not schema:
                return f"لا يوجد مخطط لجدول '{table_name}'."
            cols = "\n".join(
                f"- {col['name']} ({col['type']})" for col in schema.get("columns", [])
            )
            return f"مخطط '{table_name}':\n{cols}"

        tables = await self.tools.execute("get_database_tables", {})
        return "جداول قاعدة البيانات:\n" + "\n".join(f"- {t}" for t in tables[:50])

    async def _handle_database_map(self, _: str, __: str) -> str:
        m = await self.tools.execute("get_database_map", {})
        tables = [str(name) for name in m.get("tables", [])]
        relationships = m.get("relationships", [])
        lines = [
            "خريطة قاعدة البيانات:",
            f"- الجداول: {len(tables)}",
            f"- العلاقات: {len(relationships)}",
        ]
        if tables:
            lines.append("أسماء الجداول:")
            lines.extend(f"- {table}" for table in tables)
        return "\n".join(lines)

    async def _handle_project_query(self, _: str, __: str) -> str:
        k = await self.tools.execute("get_project_overview", {})
        return f"المشروع: {k.get('project_name')} (v{k.get('version')})\nملفات Python: {k.get('structure', {}).get('python_files')}"

    async def _handle_microservices_query(self, question: str, lowered: str) -> str:
        k = await self.tools.execute("get_microservices_overview", {})
        total = int(k.get("total_services", 0))
        raw_services = k.get("services", [])
        services = [str(name) for name in raw_services] if isinstance(raw_services, list) else []
        if total == 0:
            return "لا توجد خدمات مصغرة معرفة حالياً."

        wants_names = any(
            token in lowered
            for token in ["ما هي", "اسم", "الأسماء", "قائمة", "list", "اسماء", "أسماء"]
        )
        summary = f"عدد الخدمات المصغرة: {total}."
        if wants_names:
            lines = "\n".join(f"- {name}" for name in services)
            return f"{summary}\nأسماء الخدمات:\n{lines}"
        return summary

    async def _handle_route_query(self, question: str, lowered: str) -> str:
        f = self._extract_route_fragment(question)
        if not f:
            return "يرجى تحديد جزء من المسار."
        res = await self.tools.execute("find_route", {"path_fragment": f})
        return self._format_locs(res, f"مسارات '{f}'")

    async def _handle_symbol_query(self, question: str, lowered: str) -> str:
        s = self._extract_symbol(question)
        if not s:
            return "حدد الرمز."
        res = await self.tools.execute("find_symbol", {"symbol": s})
        return self._format_locs(res, f"تعريفات '{s}'")

    async def _handle_code_search(self, question: str, lowered: str) -> str:
        q = self._extract_search_query(question)
        if not q:
            return "حدد كلمة للبحث."
        gov = await self.refactor_agent.process({})
        if not gov.success:
            return f"خطأ حوكمة: {gov.message}"
        res = await self.tools.execute("search_codebase", {"query": q})
        return self._format_locs(res, f"نتائج '{q}'")

    async def _handle_file_snippet(self, question: str, lowered: str) -> str:
        path, start, end = self._extract_file_line(question)
        if not path or start is None:
            return "حدد الملف والسطر (file.py:10)."

        snip = await self.tools.execute(
            "read_file_snippet",
            {"file_path": path, "start_line": start, "end_line": end},
        )
        lines = "\n".join(
            f"{snip['start_line'] + i}: {line}" for i, line in enumerate(snip["lines"])
        )
        return f"مقتطف {path}:\n{lines}"

    # --- Helpers ---

    def _extract_limit(self, s: str) -> int | None:
        m = re.search(r"(?:limit|أول)\s+(\d+)", s)
        return int(m.group(1)) if m else None

    def _extract_id(self, s: str) -> int | None:
        m = re.search(r"(\d+)", s)
        return int(m.group(1)) if m else None

    def _extract_table_name(self, s: str) -> str | None:
        m = re.search(r"(?:table|جدول)\s+([\w_]+)", s)
        return m.group(1) if m else None

    def _extract_route_fragment(self, s: str) -> str | None:
        if q := self._extract_quoted(s):
            return q
        m = re.search(r"/[\w\-_\/]+", s)
        return m.group(0) if m else None

    def _extract_symbol(self, s: str) -> str | None:
        m = re.search(r"(?:دالة|function|class|كلاس)\s+([\w_]+)", s, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_search_query(self, s: str) -> str | None:
        if q := self._extract_quoted(s):
            return q
        tokens = [t for t in re.sub(r"[؟?]", " ", s).split() if len(t) > 2]
        return tokens[-1] if tokens else None

    def _extract_quoted(self, s: str) -> str | None:
        m = re.search(r"['\"]([^'\"]+)['\"]", s)
        return m.group(1).strip() if m else None

    def _extract_file_line(self, s: str) -> tuple[str | None, int | None, int | None]:
        m = re.search(r"([\w\-/\.]+\.py)(?::(\d+)(?:-(\d+))?)?", s)
        if not m:
            return None, None, None
        path = m.group(1)
        start = int(m.group(2)) if m.group(2) else None
        end = int(m.group(3)) if m.group(3) else None
        return path, start, end

    def _format_locs(self, results: list[dict], title: str) -> str:
        if not results:
            return f"{title}: لا توجد نتائج."
        lines = [
            f"- {result['file_path']}"
            + (f":{result['line_number']}" if result.get("line_number") else "")
            for result in results[:10]
        ]
        return f"{title}:\n" + "\n".join(lines)
