from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from app.core.resilience import get_circuit_breaker
from app.services.chat.handlers.base import ChatContext
from app.services.chat.security import ErrorSanitizer

if TYPE_CHECKING:
    from app.core.ai_gateway import AIClient

logger = logging.getLogger(__name__)


async def handle_deep_analysis(
    context: ChatContext,
    question: str,
    user_id: int,
    ai_client: AIClient,
) -> AsyncGenerator[str, None]:
    """
    Handle deep analytical questions using Overmind's deep understanding.
    This uses Master Agent with project indexing for comprehensive analysis.
    """
    start_time = time.time()

    yield "🧠 **تحليل عميق باستخدام Overmind Master Agent**\n\n"

    # Step 1: Build project index for context
    yield "📊 جارٍ فهرسة المشروع للحصول على سياق عميق...\n"

    try:
        from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt

        async def _build_index_async():
            return await asyncio.to_thread(build_index, root=".")

        index = await asyncio.wait_for(_build_index_async(), timeout=30.0)
        summary = summarize_for_prompt(index, max_len=3000)
        yield "✅ تم بناء فهرس المشروع\n\n"
    except TimeoutError:
        yield "⚠️ انتهت مهلة الفهرسة، سأستخدم معرفتي الحالية\n\n"
        summary = None
    except Exception as e:
        logger.warning(f"Failed to build index for deep analysis: {e}")
        yield "⚠️ لم أتمكن من فهرسة المشروع بالكامل\n\n"
        summary = None

    # Step 2: Build enhanced prompt with deep context
    system_prompt = """أنت Overmind Master Agent - نظام ذكاء اصطناعي متقدم متخصص في التحليل العميق للمشاريع البرمجية.

لديك قدرات خاصة:
- تحليل البنية المعمارية والأنماط البرمجية
- فهم التبعيات والعلاقات بين الوحدات
- تقييم جودة الكود وتحديد نقاط التحسين
- اكتشاف المشاكل المحتملة والثغرات
- تقديم توصيات مبنية على أفضل الممارسات

قم بتحليل السؤال بعمق واستخدم معرفتك ببنية المشروع لتقديم إجابة شاملة ودقيقة."""

    messages = [{"role": "system", "content": system_prompt}]

    if summary:
        context_msg = f"""**سياق المشروع:**

{summary}

---

الآن، بناءً على هذا السياق العميق للمشروع، أجب على السؤال التالي بدقة وشمولية:

{question}"""
        messages.append({"role": "user", "content": context_msg})
    else:
        messages.append({"role": "user", "content": question})

    # Step 3: Stream response from AI with enhanced context
    yield "💡 **التحليل:**\n\n"

    try:
        async for chunk in ai_client.stream_chat(messages):
            if isinstance(chunk, dict):
                choices = chunk.get("choices", [])
                if choices:
                    content = choices[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
            elif isinstance(chunk, str):
                yield chunk
    except Exception as e:
        yield f"\n\n❌ خطأ في التحليل: {ErrorSanitizer.sanitize(str(e))}\n"

    logger.debug(f"Deep analysis completed in {(time.time() - start_time) * 1000:.2f}ms")


async def handle_mission(
    context: ChatContext,
    objective: str,
    user_id: int,
    conversation_id: int,
) -> AsyncGenerator[str, None]:
    """Handle complex mission request with Overmind and polling."""
    start_time = time.time()

    allowed, msg = await context.check_rate_limit(user_id, "mission")
    if not allowed:
        yield f"⚠️ {msg}\n"
        return

    circuit = get_circuit_breaker("mission")
    can_execute, circuit_msg = circuit.can_execute()
    if not can_execute:
        yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
        return

    yield "🚀 **إنشاء مهمة Overmind**\n\n"
    yield f"**الهدف:** {objective[:150]}{'...' if len(objective) > 150 else ''}\n\n"

    if not context.async_overmind or not context.async_overmind.available:
        yield "⚠️ نظام Overmind غير متاح.\n"
        yield "سأحاول المساعدة بدون تنفيذ المهام التلقائية.\n\n"
        return

    yield "⏳ جارٍ إنشاء المهمة...\n\n"

    try:
        async with asyncio.timeout(15):
            result = await context.async_overmind.start_mission(
                objective=objective, user_id=user_id
            )
        circuit.record_success()
    except TimeoutError:
        circuit.record_failure()
        yield "⏱️ انتهت المهلة أثناء إنشاء المهمة.\n"
        return
    except Exception as e:
        circuit.record_failure()
        yield f"❌ خطأ: {ErrorSanitizer.sanitize(str(e))}\n"
        return

    if not result.get("ok"):
        error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
        yield f"❌ فشل إنشاء المهمة: {error}\n"
        return

    mission_id = result.get("mission_id")
    yield f"✅ تم إنشاء المهمة #{mission_id}\n"
    yield f"📋 الحالة: {result.get('status', 'pending')}\n\n"

    # Link mission to conversation
    await _link_mission_to_conversation(conversation_id, mission_id)

    # Mission Polling
    yield "📊 **متابعة تقدم المهمة:**\n\n"
    poll_count = 0
    max_polls = 15
    poll_interval = 2

    try:
        while poll_count < max_polls:
            await asyncio.sleep(poll_interval)
            poll_count += 1

            try:
                status_result = await context.async_overmind.get_mission_status(mission_id)
            except Exception:
                break

            if not status_result.get("ok"):
                break

            status = status_result.get("status", "unknown")
            tasks = status_result.get("tasks", {})
            is_terminal = status_result.get("is_terminal", False)

            task_info = ""
            if tasks:
                total = tasks.get("total", 0)
                success = tasks.get("success", 0)
                running = tasks.get("running", 0)
                failed = tasks.get("failed", 0)
                task_info = f" | المهام: {success}/{total} ✅"
                if running:
                    task_info += f" {running} 🔄"
                if failed:
                    task_info += f" {failed} ❌"

            status_emoji = {
                "pending": "⏳",
                "planning": "📋",
                "planned": "📝",
                "running": "🔄",
                "adapting": "🔧",
                "success": "✅",
                "failed": "❌",
                "canceled": "🚫",
            }.get(status, "❓")

            yield f"{status_emoji} الحالة: **{status}**{task_info}\n"

            if is_terminal:
                yield f"\n🏁 **انتهت المهمة بحالة: {status}**\n"
                break

    except asyncio.CancelledError:
        yield "\n⚠️ تم إلغاء المتابعة.\n"

    if poll_count >= max_polls:
        yield "\nℹ️ المهمة تعمل في الخلفية. يمكنك متابعة حالتها من لوحة التحكم.\n"

    logger.debug(f"mission handler completed in {(time.time() - start_time) * 1000:.2f}ms")


async def _link_mission_to_conversation(conversation_id: int, mission_id: int):
    """
    Link mission to conversation for tracking.

    Note: Imports are inside method to prevent circular imports.
    This is intentional as this service is loaded early in the app lifecycle.
    """
    try:
        # Lazy imports to prevent circular dependencies - this is intentional
        from app.core.database import SessionLocal
        from app.models import AdminConversation
        from app.services.async_tool_bridge import run_sync_tool

        def _update():
            session = SessionLocal()
            try:
                conv = session.get(AdminConversation, conversation_id)
                if conv and hasattr(conv, "linked_mission_id"):
                    conv.linked_mission_id = mission_id
                    session.commit()
                    return True
            except Exception as e:
                logger.warning(f"Failed to link mission to conversation: {e}")
                session.rollback()
            finally:
                session.close()
            return False

        await run_sync_tool(_update, timeout=5.0)
    except Exception as e:
        logger.warning(f"Failed to link mission {mission_id} to conv {conversation_id}: {e}")
