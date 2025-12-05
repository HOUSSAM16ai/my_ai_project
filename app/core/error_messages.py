import os
import re


def build_bilingual_error_message(error: str, prompt_length: int, max_tokens: int) -> str:
    """
    Constructs a bilingual (Arabic/English) error message for LLM failures.
    Refactored from MaestroGenerationService to ensure Separation of Concerns.
    """
    error_lower = error.lower()

    if "timeout" in error_lower or "timed out" in error_lower:
        return (
            f"⏱️ **انتهت مهلة الانتظار** (Timeout)\n\n"
            f"**بالعربية:**\n"
            f"السؤال معقد جداً وتطلب وقتاً أطول من المتاح ({max_tokens:,} رمز).\n\n"
            f"**الحلول المقترحة:**\n"
            f"1. 🚀 فعّل الوضع الخارق (ULTIMATE MODE):\n"
            f"   قم بتعيين LLM_ULTIMATE_COMPLEXITY_MODE=1 في ملف .env\n"
            f"   هذا سيمنحك 30 دقيقة و 128K رمز و 20 محاولة!\n"
            f"2. 💪 أو فعّل الوضع الشديد (EXTREME MODE):\n"
            f"   قم بتعيين LLM_EXTREME_COMPLEXITY_MODE=1 في ملف .env\n"
            f"   هذا سيمنحك 10 دقائق و 64K رمز و 8 محاولات\n"
            f"3. أو قسّم السؤال إلى أجزاء أصغر\n"
            f"4. أو اطرح سؤالاً أكثر تحديداً\n\n"
            f"**English:**\n"
            f"Question is too complex and took longer than available time ({max_tokens:,} tokens).\n\n"
            f"**Suggested Solutions:**\n"
            f"1. 🚀 Enable ULTIMATE MODE:\n"
            f"   Set LLM_ULTIMATE_COMPLEXITY_MODE=1 in .env file\n"
            f"   This gives you 30 minutes, 128K tokens, and 20 retries!\n"
            f"2. 💪 Or enable EXTREME MODE:\n"
            f"   Set LLM_EXTREME_COMPLEXITY_MODE=1 in .env file\n"
            f"   This gives you 10 minutes, 64K tokens, and 8 retries\n"
            f"3. Or break the question into smaller parts\n"
            f"4. Or ask a more specific question\n\n"
            f"**Technical Details:**\n"
            f"- Prompt length: {prompt_length:,} characters\n"
            f"- Max tokens: {max_tokens:,}\n"
            f"- Error: {error}"
        )
    if "rate" in error_lower and "limit" in error_lower:
        return (
            f"🚦 **تم تجاوز حد الطلبات** (Rate Limit)\n\n"
            f"**بالعربية:**\n"
            f"تم إرسال عدد كبير من الطلبات في فترة قصيرة.\n\n"
            f"**الحل:**\n"
            f"انتظر بضع ثوانٍ ثم حاول مرة أخرى.\n\n"
            f"**English:**\n"
            f"Too many requests sent in a short period.\n\n"
            f"**Solution:**\n"
            f"Wait a few seconds and try again.\n\n"
            f"**Technical Details:**\n"
            f"- Error: {error}"
        )
    if "context" in error_lower or ("length" in error_lower and "token" in error_lower):
        return (
            f"📏 **السياق طويل جداً** (Context Length Error)\n\n"
            f"**بالعربية:**\n"
            f"السؤال أو تاريخ المحادثة طويل جداً ({prompt_length:,} حرف).\n\n"
            f"**الحلول:**\n"
            f"1. 🚀 للأسئلة الطويلة جداً: فعّل ULTIMATE MODE\n"
            f"   قم بتعيين LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
            f"   يدعم حتى 500K حرف!\n"
            f"2. ابدأ محادثة جديدة\n"
            f"3. اطرح سؤالاً أقصر\n"
            f"4. قلل من السياق المرفق\n\n"
            f"**English:**\n"
            f"Question or conversation history is too long ({prompt_length:,} characters).\n\n"
            f"**Solutions:**\n"
            f"1. 🚀 For very long questions: Enable ULTIMATE MODE\n"
            f"   Set LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
            f"   Supports up to 500K characters!\n"
            f"2. Start a new conversation\n"
            f"3. Ask a shorter question\n"
            f"4. Reduce the attached context\n\n"
            f"**Technical Details:**\n"
            f"- Prompt length: {prompt_length:,} characters\n"
            f"- Max tokens: {max_tokens:,}\n"
            f"- Error: {error}"
        )
    if "api key" in error_lower or "auth" in error_lower or "unauthorized" in error_lower:
        return (
            f"🔑 **خطأ في المصادقة** (Authentication Error)\n\n"
            f"**بالعربية:**\n"
            f"هناك مشكلة في مفتاح API أو المصادقة.\n\n"
            f"**الحل:**\n"
            f"تواصل مع مسؤول النظام للتحقق من إعدادات API.\n\n"
            f"**English:**\n"
            f"There is a problem with the API key or authentication.\n\n"
            f"**Solution:**\n"
            f"Contact the system administrator to verify API settings.\n\n"
            f"**Technical Details:**\n"
            f"- Error: {error}"
        )
    if (
        "500" in error_lower
        or re.search(r"\bserver\b", error_lower)
        or "server_error" in error_lower
    ):
        ultimate_active = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"
        extreme_active = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"

        mode_status = ""
        if ultimate_active:
            mode_status = "🚀 ULTIMATE MODE نشط | ULTIMATE MODE Active\n"
        elif extreme_active:
            mode_status = "💪 EXTREME MODE نشط | EXTREME MODE Active\n"

        return (
            f"🔴 **خطأ في الخادم** (Server Error 500)\n\n"
            f"{mode_status}"
            f"**بالعربية:**\n"
            f"حدث خطأ في خادم الذكاء الاصطناعي (OpenRouter/OpenAI).\n\n"
            f"**الأسباب المحتملة:**\n"
            f"1. مفتاح API غير صالح أو منتهي الصلاحية\n"
            f"2. مشكلة مؤقتة في خدمة الذكاء الاصطناعي\n"
            f"3. السؤال يحتوي على محتوى غير مسموح\n"
            f"4. تجاوز حد الاستخدام أو الرصيد\n\n"
            f"**الحلول المقترحة:**\n"
            f"1. تحقق من صلاحية مفتاح API في ملف .env\n"
            f"2. تأكد من وجود رصيد كافٍ في حساب OpenRouter/OpenAI\n"
            f"3. 🚀 إذا لم يكن نشطاً، فعّل ULTIMATE MODE للتغلب على المشكلة:\n"
            f"   LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
            f"4. حاول مرة أخرى بعد بضع دقائق\n"
            f"5. إذا استمرت المشكلة، راجع سجلات الخادم (docker-compose logs web)\n\n"
            f"**English:**\n"
            f"An error occurred in the AI server (OpenRouter/OpenAI).\n\n"
            f"**Possible Causes:**\n"
            f"1. Invalid or expired API key\n"
            f"2. Temporary issue with the AI service\n"
            f"3. Question contains prohibited content\n"
            f"4. Usage limit or credit exceeded\n\n"
            f"**Suggested Solutions:**\n"
            f"1. Verify API key validity in .env file\n"
            f"2. Ensure sufficient credit in OpenRouter/OpenAI account\n"
            f"3. 🚀 If not active, enable ULTIMATE MODE to overcome the issue:\n"
            f"   LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
            f"4. Try again in a few minutes\n"
            f"5. If problem persists, check server logs (docker-compose logs web)\n\n"
            f"**Technical Details:**\n"
            f"- Prompt length: {prompt_length:,} characters\n"
            f"- Max tokens: {max_tokens:,}\n"
            f"- Error: {error}"
        )
    if error == "no_response":
        return (
            f"❌ **لم يتم استلام رد** (No Response)\n\n"
            f"**بالعربية:**\n"
            f"النظام لم يتمكن من توليد إجابة للسؤال.\n\n"
            f"**الحلول:**\n"
            f"1. أعد صياغة السؤال بشكل مختلف\n"
            f"2. تأكد من وضوح السؤال\n"
            f"3. حاول مرة أخرى\n\n"
            f"**English:**\n"
            f"The system could not generate an answer to the question.\n\n"
            f"**Solutions:**\n"
            f"1. Rephrase the question differently\n"
            f"2. Ensure the question is clear\n"
            f"3. Try again\n\n"
            f"**Technical Details:**\n"
            f"- Prompt length: {prompt_length:,} characters\n"
            f"- Max tokens: {max_tokens:,}"
        )
    return (
        f"⚠️ **حدث خطأ** (Error Occurred)\n\n"
        f"**بالعربية:**\n"
        f"حدث خطأ غير متوقع أثناء معالجة السؤال.\n\n"
        f"**الحلول:**\n"
        f"1. حاول مرة أخرى\n"
        f"2. تحقق من صياغة السؤال\n"
        f"3. إذا استمرت المشكلة، تواصل مع الدعم\n\n"
        f"**English:**\n"
        f"An unexpected error occurred while processing the question.\n\n"
        f"**Solutions:**\n"
        f"1. Try again\n"
        f"2. Check the question phrasing\n"
        f"3. If the problem persists, contact support\n\n"
        f"**Technical Details:**\n"
        f"- Prompt length: {prompt_length:,} characters\n"
        f"- Max tokens: {max_tokens:,}\n"
        f"- Error: {error}"
    )
