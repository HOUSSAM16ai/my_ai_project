"""
Intent handlers using Strategy pattern.
"""

import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlmodel import SQLModel

# Import chat domain to ensure AdminConversation is registered, preventing mapping errors
import app.core.domain.chat  # noqa: F401
from app.core.agents.system_principles import (
    format_architecture_system_principles,
    format_system_principles,
)
from app.core.domain.mission import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    Task,
)
from app.core.event_bus import get_event_bus
from app.core.patterns.strategy import Strategy
from app.services.chat.context import ChatContext
from app.services.chat.context_service import get_context_service
from app.services.overmind.factory import create_overmind
from app.services.overmind.identity import OvermindIdentity

logger = logging.getLogger(__name__)


class IntentHandler(Strategy[ChatContext, AsyncGenerator[str, None]]):
    """Base intent handler."""

    def __init__(self, intent_name: str, priority: int = 0):
        self._intent_name = intent_name
        self._priority = priority

    async def can_handle(self, context: ChatContext) -> bool:
        """Check if handler can process this intent."""
        return context.intent == self._intent_name

    @property
    def priority(self) -> int:
        return self._priority


class FileReadHandler(IntentHandler):
    """Handle file read requests."""

    def __init__(self):
        super().__init__("FILE_READ", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Execute file read."""
        path = context.get_param("path", "")

        if not path:
            yield "❌ لم يتم تحديد مسار الملف\n"
            return

        try:
            yield f"📖 قراءة الملف: `{path}`\n\n"
            content = await self._read_file(path)
            yield f"```\n{content}\n```\n"
            logger.info(f"File read successful: {path}", extra={"user_id": context.user_id})
        except FileNotFoundError:
            yield f"❌ الملف غير موجود: `{path}`\n"
        except PermissionError:
            yield f"❌ لا توجد صلاحية لقراءة الملف: `{path}`\n"
        except Exception as e:
            yield f"❌ خطأ في قراءة الملف: {e!s}\n"
            logger.error(f"File read error: {e}", extra={"path": path, "user_id": context.user_id})

    async def _read_file(self, path: str) -> str:
        """Read file contents in a non-blocking way."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._read_file_sync(path))

    def _read_file_sync(self, path: str) -> str:
        """Synchronous file read."""
        with open(path, encoding="utf-8") as f:
            return f.read()


class FileWriteHandler(IntentHandler):
    """Handle file write requests."""

    def __init__(self):
        super().__init__("FILE_WRITE", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Execute file write."""
        path = context.get_param("path", "")

        if not path:
            yield "❌ لم يتم تحديد مسار الملف\n"
            return

        yield f"📝 لإنشاء ملف `{path}`، يرجى تحديد المحتوى.\n"
        yield "يمكنك كتابة المحتوى في الرسالة التالية.\n"


class CodeSearchHandler(IntentHandler):
    """Handle code search requests."""

    def __init__(self):
        super().__init__("CODE_SEARCH", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Execute code search."""
        query = context.get_param("query", "")

        if not query:
            yield "❌ لم يتم تحديد استعلام البحث\n"
            return

        yield f"🔍 البحث عن: `{query}`\n\n"
        results = await self._search_code(query, context.user_id)

        if not results:
            yield "لم يتم العثور على نتائج\n"
            return

        yield f"تم العثور على {len(results)} نتيجة:\n\n"
        for result in results:
            yield f"- `{result['file']}:{result['line']}`\n"

    async def _search_code(self, query: str, user_id: int) -> list[dict]:
        """Search code (placeholder)."""
        logger.info(f"Code search: {query}", extra={"user_id": user_id})
        return []


class ProjectIndexHandler(IntentHandler):
    """Handle project indexing requests."""

    def __init__(self):
        super().__init__("PROJECT_INDEX", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Execute project indexing."""
        yield "📊 فهرسة المشروع...\n\n"
        stats = await self._index_project(context.user_id)

        yield "✅ تمت الفهرسة بنجاح:\n"
        yield f"- الملفات: {stats.get('files', 0)}\n"
        yield f"- الأسطر: {stats.get('lines', 0)}\n"

    async def _index_project(self, user_id: int) -> dict:
        """Index project (placeholder)."""
        logger.info("Project indexing started", extra={"user_id": user_id})
        return {"files": 0, "lines": 0}


class DeepAnalysisHandler(IntentHandler):
    """Handle deep analysis requests."""

    def __init__(self):
        super().__init__("DEEP_ANALYSIS", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Execute deep analysis."""
        yield "🧠 تحليل عميق للسؤال...\n\n"

        analysis = await self._analyze(context.question, context.ai_client)

        yield f"{analysis}\n"

    async def _analyze(self, question: str, ai_client) -> str:
        """Perform deep analysis."""
        return "تحليل عميق (قيد التطوير)"


class MissionComplexHandler(IntentHandler):
    """
    Handle complex mission requests using Overmind.
    Implements 'API First' streaming response pattern.
    """

    def __init__(self):
        super().__init__("MISSION_COMPLEX", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """
        Execute complex mission.
        Creates a Mission DB entry and triggers the Overmind in background.
        Streams updates to the user.
        """
        # Global try-except to prevent stream crash
        try:
            yield "🚀 **بدء المهمة الخارقة (Super Agent)**...\n"

            if not context.session_factory:
                yield "❌ خطأ: لا يوجد مصنع جلسات (Session Factory).\n"
                return

            # 1. Initialize Mission in DB
            mission_id = 0
            try:
                async with context.session_factory() as session:
                    # Self-healing: Ensure schema exists
                    await self._ensure_mission_schema(session)

                    mission = Mission(
                        objective=context.question,
                        status=MissionStatus.PENDING,
                        initiator_id=context.user_id or 1,  # Fallback if user_id missing
                    )
                    session.add(mission)
                    await session.commit()
                    await session.refresh(mission)
                    mission_id = mission.id
                    yield f"🆔 رقم المهمة: `{mission.id}`\n"
                    yield "⏳ مجلس الحكمة يبدأ التداول (Strategist, Architect, Auditor)...\n"
            except Exception as e:
                logger.error(f"Failed to create mission: {e}", exc_info=True)
                yield "\n❌ **خطأ في قاعدة البيانات:** لم نتمكن من بدء المهمة.\n"
                yield f"التفاصيل التقنية: `{e!s}`\n"
                yield "💡 **الحل:** يرجى إبلاغ الفريق التقني لفحص حالة قاعدة البيانات.\n"
                return

            # 2. Subscribe for mission events before launching background task
            event_bus = get_event_bus()
            event_queue = event_bus.subscribe_queue(f"mission:{mission_id}")

            # 3. Spawn Background Task (Non-Blocking)
            # We pass the factory so the background task can manage its own session
            task = asyncio.create_task(self._run_mission_bg(mission_id, context.session_factory))

            # 4. Stream Updates (Event-Driven)
            last_event_id = 0
            running = True

            try:
                while running:
                    try:
                        event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    except TimeoutError:
                        event = None

                    if event is not None:
                        last_event_id = max(last_event_id, event.id)
                        yield self._format_event(event)

                    if task.done():
                        running = False
                        try:
                            await task  # Check for exceptions
                        except Exception as e:
                            yield f"❌ **خطأ غير متوقع في النظام:** {e}\n"
                            logger.error(f"Background mission task failed: {e}")
                            return

                # Catch-up from DB to ensure no event is missed after task completion.
                async with context.session_factory() as session:
                    stmt = (
                        select(MissionEvent)
                        .where(MissionEvent.mission_id == mission_id)
                        .where(MissionEvent.id > last_event_id)
                        .order_by(MissionEvent.id)
                    )
                    result = await session.execute(stmt)
                    events = result.scalars().all()

                    for event in events:
                        last_event_id = event.id
                        yield self._format_event(event)

                    mission_check = await session.get(Mission, mission_id)
                    if mission_check:
                        yield f"\n🏁 **الحالة النهائية:** {mission_check.status.value}\n"

                yield "\n✅ **تم انتهاء متابعة المهمة.**\n"
            finally:
                event_bus.unsubscribe_queue(f"mission:{mission_id}", event_queue)
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info("Background mission task cancelled after stream closure.")
        except Exception as global_ex:
            logger.critical(f"Critical error in MissionComplexHandler: {global_ex}", exc_info=True)
            yield f"\n🛑 **حدث خطأ حرج أثناء تنفيذ المهمة:** {global_ex}\n"

    async def _ensure_mission_schema(self, session) -> None:
        """
        Checks and attempts to self-heal missing mission tables.
        Now uses SQLModel metadata to ensure cross-database compatibility (SQLite/Postgres).
        """
        try:
            # Explicitly define tables to verify/create
            # This avoids creating incompatible tables (e.g. vector type on SQLite)
            target_tables = [
                Mission.__table__,
                MissionPlan.__table__,
                Task.__table__,
                MissionEvent.__table__,
            ]

            bind = session.bind
            if not bind:
                logger.warning("No bind found for session in schema check.")
                return

            # Check if bind is AsyncConnection (has run_sync) or AsyncEngine (needs connect)
            if hasattr(bind, "run_sync"):
                await bind.run_sync(
                    SQLModel.metadata.create_all, tables=target_tables, checkfirst=True
                )
            else:
                # Assume AsyncEngine
                async with bind.begin() as conn:
                    await conn.run_sync(
                        SQLModel.metadata.create_all, tables=target_tables, checkfirst=True
                    )

            logger.info("Schema self-healing: Verified mission tables.")

        except Exception as e:
            # Log error but attempt to continue, assuming tables might exist or partial failure
            logger.error(f"Schema self-healing failed: {e}")

    async def _run_mission_bg(self, mission_id: int, session_factory):
        """
        Runs the Overmind mission in a background task with its own session.
        """
        async with session_factory() as session:
            overmind = await create_overmind(session)
            await overmind.run_mission(mission_id)

    def _format_event(self, event: MissionEvent) -> str:
        """Format mission event for user display."""
        try:
            payload = event.payload_json or {}
            if event.event_type == MissionEventType.STATUS_CHANGE:
                brain_evt = payload.get("brain_event")
                if brain_evt:
                    return _format_brain_event(str(brain_evt), payload.get("data", {}))
                status_note = payload.get("note")
                if status_note:
                    return f"🔄 **تحديث حالة:** {status_note}\n"
                return f"🔄 **تحديث حالة:** {payload.get('old_status')} -> {payload.get('new_status')}\n"

            if event.event_type == MissionEventType.MISSION_COMPLETED:
                result = payload.get("result", {})
                result_text = ""
                if isinstance(result, dict):
                    # Check for explicit answer/output first
                    if result.get("output") or result.get("answer") or result.get("summary"):
                        result_text = (
                            result.get("output") or result.get("answer") or result.get("summary")
                        )
                    # Check for OperatorAgent results list (Customer Visibility Fix)
                    elif "results" in result and isinstance(result["results"], list):
                        result_text = _format_task_results(result["results"])
                    # Check nested execution report (Common fallback)
                    elif (
                        "last_execution_report" in result
                        and isinstance(result["last_execution_report"], dict)
                        and "results" in result["last_execution_report"]
                        and isinstance(result["last_execution_report"]["results"], list)
                    ):
                        result_text = _format_task_results(
                            result["last_execution_report"]["results"]
                        )
                    else:
                        result_text = json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    result_text = str(result)
                return f"🎉 **المهمة اكتملت بنجاح!**\n\n**النتيجة:**\n{result_text}\n"

            if event.event_type == MissionEventType.MISSION_FAILED:
                return f"💀 **فشل المهمة:** {payload.get('error')}\n"

            return f"ℹ️ {event.event_type.value}: {payload}\n"
        except Exception:
            return "ℹ️ حدث جديد...\n"


def _format_task_results(tasks: list) -> str:
    """Format a list of task results into a readable string."""
    lines = [f"✅ **تم تنفيذ {len(tasks)} مهمة بنجاح:**\n"]
    for t in tasks:
        if not isinstance(t, dict):
            continue

        name = t.get("name", "مهمة")

        # Handle Skipped
        if t.get("status") == "skipped":
            reason = t.get("reason", "غير محدد")
            lines.append(f"🔹 **{name}**: ⏭️ تم التجاوز ({reason})\n")
            continue

        res = t.get("result", {})
        if not res:
            lines.append(f"🔹 **{name}**: (لا توجد نتيجة)\n")
            continue

        # Extract content
        result_data = res.get("result_data")
        result_text = res.get("result_text")

        display_text = ""

        if result_data:
            display_text = _format_tool_result_data(result_data)
        elif result_text:
            if isinstance(result_text, str):
                try:
                    if result_text.strip().startswith(("{", "[")):
                        parsed = json.loads(result_text)
                        display_text = _format_tool_result_data(parsed)
                    else:
                        display_text = _clean_raw_string(result_text)
                except Exception:
                    display_text = result_text
            else:
                display_text = str(result_text)
        else:
            display_text = "لا توجد بيانات"

        # Auto-read file content if written
        file_content = ""
        if result_data and isinstance(result_data, dict):
            data_payload = result_data.get("data", {})
            if (
                isinstance(data_payload, dict)
                and data_payload.get("written")
                and data_payload.get("path")
            ):
                path = data_payload["path"]
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                    file_content = f"\n\n**محتوى الملف ({path}):**\n```\n{content}\n```"
                except Exception as e:
                    logger.warning(f"Failed to auto-read file {path}: {e}")

        lines.append(f"🔹 **{name}**:\n{display_text}\n{file_content}\n")
    return "\n".join(lines)


def _format_brain_event(event_name: str, data: dict[str, object] | object) -> str:
    """
    تنسيق أحداث الدماغ الخارق بصورة ملهمة للطالب أثناء التنفيذ.
    """
    if not isinstance(data, dict):
        data = {}
    normalized = event_name.lower()
    phase = str(data.get("phase", "")).upper()
    agent = str(data.get("agent", "")).strip() or "رئيس الوكلاء"

    phase_labels = {
        "PLANNING": "بناء الخطة",
        "REVIEW_PLAN": "تدقيق الخطة",
        "DESIGN": "تصميم الحل",
        "EXECUTION": "تنفيذ المهام",
        "REFLECTION": "مراجعة النتائج",
        "RE-PLANNING": "إعادة التخطيط الذكي",
    }

    if normalized == "loop_start":
        iteration = data.get("iteration", "؟")
        chief_agent = str(data.get("chief_agent") or agent)
        graph_mode = str(data.get("graph_mode") or "cognitive_graph")
        return (
            f"🧠 **جاري تفعيل الرسم البياني المعرفي** ({graph_mode}) — **{chief_agent}** يوزّع المهام بخوارزميات عبقرية"
            f" (الدورة #{iteration}).\n"
        )

    if normalized == "phase_start":
        phase_label = phase_labels.get(phase, phase or "مرحلة غير معروفة")
        unit = data.get("unit_of_work", {})
        unit_id = ""
        if isinstance(unit, dict):
            unit_id = str(unit.get("unit_id") or "")
        unit_suffix = f" | وحدة العمل: `{unit_id}`" if unit_id else ""
        return (
            f"✨ **جاري {phase_label}** داخل شبكة التنسيق العامة بواسطة **{agent}**"
            f"{unit_suffix}...\n"
        )

    if normalized == "plan_rejected":
        return "🧩 **جاري إعادة ضبط الخطة** بعد مراجعة صارمة لضمان أفضل مسار.\n"

    if normalized == "plan_approved":
        return "✅ **تم اعتماد الخطة العبقرية** والانطلاق نحو التنفيذ المتقدم.\n"

    if normalized.endswith("_completed"):
        return "🏁 **اكتملت مرحلة أساسية بنجاح** — التقدم جارٍ بشكل خارق.\n"

    if normalized.endswith("_timeout"):
        return "⏳ **تأخر غير متوقع** — جاري إعادة المزامنة لضمان الجودة.\n"

    if normalized == "mission_critique_failed":
        critique = data.get("critique", {})
        feedback = (
            critique.get("feedback", "لم يتم تقديم ملاحظات.")
            if isinstance(critique, dict)
            else str(critique)
        )
        return f"🔔 **تحديث معرفي (فشل التدقيق):**\n📝 **الملاحظات:** {feedback}\n🔄 جاري إعادة التخطيط...\n"

    if normalized in {"mission_success", "phase_error"}:
        return f"🔔 **تحديث معرفي:** {event_name}.\n"

    return f"🔹 **{event_name}**: {data}\n"


def _format_tool_result_data(data: object) -> str:
    """Format tool result data for display."""
    if not isinstance(data, (dict, list)):
        return str(data)

    # Handle ToolResult structure (only if dict)
    if isinstance(data, dict) and "ok" in data and ("data" in data or "error" in data):
        if not data.get("ok"):
            return f"❌ خطأ: {data.get('error')}"

        inner_data = data.get("data")
        if inner_data is None:
            return "✅ تم التنفيذ بنجاح."

        return _format_inner_data(inner_data)

    return _format_inner_data(data)


def _format_inner_data(data: object) -> str:
    """Format inner data (dict/list) nicely."""
    # Custom formatting for search results (List of content items)
    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], dict)
        and "title" in data[0]
        and "id" in data[0]
    ):
        lines = ["✅ **تم العثور على النتائج التالية:**\n"]
        for item in data:
            title = item.get("title", "بدون عنوان")
            year = item.get("year", "")
            subject = item.get("subject", "")
            branch = item.get("branch", "")

            meta = []
            if year:
                meta.append(str(year))
            if subject:
                meta.append(subject)
            if branch:
                meta.append(branch)

            meta_str = f" *({', '.join(str(x) for x in meta)})*" if meta else ""
            lines.append(f"* 🔹 **{title}**{meta_str}")

        # Add a hint about how to proceed
        lines.append("\n💡 *يمكنك طلب محتوى أي عنصر باستخدام اسمه أو تفاصيله.*")
        return "\n".join(lines)

    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)


def _clean_raw_string(text: str) -> str:
    """Clean raw ToolResult string representation."""
    if text.startswith("ToolResult("):
        match = re.search(r"data=(.*?)(, error=|$)", text)
        if match:
            return f"✅ {match.group(1)}"
        return text
    return text


class HelpHandler(IntentHandler):
    """Handle help requests."""

    def __init__(self):
        super().__init__("HELP", priority=10)

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Show help."""
        yield "📚 **المساعدة**\n\n"
        yield "الأوامر المتاحة:\n"
        yield "- قراءة ملف: `اقرأ ملف path/to/file`\n"
        yield "- كتابة ملف: `اكتب ملف path/to/file`\n"
        yield "- البحث: `ابحث عن query`\n"
        yield "- فهرسة: `فهرس المشروع`\n"
        yield "- مهمة معقدة: (أي سؤال معقد سيتم تحويله للوكيل الخارق)\n"


class DefaultChatHandler(IntentHandler):
    """Default chat handler (fallback)."""

    def __init__(self):
        super().__init__("DEFAULT", priority=-1)
        self._identity = OvermindIdentity()
        self._context_service = get_context_service()

    async def can_handle(self, context: ChatContext) -> bool:
        """Always can handle (fallback)."""
        return True

    async def execute(self, context: ChatContext) -> AsyncGenerator[str, None]:
        """Execute default chat with identity context."""
        # إضافة معلومات الهوية إلى رسائل المحادثة
        enhanced_messages = self._add_identity_context(context.history_messages)

        async for chunk in context.ai_client.stream_chat(enhanced_messages):
            if isinstance(chunk, dict):
                choices = chunk.get("choices", [])
                if choices:
                    content = choices[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
            elif isinstance(chunk, str):
                yield chunk

    def _add_identity_context(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        إضافة سياق النظام والهوية لإثراء إجابة Overmind.

        Args:
            messages: قائمة الرسائل الأصلية.

        Returns:
            list[dict[str, str]]: قائمة الرسائل بعد إدراج سياق النظام.
        """
        has_system = bool(messages) and messages[0].get("role") == "system"
        system_prompt = self._build_system_prompt(include_base_prompt=not has_system)
        if not has_system:
            return [{"role": "system", "content": system_prompt}, *messages]

        enhanced_messages = messages.copy()
        enhanced_messages[0] = {
            "role": "system",
            "content": messages[0]["content"] + "\n\n" + system_prompt,
        }
        return enhanced_messages

    def _build_system_prompt(self, *, include_base_prompt: bool) -> str:
        """
        إنشاء رسالة النظام الموحدة لتوجيه الردود الخارقة.

        Returns:
            str: رسالة نظام مركزة تجمع الهوية والتعليمات المتقدمة.
        """
        base_prompt = ""
        if include_base_prompt:
            base_prompt = self._context_service.get_context_system_prompt().strip()
        identity_context = self._build_identity_context()
        intelligence_directive = (
            "توجيه إضافي:\n"
            "- أجب بطريقة عبقرية فائقة الذكاء مع شرح منطقي متسلسل.\n"
            "- حافظ على العمق والوضوح، وقدم أمثلة تعليمية عند الحاجة.\n"
            "- إذا كان السؤال تعليمياً، قدم خطة تعلم مختصرة قبل الإجابة.\n"
        )
        multi_agent_directive = (
            "توجيهات العقل الجمعي:\n"
            "- فعّل أسلوب التفكير متعدد الوكلاء (Strategist/Architect/Auditor/Operator).\n"
            "- لخّص خطة الحل في نقاط، ثم نفّذ الإجابة خطوة بخطوة.\n"
            "- تحقّق من الفرضيات وصحّح المسار عند وجود غموض.\n"
            "- استخدم أسلوب Tree of Thoughts عند الأسئلة المعقدة.\n"
        )
        return "\n\n".join(
            part
            for part in [
                base_prompt,
                identity_context,
                intelligence_directive,
                multi_agent_directive,
            ]
            if part
        )

    def _build_identity_context(self) -> str:
        """
        بناء سياق الهوية التفصيلي لـ Overmind.

        Returns:
            str: نص هوية شامل للمؤسس ودور النظام.
        """
        founder = self._identity.get_founder_info()
        overmind = self._identity.get_overmind_info()
        principles_text = format_system_principles(
            header="المبادئ الصارمة للنظام (تُطبّق على الشيفرة بالكامل):",
            bullet="-",
            include_header=True,
        )
        architecture_principles_text = format_architecture_system_principles(
            header="مبادئ المعمارية وحوكمة البيانات (تُطبّق على الشيفرة بالكامل):",
            bullet="-",
            include_header=True,
        )
        return f"""أنت {overmind["name_ar"]} (Overmind)، {overmind["role_ar"]}.

معلومات المؤسس (مهمة جداً):
- الاسم الكامل: {founder["name_ar"]} ({founder["name"]})
- الاسم الأول: {founder["first_name_ar"]} ({founder["first_name"]})
- اللقب: {founder["last_name_ar"]} ({founder["last_name"]})
- تاريخ الميلاد: {founder["birth_date"]} (11 أغسطس 1997)
- الدور: {founder["role_ar"]} ({founder["role"]})
- GitHub: @{founder["github"]}

{principles_text}

{architecture_principles_text}

عندما يسأل أحد عن المؤسس أو مؤسس النظام أو من أنشأ Overmind، أجب بهذه المعلومات بدقة تامة.
"""
