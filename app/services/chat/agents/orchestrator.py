import re

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.services.chat.agents.analytics import AnalyticsAgent
from app.services.chat.agents.api_contract import APIContractAgent
from app.services.chat.agents.curriculum import CurriculumAgent
from app.services.chat.agents.data_access import DataAccessAgent
from app.services.chat.agents.refactor import RefactorAgent
from app.services.chat.agents.test_agent import TestAgent
from app.services.chat.context_service import get_context_service
from app.services.chat.intent_detector import ChatIntent, IntentDetector
from app.services.chat.tools import ToolRegistry

logger = get_logger("orchestrator-agent")


class OrchestratorAgent:
    """
    الوكيل المنسق الرئيسي للوكلاء والأدوات.

    مسؤولياته:
    - تحليل الاستفسار الإداري.
    - توجيه الطلبات إلى الأدوات المناسبة.
    - دمج النتائج في رد واضح وقابل للتنفيذ.
    """

    def __init__(self, ai_client: AIClient, tools: ToolRegistry) -> None:
        self.ai_client = ai_client
        self.tools = tools
        self.intent_detector = IntentDetector()
        self.system_context: str | None = None

        # Agents
        self.api_agent = APIContractAgent()
        self.data_agent = DataAccessAgent()
        self.refactor_agent = RefactorAgent()
        self.test_agent = TestAgent()
        # Pass AI Client to Analytics Agent for Superhuman capabilities
        self.analytics_agent = AnalyticsAgent(tools, ai_client)
        self.curriculum_agent = CurriculumAgent(tools)

    async def run(self, question: str, context: dict[str, object] | None = None):
        """
        حلقة التنفيذ الرئيسية (Streaming Version):
        1. تحليل النية (محدث لاستخدام IntentDetector).
        2. التحقق من الحوكمة.
        3. تنفيذ الأدوات.
        4. صياغة إجابة دقيقة.
        """
        logger.info(f"Orchestrator received: {question}")

        normalized = question.strip()
        lowered = normalized.lower()
        context = context or {}
        self.system_context = context.get("system_context") if context else None

        # 1. Advanced Intent Detection
        intent_result = await self.intent_detector.detect(normalized)
        logger.info(f"Detected intent: {intent_result.intent}")

        # 2. Select Handler based on Intent or Legacy Regex
        handler = self._resolve_handler(intent_result, lowered)

        try:
            # If the handler is the fallback (LLM) or agent, it might yield chunks
            if handler == self._handle_analytics:
                # Security: Ensure user_id comes from authenticated context, do not default to 1
                result = self.analytics_agent.process(context)
            elif handler == self._handle_curriculum:
                # Refine intent for Curriculum Agent
                if self._is_path_progress_query(lowered):
                    context["intent_type"] = "path_progress"
                elif self._is_difficulty_adjustment(lowered):
                    context["intent_type"] = "difficulty_adjust"
                    context["feedback"] = "too_hard" if "صعب" in lowered else "good"
                else:
                    context["intent_type"] = "recommendation"

                result = self.curriculum_agent.process(context)
            else:
                result = await handler(normalized, lowered)

            # If result is an async generator, yield from it
            if hasattr(result, "__aiter__"):
                async for chunk in result:
                    yield chunk
            else:
                # It's a string, yield it directly
                yield str(result)

        except Exception as exc:
            logger.error("Orchestrator failed", exc_info=exc)
            yield f"تعذر تنفيذ الطلب بدقة: {exc}"

    def _resolve_handler(self, intent_result, lowered: str):
        """توجيه الطلب بناءً على كاشف النوايا أو القواعد القديمة."""

        # New Intents
        if intent_result.intent == ChatIntent.ANALYTICS_REPORT:
            return self._handle_analytics
        if intent_result.intent == ChatIntent.LEARNING_SUMMARY:
            return self._handle_analytics
        if intent_result.intent == ChatIntent.CURRICULUM_PLAN:
            return self._handle_curriculum

        # Legacy Regex Checks
        return self._select_handler(lowered)

    def _select_handler(self, lowered: str):
        """اختيار معالج مناسب حسب كلمات مفتاحية (Legacy)."""
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
        return self._handle_fallback

    def _is_user_count_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "how many users",
                "count users",
                "عدد المستخدمين",
                "كم عدد المستخدمين",
                "كم مستخدم",
                "كم شخص",
                "كم شخص مسجل",
                "كم مستخدم مسجل",
                "عدد المسجلين",
                "عدد الحسابات",
            ]
        )

    def _is_user_list_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "list users",
                "all users",
                "قائمة المستخدمين",
                "عرض المستخدمين",
            ]
        )

    def _is_user_profile_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "user profile",
                "تفاصيل المستخدم",
                "معلومات المستخدم",
            ]
        )

    def _is_user_stats_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "user stats",
                "user statistics",
                "إحصائيات المستخدم",
                "دردشات المستخدم",
                "سجل الدردشة",
            ]
        )

    def _is_database_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "database",
                "schema",
                "tables",
                "قاعدة البيانات",
                "قواعد البيانات",
                "الجداول",
                "مخطط",
            ]
        )

    def _is_database_map_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "database map",
                "relationships",
                "foreign keys",
                "خريطة قاعدة البيانات",
                "العلاقات",
                "المفاتيح الأجنبية",
            ]
        )

    def _is_project_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "project",
                "structure",
                "architecture",
                "المشروع",
                "بنية المشروع",
                "هيكل المشروع",
            ]
        )

    def _is_file_snippet_query(self, lowered: str) -> bool:
        has_file = ".py" in lowered
        has_line = "line" in lowered or "سطر" in lowered or ":" in lowered
        return has_file and has_line

    def _is_route_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "route",
                "endpoint",
                "api path",
                "مسار",
                "نقطة نهاية",
            ]
        )

    def _is_symbol_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
                "function",
                "class",
                "دالة",
                "كلاس",
                "class ",
            ]
        )

    def _is_code_search_query(self, lowered: str) -> bool:
        return any(
            phrase in lowered
            for phrase in [
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

    @staticmethod
    def _format_user_lines(users: list[dict[str, object]]) -> list[str]:
        """
        تنسيق قائمة المستخدمين بصيغة موجزة تحتوي على الاسم والتاريخ.
        """
        lines: list[str] = []
        for user in users:
            updated_at = user.get("updated_at") or "غير متوفر"
            lines.append(
                f"- #{user['id']} | {user['full_name']} | {user['email']} | "
                f"حالة: {user['status']} | إنشاء: {user['created_at']} | تحديث: {updated_at}"
            )
        return lines

    async def _handle_user_count(self, _: str, lowered: str) -> str:
        gov_response = await self.data_agent.process(
            {"entity": "user", "operation": "count", "access_method": "service_api"}
        )
        if not gov_response.success:
            return f"Governance Error: {gov_response.message}"

        count = await self.tools.execute("get_user_count", {})
        if count == 0:
            return "لا يوجد مستخدمون مسجلون حالياً ضمن المنصة. (0 users)"
        return f"عدد المستخدمين الحاليين في المنصة هو: {count}. ({count} users)"

    async def _handle_user_list(self, question: str, lowered: str) -> str:
        gov_response = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "list",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov_response.success:
            return f"خطأ حوكمة البيانات: {gov_response.message}"

        limit = self._extract_limit(lowered) or 20
        users = await self.tools.execute("list_users", {"limit": limit, "offset": 0})
        if not users:
            return "لا يوجد مستخدمون متاحون حالياً."

        lines = self._format_user_lines(users)
        return "قائمة المستخدمين (موجز):\n" + "\n".join(lines)

    async def _handle_user_profile(self, question: str, lowered: str) -> str:
        user_id = self._extract_user_id(question)
        if user_id is None:
            return "يرجى تزويدي بمعرّف المستخدم (ID) لعرض ملفه الكامل."

        gov_response = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "profile",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov_response.success:
            return f"خطأ حوكمة البيانات: {gov_response.message}"

        profile = await self.tools.execute("get_user_profile", {"user_id": user_id})
        if profile.get("error"):
            return f"تعذر العثور على المستخدم #{user_id}."

        basic = profile.get("basic", {})
        stats = profile.get("statistics", {})
        return (
            f"ملف المستخدم #{user_id}:\n"
            f"- الاسم: {basic.get('full_name')}\n"
            f"- البريد: {basic.get('email')}\n"
            f"- حالة الحساب: {basic.get('status')}\n"
            f"- تاريخ التسجيل: {basic.get('created_at')}\n"
            f"- آخر تحديث: {basic.get('updated_at')}\n"
            f"- إجمالي الرسائل: {stats.get('total_chat_messages')}\n"
            f"- آخر نشاط: {stats.get('last_activity')}"
        )

    async def _handle_user_statistics(self, question: str, lowered: str) -> str:
        user_id = self._extract_user_id(question)
        if user_id is None:
            return "يرجى تحديد رقم المستخدم للحصول على إحصائياته."

        gov_response = await self.data_agent.process(
            {
                "entity": "user",
                "operation": "statistics",
                "access_method": "direct_db",
                "purpose": "admin_analytics",
            }
        )
        if not gov_response.success:
            return f"خطأ حوكمة البيانات: {gov_response.message}"

        stats = await self.tools.execute("get_user_statistics", {"user_id": user_id})
        if not stats:
            return f"تعذر العثور على إحصائيات للمستخدم #{user_id}."

        return (
            f"إحصائيات المستخدم #{user_id}:\n"
            f"- إجمالي المهام: {stats.get('total_missions')}\n"
            f"- مهام مكتملة: {stats.get('completed_missions')}\n"
            f"- مهام نشطة: {stats.get('active_missions')}\n"
            f"- إجمالي الرسائل: {stats.get('total_chat_messages')}\n"
            f"- آخر نشاط: {stats.get('last_activity')}"
        )

    async def _handle_database_query(self, question: str, lowered: str) -> str:
        table_name = self._extract_table_name(lowered)
        if table_name and ("count" in lowered or "عدد" in lowered):
            count = await self.tools.execute("get_table_count", {"table_name": table_name})
            return f"عدد السجلات في جدول '{table_name}': {count}."
        if table_name:
            schema = await self.tools.execute("get_table_schema", {"table_name": table_name})
            if not schema:
                return f"تعذر العثور على مخطط جدول '{table_name}'."
            columns = schema.get("columns", [])
            columns_text = "\n".join(f"- {col['name']} ({col['type']})" for col in columns)
            return f"مخطط جدول '{table_name}':\n{columns_text}"

        tables = await self.tools.execute("get_database_tables", {})
        return "جداول قاعدة البيانات:\n" + "\n".join(f"- {name}" for name in tables[:50])

    async def _handle_database_map(self, _: str, __: str) -> str:
        db_map = await self.tools.execute("get_database_map", {})
        tables = db_map.get("tables", [])
        relationships = db_map.get("relationships", [])
        sample_relationships = relationships[:10]
        formatted_relationships = "\n".join(
            f"- {rel['from_table']} -> {rel['to_table']} ({rel['from_column']} → {rel['to_column']})"
            for rel in sample_relationships
        )
        return (
            "خريطة قاعدة البيانات:\n"
            f"- عدد الجداول: {len(tables)}\n"
            f"- عدد العلاقات: {len(relationships)}\n"
            f"- أمثلة علاقات:\n{formatted_relationships}"
        )

    async def _handle_project_query(self, _: str, __: str) -> str:
        knowledge = await self.tools.execute("get_project_overview", {})
        structure = knowledge.get("structure", {})
        database = knowledge.get("database", {})
        return (
            "ملخص المشروع:\n"
            f"- اسم المشروع: {knowledge.get('project_name')}\n"
            f"- الإصدار: {knowledge.get('version')}\n"
            f"- عدد الجداول: {database.get('total_tables')}\n"
            f"- ملفات Python: {structure.get('python_files')}\n"
            f"- المسار الجذري: {structure.get('root_path')}"
        )

    async def _handle_route_query(self, question: str, lowered: str) -> str:
        fragment = self._extract_route_fragment(question)
        if not fragment:
            return "يرجى تحديد جزء من مسار الـ API للبحث عنه."
        results = await self.tools.execute("find_route", {"path_fragment": fragment})
        return self._format_code_locations(results, f"نتائج المسارات المحتملة لـ '{fragment}'")

    async def _handle_symbol_query(self, question: str, lowered: str) -> str:
        symbol = self._extract_symbol_name(question)
        if not symbol:
            return "يرجى تحديد اسم الدالة/الكلاس المراد البحث عنه."
        results = await self.tools.execute("find_symbol", {"symbol": symbol})
        return self._format_code_locations(results, f"تعريفات '{symbol}'")

    async def _handle_code_search(self, question: str, lowered: str) -> str:
        query = self._extract_search_query(question)
        if not query:
            return "يرجى تحديد كلمة مفتاحية أو اسم ميزة للبحث عنها في الشيفرة."
        gov_response = await self.refactor_agent.process({})
        if not gov_response.success:
            return f"خطأ حوكمة: {gov_response.message}"
        results = await self.tools.execute("search_codebase", {"query": query})
        return self._format_code_locations(results, f"نتائج البحث عن '{query}'")

    async def _handle_file_snippet(self, question: str, lowered: str) -> str:
        file_path, start_line, end_line = self._extract_file_and_line(question)
        if not file_path or start_line is None:
            return "يرجى تحديد مسار الملف ورقم السطر (مثال: app/services/chat/orchestrator.py:120)."

        snippet = await self.tools.execute(
            "read_file_snippet",
            {"file_path": file_path, "start_line": start_line, "end_line": end_line},
        )
        formatted_lines = "\n".join(
            f"{snippet['start_line'] + idx}: {line}" for idx, line in enumerate(snippet["lines"])
        )
        return (
            f"مقتطف من {snippet['file_path']} (الأسطر {snippet['start_line']} إلى {snippet['end_line']}):\n"
            f"{formatted_lines}"
        )

    # --- New Agent Handlers (Placeholders for typing consistency) ---
    # The actual dispatch logic is in run(), calling agent.process() directly

    async def _handle_analytics(self, *args):
        pass

    async def _handle_curriculum(self, *args):
        pass

    async def _handle_fallback(self, question: str, __: str):
        """
        معالجة الاستفسارات العامة غير المطابقة لأوامر الأدمن الصريحة.
        تعتمد على نموذج الذكاء الاصطناعي لتقديم إجابة واقعية بدلاً من رد ثابت.
        """
        try:
            context_service = get_context_service()
            system_prompt = context_service.get_admin_system_prompt()
        except Exception as exc:
            logger.error("فشل تحميل سياق الأدمن", exc_info=exc)
            system_prompt = "أنت مساعد إداري محترف يجيب بإيجاز ودقة."

        if self.system_context:
            system_prompt = "\n\n".join([system_prompt, self.system_context])

        try:
            # We manually construct the message list here to use stream_chat directly
            # This bypasses the send_message string accumulator
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]

            async for chunk in self.ai_client.stream_chat(messages):
                # Extract content from chunk structure
                # The structure depends on what mesh.stream_chat yields
                # mesh.stream_chat yields: {"choices": [{"delta": {"content": ...}}]}

                content = ""
                # Handle direct dict access safely
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")

                if content:
                    yield content

        except Exception as exc:
            logger.error("فشل الرد عبر نموذج الذكاء الاصطناعي", exc_info=exc)
            yield (
                "تعذر توليد إجابة دقيقة حالياً. "
                "يرجى إعادة صياغة السؤال أو تحديد المجال المطلوب بدقة."
            )

    def _extract_limit(self, lowered: str) -> int | None:
        match = re.search(r"(?:limit|أول|first)\s+(\d+)", lowered)
        if not match:
            return None
        return int(match.group(1))

    def _extract_user_id(self, question: str) -> int | None:
        match = re.search(r"(\d+)", question)
        if not match:
            return None
        return int(match.group(1))

    def _extract_table_name(self, lowered: str) -> str | None:
        match = re.search(r"(?:table|جدول)\s+([\w_]+)", lowered)
        if not match:
            return None
        return match.group(1)

    def _extract_route_fragment(self, question: str) -> str | None:
        quoted = self._extract_quoted_text(question)
        if quoted:
            return quoted
        match = re.search(r"/[\w\-_\/]+", question)
        if match:
            return match.group(0)
        return None

    def _extract_file_and_line(self, question: str) -> tuple[str | None, int | None, int | None]:
        match = re.search(r"([\w\-/\.]+\.py)(?::(\d+)(?:-(\d+))?)?", question)
        if not match:
            return None, None, None
        file_path = match.group(1)
        start_line = int(match.group(2)) if match.group(2) else None
        end_line = int(match.group(3)) if match.group(3) else None
        if start_line is None and ("line" in question.lower() or "سطر" in question):
            return file_path, None, None
        return file_path, start_line, end_line

    def _extract_symbol_name(self, question: str) -> str | None:
        match = re.search(r"(?:دالة|function|class|كلاس)\s+([\w_]+)", question, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _is_path_progress_query(self, lowered: str) -> bool:
        return any(x in lowered for x in ["مسار", "path", "تقدم", "progress", "milestone"])

    def _is_difficulty_adjustment(self, lowered: str) -> bool:
        return any(x in lowered for x in ["صعب", "hard", "easy", "سهل", "تغيير المستوى", "change level"])

    def _extract_search_query(self, question: str) -> str | None:
        quoted = self._extract_quoted_text(question)
        if quoted:
            return quoted
        cleaned = re.sub(r"[؟?]", " ", question)
        tokens = [t for t in cleaned.split() if len(t) > 2]
        if not tokens:
            return None
        return tokens[-1]

    def _extract_quoted_text(self, question: str) -> str | None:
        match = re.search(r"['\\\"]([^'\\\"]+)['\\\"]", question)
        if match:
            return match.group(1).strip()
        return None

    def _format_code_locations(self, results: list[dict[str, object]], title: str) -> str:
        if not results:
            return f"{title}:\nلا توجد نتائج مطابقة."
        lines = []
        for location in results[:8]:
            line = f"- {location['file_path']}"
            if location.get("line_number"):
                line += f":{location['line_number']}"
            if location.get("match_context"):
                line += f" — {location['match_context']}"
            lines.append(line)
        return f"{title}:\n" + "\n".join(lines)
