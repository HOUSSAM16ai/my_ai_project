"""صياغة رسائل الأخطاء بشكل موحّد ومفهوم للمبتدئين."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass


ServerErrorPredicate = Callable[["ErrorContext"], bool]
ServerErrorBuilder = Callable[["ErrorContext"], str]


@dataclass(frozen=True)
class ErrorContext:
    """سياق موحّد يضم بيانات الخطأ لتبسيط منطق المعالجة."""

    prompt_length: int
    max_tokens: int
    error: str

    @property
    def normalized_error(self) -> str:
        """يعيد نص الخطأ بحروف صغيرة لتسهيل المقارنة."""
        return self.error.lower()


SERVER_ERROR_GUIDANCE = (
    "**بالعربية:**\n"
    "حدث خطأ في خادم الذكاء الاصطناعي (OpenRouter/OpenAI).\n\n"
    "**الأسباب المحتملة:**\n"
    "1. مفتاح API غير صالح أو منتهي الصلاحية\n"
    "2. مشكلة مؤقتة في خدمة الذكاء الاصطناعي\n"
    "3. السؤال يحتوي على محتوى غير مسموح\n"
    "4. تجاوز حد الاستخدام أو الرصيد\n\n"
    "**الحلول المقترحة:**\n"
    "1. تحقق من صلاحية مفتاح API في ملف .env\n"
    "2. تأكد من وجود رصيد كافٍ في حساب OpenRouter/OpenAI\n"
    "3. 🚀 إذا لم يكن نشطاً، فعّل ULTIMATE MODE للتغلب على المشكلة:\n"
    "   LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
    "4. حاول مرة أخرى بعد بضع دقائق\n"
    "5. إذا استمرت المشكلة، راجع سجلات الخادم (docker-compose logs web)\n\n"
    "**English:**\n"
    "An error occurred in the AI server (OpenRouter/OpenAI).\n\n"
    "**Possible Causes:**\n"
    "1. Invalid or expired API key\n"
    "2. Temporary issue with the AI service\n"
    "3. Question contains prohibited content\n"
    "4. Usage limit or credit exceeded\n\n"
    "**Suggested Solutions:**\n"
    "1. Verify API key validity in .env file\n"
    "2. Ensure sufficient credit in OpenRouter/OpenAI account\n"
    "3. 🚀 If not active, enable ULTIMATE MODE to overcome the issue:\n"
    "   LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
    "4. Try again in a few minutes\n"
    "5. If problem persists, check server logs (docker-compose logs web)"
)


def _format_timeout_error(max_tokens: int) -> str:
    """يصوغ رسالة تجاوز المهلة للمستخدمين بالعربية والإنجليزية."""
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
        f"4. Or ask a more specific question"
    )

def _format_rate_limit_error(error: str) -> str:
    """يصوغ رسالة تجاوز حد الطلبات بطريقة واضحة."""
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

def _format_context_error(prompt_length: int, max_tokens: int, error: str) -> str:
    """يصوغ رسالة خطأ طول السياق مع اقتراحات مختصرة."""
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

def _format_auth_error(error: str) -> str:
    """يصوغ رسالة خطأ المصادقة بمستوى إرشاد للمبتدئين."""
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

def _format_server_error(prompt_length: int, max_tokens: int, error: str) -> str:
    """يبني رسالة خطأ الخادم 500 مع إبراز وضع ULTIMATE/EXTREME."""
    return (
        "🔴 **خطأ في الخادم** (Server Error 500)\n\n"
        f"{_server_mode_status()}"
        f"{SERVER_ERROR_GUIDANCE}"
        f"{_technical_details_block(prompt_length, max_tokens, error)}"
    )

def _format_no_response_error(prompt_length: int, max_tokens: int) -> str:
    """يصوغ رسالة عدم وجود استجابة مع حلول مختصرة."""
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

def _format_generic_error(prompt_length: int, max_tokens: int, error: str) -> str:
    """يصوغ رسالة خطأ عامة عند عدم تطابق أي حالة أخرى."""
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

def build_bilingual_error_message(error: str, prompt_length: int, max_tokens: int) -> str:
    """يجمع رسالة خطأ ثنائية اللغة عبر قواعد واضحة وبسيطة."""
    context = ErrorContext(prompt_length=prompt_length, max_tokens=max_tokens, error=error)

    for predicate, builder in ERROR_HANDLERS:
        if predicate(context):
            return builder(context)

    return _format_generic_error(prompt_length, max_tokens, error)


def _server_mode_status() -> str:
    """يحدّد نص حالة وضع ULTIMATE أو EXTREME لدعم المستخدم."""
    ultimate_active = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"
    extreme_active = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"

    if ultimate_active:
        return "🚀 ULTIMATE MODE نشط | ULTIMATE MODE Active\n"
    if extreme_active:
        return "💪 EXTREME MODE نشط | EXTREME MODE Active\n"
    return ""


def _technical_details_block(prompt_length: int, max_tokens: int, error: str) -> str:
    """يبني ملحق التفاصيل التقنية للحفاظ على الشفافية."""
    return (
        f"\n\n**Technical Details:**\n"
        f"- Prompt length: {prompt_length:,} characters\n"
        f"- Max tokens: {max_tokens:,}\n"
        f"- Error: {error}"
    )


def _is_timeout(context: ErrorContext) -> bool:
    """يتحقق من أخطاء المهلة الزمنية بسهولة القراءة."""
    error_lower = context.normalized_error
    return "timeout" in error_lower or "timed out" in error_lower


def _is_rate_limited(context: ErrorContext) -> bool:
    """يتحقق من رسائل تجاوز الحد."""
    error_lower = context.normalized_error
    return "rate" in error_lower and "limit" in error_lower


def _is_context_error(context: ErrorContext) -> bool:
    """يتحقق من أخطاء طول السياق."""
    error_lower = context.normalized_error
    return "context" in error_lower or ("length" in error_lower and "token" in error_lower)


def _is_auth_error(context: ErrorContext) -> bool:
    """يتحقق من أخطاء المصادقة ورفض الوصول."""
    error_lower = context.normalized_error
    return "api key" in error_lower or "auth" in error_lower or "unauthorized" in error_lower


def _is_server_error(context: ErrorContext) -> bool:
    """يتحقق من أخطاء الخادم 500 أو الرسائل المشابهة."""
    error_lower = context.normalized_error
    return (
        "500" in error_lower
        or re.search(r"\bserver\b", error_lower) is not None
        or "server_error" in error_lower
    )


def _is_empty_response(context: ErrorContext) -> bool:
    """يتحقق من حالة عدم وصول أي رد من النموذج."""
    return context.error == "no_response"


def _build_timeout_message(context: ErrorContext) -> str:
    """يبني رسالة أخطاء المهلة مع تفاصيل تقنية."""
    return _format_timeout_error(context.max_tokens) + _technical_details_block(
        context.prompt_length, context.max_tokens, context.error
    )


def _build_rate_limit_message(context: ErrorContext) -> str:
    """يبني رسالة تجاوز الحد."""
    return _format_rate_limit_error(context.error)


def _build_context_length_message(context: ErrorContext) -> str:
    """يبني رسالة طول السياق الزائد."""
    return _format_context_error(context.prompt_length, context.max_tokens, context.error)


def _build_auth_message(context: ErrorContext) -> str:
    """يبني رسالة أخطاء المصادقة."""
    return _format_auth_error(context.error)


def _build_server_error_message(context: ErrorContext) -> str:
    """يبني رسالة خطأ الخادم باستخدام المساعدات الجديدة."""
    return _format_server_error(context.prompt_length, context.max_tokens, context.error)


def _build_no_response_message(context: ErrorContext) -> str:
    """يبني رسالة توضح عدم وجود استجابة."""
    return _format_no_response_error(context.prompt_length, context.max_tokens)


ERROR_HANDLERS: tuple[tuple[ServerErrorPredicate, ServerErrorBuilder], ...] = (
    (_is_timeout, _build_timeout_message),
    (_is_rate_limited, _build_rate_limit_message),
    (_is_context_error, _build_context_length_message),
    (_is_auth_error, _build_auth_message),
    (_is_server_error, _build_server_error_message),
    (_is_empty_response, _build_no_response_message),
)
