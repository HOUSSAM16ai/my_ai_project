from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_gateway import AIClient
from app.models import AdminConversation, MessageRole
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.chat import get_chat_orchestrator

logger = logging.getLogger(__name__)


class AdminChatStreamer:
    """
    بث محادثات المسؤول (Admin Chat Streamer).
    ---------------------------------------------------------
    مسؤول عن إدارة تدفق البيانات الحية (SSE) بين النواة المركزية (Overmind)
    وواجهة المسؤول، مع ضمان الحفاظ على الحالة (Persistence) بشكل غير متزامن.

    المبادئ المعمارية:
    - **فصل الاهتمامات (Separation of Concerns)**: منطق البث مفصول تماماً عن منطق التخزين.
    - **المرونة (Resilience)**: استخدام `asyncio.create_task` لضمان عدم حجب التدفق أثناء الحفظ.
    - **الاستجابة الفورية (Low Latency)**: إرسال الأجزاء (Chunks) فور وصولها.
    """

    def __init__(self, persistence: AdminChatPersistence) -> None:
        """
        تهيئة باث المحادثة.

        Args:
            persistence: خدمة التخزين الدائم للمحادثات.
        """
        self.persistence = persistence

    async def stream_response(
        self,
        user_id: int,
        conversation: AdminConversation,
        question: str,
        history: list[dict[str, Any]],
        ai_client: AIClient,
        session_factory_func: Callable[[], AsyncSession],
    ) -> AsyncGenerator[str, None]:
        """
        تنفيذ عملية البث الحي للاستجابة.

        يقوم بالخطوات التالية:
        1. حقن سياق النظام (System Context) إذا لزم الأمر.
        2. تحديث التاريخ المحلي للجلسة.
        3. إرسال حدث بدء المحادثة.
        4. استدعاء المنسق (Orchestrator) لمعالجة الطلب.
        5. بث النتائج جزئياً (Streaming).
        6. بدء حفظ النتيجة في الخلفية (Background Persistence) لعدم تأخير إشارة النهاية.

        Yields:
            str: أحداث SSE بتنسيق `event: type\ndata: json\n\n`.
        """
        # 0. حقن سياق العقل المدبر (Overmind Context) إذا كان مفقوداً
        has_system = any(msg.get("role") == "system" for msg in history)
        if not has_system:
            try:
                # استيراد متأخر لتجنب الدورات (Circular Imports)
                from app.services.chat.context_service import get_context_service

                ctx_service = get_context_service()
                system_prompt = ctx_service.get_context_system_prompt()
                history.insert(0, {"role": "system", "content": system_prompt})
            except Exception as e:
                logger.error(f"⚠️ Failed to inject Overmind context: {e}")

        # 1. تحديث التاريخ في الذاكرة (للسياق الحالي فقط)
        if not history or history[-1]["content"] != question:
            history.append({"role": "user", "content": question})

        orchestrator = get_chat_orchestrator()

        # 2. إرسال حدث التهيئة (Init Event)
        # يساعد الواجهة الأمامية على ربط المحادثة الحالية بالمعرف الصحيح
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        yield f"event: conversation_init\ndata: {json.dumps(init_payload)}\n\n"

        full_response: list[str] = []

        # 3. دالة مساعدة للحفظ الآمن (Persistence Helper)
        async def safe_persist() -> None:
            """حفظ رد المساعد في قاعدة البيانات باستخدام جلسة منفصلة."""
            assistant_content = "".join(full_response)
            if not assistant_content:
                # في حال لم يتم توليد أي رد، نسجل خطأ
                assistant_content = "Error: No response received from AI service."

            try:
                # استخدام جلسة جديدة لضمان عدم تأثر الحفظ بحالة الجلسة الأصلية
                async with session_factory_func() as session:
                    p = AdminChatPersistence(session)
                    await p.save_message(conversation.id, MessageRole.ASSISTANT, assistant_content)
                logger.info(f"✅ Conversation {conversation.id} saved successfully in background.")
            except Exception as e:
                logger.error(f"❌ Failed to save assistant message: {e}")

        # 4. تنفيذ البث (Streaming Execution)
        try:
            # استخدام try/finally لضمان الحفظ دائماً
            try:
                async for content_part in orchestrator.process(
                    question=question,
                    user_id=user_id,
                    conversation_id=conversation.id,
                    ai_client=ai_client,
                    history_messages=history,
                    session_factory=session_factory_func,
                ):
                    if content_part:
                        full_response.append(content_part)
                        # تغليف المحتوى في الهيكل المتوقع (OpenAI Style Delta)
                        chunk_data = {"choices": [{"delta": {"content": content_part}}]}
                        yield f"data: {json.dumps(chunk_data)}\n\n"

            finally:
                # حماية عملية الحفظ: تشغيلها كعملية خلفية مستقلة (Fire-and-Forget)
                # هذا يضمن وصول إشارة [DONE] إلى العميل فوراً دون انتظار قاعدة البيانات
                # RUF006: نحتفظ بمرجع للمهمة لمنع جمع القمامة المبكر
                background_tasks: set[asyncio.Task] = set()
                task = asyncio.create_task(safe_persist())
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

            # 5. إشارة الانتهاء (Completion Signal)
            # تصل للعميل فوراً بفضل فصل عملية الحفظ
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"🔥 Streaming error: {e}")
            error_payload = {"type": "error", "payload": {"details": str(e)}}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
