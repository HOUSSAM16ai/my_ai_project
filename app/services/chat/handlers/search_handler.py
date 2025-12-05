from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncGenerator

from app.core.resilience import get_circuit_breaker
from app.services.chat.handlers.base import ChatContext
from app.services.chat.security import ErrorSanitizer

logger = logging.getLogger(__name__)


async def handle_code_search(
    context: ChatContext,
    query: str,
    user_id: int,
) -> AsyncGenerator[str, None]:
    """Handle code search request."""
    start_time = time.time()

    if len(query) < 2:
        yield "⚠️ استعلام البحث قصير جداً.\n"
        return

    if len(query) > 200:
        yield "⚠️ استعلام البحث طويل جداً.\n"
        return

    allowed, msg = await context.check_rate_limit(user_id, "code_search")
    if not allowed:
        yield f"⚠️ {msg}\n"
        return

    circuit = get_circuit_breaker("code_search")
    can_execute, circuit_msg = circuit.can_execute()
    if not can_execute:
        yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
        return

    yield f"🔍 البحث عن: `{query}`\n\n"

    if not context.async_tools or not context.async_tools.available:
        yield "⚠️ أدوات البحث غير متاحة حالياً.\n"
        return

    try:
        async with asyncio.timeout(20):
            result = await context.async_tools.code_search_lexical(
                query=query, limit=10, context_radius=3
            )
        circuit.record_success()
    except TimeoutError:
        circuit.record_failure()
        yield "⏱️ انتهت المهلة أثناء البحث.\n"
        return
    except Exception as e:
        circuit.record_failure()
        yield f"❌ خطأ: {ErrorSanitizer.sanitize(str(e))}\n"
        return

    if result.get("ok"):
        data = result.get("data", {})
        results = data.get("results", [])

        if not results:
            yield "لم يتم العثور على نتائج.\n"
        else:
            yield f"✅ تم العثور على {len(results)} نتيجة:\n\n"
            for i, r in enumerate(results[:5], 1):
                file_path = r.get("file", "unknown")
                line = r.get("line", 0)
                excerpt = r.get("match_line_excerpt", "")[:100]
                yield f"**{i}. `{file_path}:{line}`**\n```\n{excerpt}\n```\n\n"

            if len(results) > 5:
                yield f"... و {len(results) - 5} نتيجة أخرى.\n"
    else:
        error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
        yield f"❌ خطأ: {error}\n"

    logger.debug(f"code_search completed in {(time.time() - start_time) * 1000:.2f}ms")
