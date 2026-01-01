from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator

from app.core.resilience import get_circuit_breaker
from app.services.chat.handlers.base import ChatContext
from app.services.chat.security import ErrorSanitizer, PathValidator

logger = logging.getLogger(__name__)

async def handle_file_read(
    context: ChatContext,
    path: str,
    user_id: int,
) -> AsyncGenerator[str, None]:
    """Handle file read request with full safety."""
    start_time = time.time()

    valid, reason = PathValidator.validate(path)
    if not valid:
        yield f"❌ مسار غير صالح: {reason}\n"
        return

    allowed, msg = await context.check_rate_limit(user_id, "read_file")
    if not allowed:
        yield f"⚠️ {msg}\n"
        return

    circuit = get_circuit_breaker("read_file")
    can_execute, circuit_msg = circuit.can_execute()
    if not can_execute:
        yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
        return

    yield f"📂 قراءة الملف: `{path}`\n\n"

    if not context.async_tools or not context.async_tools.available:
        yield "⚠️ أدوات القراءة غير متاحة حالياً.\n"
        return

    try:
        async with asyncio.timeout(15):
            result = await context.async_tools.read_file(path=path, max_bytes=50000)
        circuit.record_success()
    except TimeoutError:
        circuit.record_failure()
        yield "⏱️ انتهت المهلة أثناء قراءة الملف.\n"
        return
    except Exception as e:
        circuit.record_failure()
        yield f"❌ خطأ: {ErrorSanitizer.sanitize(str(e))}\n"
        return

    if result.get("ok"):
        data = result.get("data", {})
        content = data.get("content", "")
        exists = data.get("exists", True)
        missing = data.get("missing", False)

        if missing or not exists:
            yield f"⚠️ الملف غير موجود: `{path}`\n"
        elif not content:
            yield f"📄 الملف فارغ: `{path}`\n"
        else:
            truncated = data.get("truncated", False)
            ext = path.split(".")[-1] if "." in path else ""
            lang = {"py": "python", "js": "javascript", "ts": "typescript"}.get(ext, ext)
            yield f"```{lang}\n{content}\n```\n"
            if truncated:
                yield "\n⚠️ الملف طويل - تم عرض جزء منه فقط.\n"
    else:
        error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
        yield f"❌ خطأ: {error}\n"

    logger.debug(f"read_file completed in {(time.time() - start_time) * 1000:.2f}ms")

async def handle_file_write(
    context: ChatContext,
    path: str,
    content: str,
    user_id: int,
) -> AsyncGenerator[str, None]:
    """Handle file write request with full safety."""
    start_time = time.time()

    valid, reason = PathValidator.validate(path)
    if not valid:
        yield f"❌ مسار غير صالح: {reason}\n"
        return

    allowed, msg = await context.check_rate_limit(user_id, "write_file")
    if not allowed:
        yield f"⚠️ {msg}\n"
        return

    circuit = get_circuit_breaker("write_file")
    can_execute, circuit_msg = circuit.can_execute()
    if not can_execute:
        yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
        return

    yield f"📝 كتابة الملف: `{path}`\n\n"

    if not context.async_tools or not context.async_tools.available:
        yield "⚠️ أدوات الكتابة غير متاحة حالياً.\n"
        return

    try:
        async with asyncio.timeout(15):
            result = await context.async_tools.write_file(path=path, content=content)
        circuit.record_success()
    except TimeoutError:
        circuit.record_failure()
        yield "⏱️ انتهت المهلة أثناء كتابة الملف.\n"
        return
    except Exception as e:
        circuit.record_failure()
        yield f"❌ خطأ: {ErrorSanitizer.sanitize(str(e))}\n"
        return

    if result.get("ok"):
        yield f"✅ تم إنشاء/تحديث الملف بنجاح: `{path}`\n"
        bytes_written = result.get("data", {}).get("bytes_written", len(content))
        yield f"📊 حجم الملف: {bytes_written} bytes\n"
    else:
        error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
        yield f"❌ خطأ: {error}\n"

    logger.debug(f"write_file completed in {(time.time() - start_time) * 1000:.2f}ms")
