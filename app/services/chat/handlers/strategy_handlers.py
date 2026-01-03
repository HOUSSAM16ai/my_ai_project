"""
Intent handlers using Strategy pattern.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import select

from app.core.patterns.strategy import Strategy
from app.core.domain.models import Mission, MissionEvent, MissionEventType, MissionStatus
from app.services.chat.context import ChatContext
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
        yield "🚀 **بدء المهمة الخارقة (Super Agent)**...\n"

        if not context.session_factory:
            yield "❌ خطأ: لا يوجد مصنع جلسات (Session Factory).\n"
            return

        # 1. Initialize Mission in DB
        mission_id = 0
        async with context.session_factory() as session:
            mission = Mission(
                objective=context.question,
                status=MissionStatus.PENDING,
                initiator_id=context.user_id or 1 # Fallback if user_id missing
            )
            session.add(mission)
            await session.commit()
            await session.refresh(mission)
            mission_id = mission.id
            yield f"🆔 رقم المهمة: `{mission.id}`\n"
            yield "⏳ مجلس الحكمة يبدأ التداول (Strategist, Architect, Auditor)...\n"

        # 2. Spawn Background Task (Non-Blocking)
        # We pass the factory so the background task can manage its own session
        task = asyncio.create_task(self._run_mission_bg(mission_id, context.session_factory))

        # 3. Poll for Updates
        last_event_id = 0
        running = True

        while running:
            await asyncio.sleep(1.0) # Poll interval

            # Check if background task crashed or finished
            if task.done():
                running = False
                try:
                    await task # Check for exceptions
                except Exception as e:
                    yield f"❌ **خطأ غير متوقع في النظام:** {e}\n"
                    logger.error(f"Background mission task failed: {e}")
                    return

            # Poll events
            async with context.session_factory() as session:
                # Fetch new events
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

                # Check mission status if task is done or we suspect completion
                mission_check = await session.get(Mission, mission_id)
                if mission_check.status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                     if running: # If we haven't detected task end yet
                         running = False
                         yield f"\n🏁 **الحالة النهائية:** {mission_check.status.value}\n"

        yield "\n✅ **تم انتهاء متابعة المهمة.**\n"

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
                    return f"🔹 *{brain_evt}*: {payload.get('data', '')}\n"
                return f"🔄 **تحديث حالة:** {payload.get('old_status')} -> {payload.get('new_status')}\n"

            if event.event_type == MissionEventType.MISSION_COMPLETED:
                return "🎉 **المهمة اكتملت بنجاح!**\n"

            if event.event_type == MissionEventType.MISSION_FAILED:
                return f"💀 **فشل المهمة:** {payload.get('error')}\n"

            return f"ℹ️ {event.event_type.value}: {payload}\n"
        except Exception:
            return "ℹ️ حدث جديد...\n"

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
        إضافة معلومات الهوية إلى سياق المحادثة.
        
        Args:
            messages: قائمة الرسائل الأصلية
            
        Returns:
            list: قائمة الرسائل مع معلومات الهوية
        """
        # الحصول على معلومات المؤسس
        founder = self._identity.get_founder_info()
        overmind = self._identity.get_overmind_info()
        
        # بناء رسالة النظام مع معلومات الهوية
        identity_context = f"""أنت {overmind['name_ar']} (Overmind)، {overmind['role_ar']}.

معلومات المؤسس (مهمة جداً):
- الاسم الكامل: {founder['name_ar']} ({founder['name']})
- الاسم الأول: {founder['first_name_ar']} ({founder['first_name']})
- اللقب: {founder['last_name_ar']} ({founder['last_name']})
- تاريخ الميلاد: {founder['birth_date']} (11 أغسطس 1997)
- الدور: {founder['role_ar']} ({founder['role']})
- GitHub: @{founder['github']}

عندما يسأل أحد عن المؤسس أو مؤسس النظام أو من أنشأ Overmind، أجب بهذه المعلومات بدقة تامة.
"""
        
        # إضافة رسالة النظام في البداية إذا لم تكن موجودة
        if not messages or messages[0].get("role") != "system":
            return [{"role": "system", "content": identity_context}] + messages
        else:
            # إضافة معلومات الهوية إلى رسالة النظام الموجودة
            enhanced_messages = messages.copy()
            enhanced_messages[0] = {
                "role": "system",
                "content": messages[0]["content"] + "\n\n" + identity_context
            }
            return enhanced_messages
