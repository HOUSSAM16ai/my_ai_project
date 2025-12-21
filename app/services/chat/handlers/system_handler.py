from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator

from app.core.resilience import get_circuit_breaker
from app.services.chat.handlers.base import ChatContext
from app.services.chat.security import ErrorSanitizer

logger = logging.getLogger(__name__)


async def handle_project_index(
    context: ChatContext,
    user_id: int,
) -> AsyncGenerator[str, None]:
    """Handle project indexing/analysis request."""
    start_time = time.time()

    allowed, msg = await context.check_rate_limit(user_id, "project_index")
    if not allowed:
        yield f"⚠️ {msg}\n"
        return

    circuit = get_circuit_breaker("project_index")
    can_execute, circuit_msg = circuit.can_execute()
    if not can_execute:
        yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
        return

    yield "📊 **تحليل هيكل المشروع**\n\n"
    yield "⏳ جارٍ فهرسة الملفات...\n\n"

    if not context.async_tools or not context.async_tools.available:
        yield "⚠️ أدوات الفهرسة غير متاحة حالياً.\n"
        return

    try:
        async with asyncio.timeout(60):
            result = await context.async_tools.code_index_project(root=".", max_files=500)
        circuit.record_success()
    except TimeoutError:
        circuit.record_failure()
        yield "⏱️ انتهت المهلة أثناء فهرسة المشروع.\n"
        return
    except Exception as e:
        circuit.record_failure()
        yield f"❌ خطأ: {ErrorSanitizer.sanitize(str(e))}\n"
        return

    if result.get("ok"):
        data = result.get("data", {})
        total_files = data.get("total_files", 0)
        total_lines = data.get("total_lines", 0)
        languages = data.get("languages", {})
        structure = data.get("structure", [])

        yield "✅ **ملخص المشروع:**\n\n"
        yield f"- 📁 إجمالي الملفات: **{total_files}**\n"
        yield f"- 📝 إجمالي الأسطر: **{total_lines:,}**\n\n"

        if languages:
            yield "**اللغات المستخدمة:**\n"
            for lang, count in sorted(languages.items(), key=lambda x: -x[1])[:5]:
                yield f"- {lang}: {count} ملف\n"
            yield "\n"

        if structure:
            yield "**الهيكل الرئيسي:**\n```\n"
            for item in structure[:15]:
                yield f"{item}\n"
            if len(structure) > 15:
                yield f"... و {len(structure) - 15} عنصر آخر\n"
            yield "```\n"
    else:
        error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
        yield f"❌ خطأ: {error}\n"

    duration = (time.time() - start_time) * 1000
    yield f"\n⏱️ وقت التنفيذ: {duration:.0f}ms\n"
    logger.debug(f"project_index completed in {duration:.2f}ms")


async def handle_help() -> AsyncGenerator[str, None]:
    """Show available commands."""
    yield """
## 🧠 Overmind CLI Mindgate - الأوامر المتاحة

### 📂 قراءة الملفات
- `read app/models.py` - قراءة محتوى ملف
- `اقرأ app/main.py` - (بالعربية)

### 📝 كتابة الملفات
- `create file test.py` - إنشاء ملف جديد
- `أنشئ ملف example.txt` - (بالعربية)

### 🔍 البحث في الكود
- `search AdminMessage` - البحث عن كلمة في الكود
- `ابحث عن SessionLocal` - (بالعربية)

### 📊 تحليل المشروع
- `analyze the project` - فهرسة وتحليل المشروع
- `حلل المشروع` - (بالعربية)

### 🚀 المهام المعقدة
- `create mission to fix bugs` - إنشاء مهمة Overmind
- `أنشئ مهمة لتحسين الكود` - (بالعربية)

### 💬 الدردشة العادية
أي سؤال آخر سيتم الرد عليه بواسطة الذكاء الاصطناعي.

---
**ℹ️ نصائح:**
- استخدم مسارات نسبية للملفات (مثل: `app/models.py`)
- المهام المعقدة تُنفذ في الخلفية ويمكن متابعتها
"""
