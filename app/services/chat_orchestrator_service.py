# app/services/chat_orchestrator_service.py
"""
CHAT ORCHESTRATOR SERVICE V3.0 — DEEP INTEGRATION EDITION
==========================================================

Bridges Admin Chat with Master Agent Overmind System.
Implements all safety measures and async patterns.

CRITICAL ARCHITECTURE:
1. All sync tools called via AsyncAgentTools (run_in_executor)
2. User passed as user_id (int), never as ORM object
3. Rate limiting on all tool executions
4. Timeout protection with asyncio.timeout
5. Graceful degradation when services unavailable
6. Error sanitization to prevent info leakage

SECURITY FIXES APPLIED:
✅ run_in_executor for all sync operations (no event loop blocking)
✅ Pass user_id instead of User objects (no session detachment)
✅ Proper async wrappers for sync tools via async_tool_bridge
✅ Rate limiting for tool execution
✅ Path validation before tool execution
✅ Error message sanitization
✅ Lazy imports to prevent circular dependencies
✅ Graceful degradation with LLM fallback
✅ Improved regex patterns with fewer false positives
✅ Timeout support for long-running operations
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from app.core.ai_gateway import AIClient

logger = logging.getLogger(__name__)


# =============================================================================
# INTENT DETECTION
# =============================================================================
class ChatIntent(Enum):
    """Detected intent for chat message."""

    SIMPLE_CHAT = "simple"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_SEARCH = "code_search"
    PROJECT_INDEX = "project_index"
    MISSION_COMPLEX = "mission"
    HELP = "help"


@dataclass
class IntentResult:
    """Result of intent detection."""

    intent: ChatIntent
    confidence: float
    params: dict[str, Any]
    reasoning: str


class IntentDetector:
    """
    Enhanced intent detection with improved patterns.
    Supports Arabic and English.
    """

    # File path regex - handles quotes, spaces, relative paths
    _PATH_PATTERN = r"['\"]?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)['\"]?"

    # Intent patterns with named groups
    PATTERNS: ClassVar[dict[ChatIntent, list[str]]] = {
        ChatIntent.FILE_READ: [
            # English
            rf"(?:read|show|display|view|cat|open|get)\s+(?:file\s+)?{_PATH_PATTERN}",
            rf"(?:what(?:'s| is) (?:in|inside))\s+{_PATH_PATTERN}",
            # Arabic
            rf"(?:اقرأ|اعرض|أظهر|افتح)\s+(?:ملف\s+)?{_PATH_PATTERN}",
            rf"(?:ما (?:محتوى|محتويات))\s+{_PATH_PATTERN}",
        ],
        ChatIntent.FILE_WRITE: [
            # English
            rf"(?:write|create|make|generate|save)\s+(?:a\s+)?(?:file\s+)?{_PATH_PATTERN}",
            rf"(?:create|make)\s+(?:new\s+)?{_PATH_PATTERN}",
            # Arabic
            rf"(?:أنشئ|اكتب|أضف|احفظ)\s+(?:ملف\s+)?{_PATH_PATTERN}",
        ],
        ChatIntent.CODE_SEARCH: [
            # English
            r"(?:find|search|look for|where is|locate)\s+(?:code\s+)?(?:for\s+)?['\"]?(.+?)['\"]?(?:\s+in|\s*$)",
            r"(?:search|grep)\s+(.+)",
            # Arabic
            r"(?:ابحث عن|أين|أوجد|جد)\s+(.+)",
        ],
        ChatIntent.PROJECT_INDEX: [
            # English
            r"(?:index|scan|analyze)\s+(?:the\s+)?(?:project|codebase|repository)",
            r"(?:show|list)\s+(?:project\s+)?(?:structure|files|overview)",
            # Arabic
            r"(?:فهرس|حلل|امسح)\s+(?:المشروع|الكود)",
            r"(?:أظهر|اعرض)\s+(?:هيكل|بنية)\s+المشروع",
        ],
        ChatIntent.MISSION_COMPLEX: [
            # English
            r"(?:analyze|refactor|fix|improve|optimize|implement|debug)\s+(?:the\s+)?(?:project|codebase|system|architecture|code)",
            r"(?:create|start|begin)\s+(?:a\s+)?mission\s+(?:to\s+)?(.+)",
            # Arabic
            r"(?:حلل|أصلح|حسّن|طور|نفذ)\s+(?:المشروع|الكود|النظام)",
            r"(?:أنشئ|ابدأ)\s+مهمة\s+(.+)",
        ],
        ChatIntent.HELP: [
            r"(?:help|what can you do|capabilities|commands)",
            r"(?:مساعدة|ماذا تستطيع|قدراتك|الأوامر)",
        ],
    }

    @classmethod
    def detect(cls, text: str) -> IntentResult:
        """Detect intent from text."""
        text_clean = text.strip()

        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_clean, re.IGNORECASE | re.UNICODE)
                if match:
                    # Extract parameter from first capture group
                    param = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                    param = param.strip().strip("'\"")

                    params: dict[str, Any] = {}
                    if intent == ChatIntent.FILE_READ or intent == ChatIntent.FILE_WRITE:
                        params["path"] = param
                    elif intent == ChatIntent.CODE_SEARCH:
                        params["query"] = param
                    elif intent == ChatIntent.MISSION_COMPLEX:
                        params["objective"] = text_clean

                    return IntentResult(
                        intent=intent,
                        confidence=0.9,
                        params=params,
                        reasoning=f"Matched pattern for {intent.value}",
                    )

        # Default to simple chat
        return IntentResult(
            intent=ChatIntent.SIMPLE_CHAT,
            confidence=0.7,
            params={},
            reasoning="No specific pattern matched",
        )


# =============================================================================
# PATH VALIDATION
# =============================================================================
class PathValidator:
    """Validates file paths to prevent traversal attacks."""

    BLOCKED_PATTERNS: ClassVar[list[str]] = [
        r"\.\./",  # Parent directory
        r"\.\.\\",  # Windows parent
        r"^/",  # Absolute Unix
        r"^[A-Za-z]:",  # Windows drive
        r"~",  # Home directory
        r"\x00",  # Null byte
    ]

    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {
        ".py",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".sh",
        ".sql",
        ".toml",
        ".cfg",
        ".ini",
        ".env.example",
    }

    @classmethod
    def validate(cls, path: str) -> tuple[bool, str]:
        """
        Validate a file path.

        Returns:
            (valid: bool, reason: str)
        """
        if not path or len(path) > 500:
            return False, "Invalid path length"

        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, path):
                return False, "Path contains blocked pattern"

        # Check extension using pathlib for proper handling of compound extensions
        from pathlib import Path

        path_obj = Path(path)
        suffixes = path_obj.suffixes  # Gets all suffixes like ['.tar', '.gz']
        if suffixes:
            # Check all suffixes (handles .tar.gz, .env.example, etc.)
            ext = suffixes[-1].lower()  # Last suffix
            full_ext = "".join(s.lower() for s in suffixes)  # Full compound extension

            # Allow if either the last extension or full compound extension is allowed
            if ext not in cls.ALLOWED_EXTENSIONS and full_ext not in cls.ALLOWED_EXTENSIONS:
                return False, f"Extension not allowed: {ext}"

        return True, "ok"


# =============================================================================
# ERROR SANITIZER
# =============================================================================
class ErrorSanitizer:
    """Sanitizes error messages to prevent information leakage."""

    PATTERNS_TO_REMOVE: ClassVar[list[tuple[str, str]]] = [
        (r"/[a-zA-Z0-9_/.-]+\.py", "[file]"),
        (r"line \d+", "line [N]"),
        (r"at 0x[a-fA-F0-9]+", "at [addr]"),
        (r"password['\"]?\s*[:=]\s*['\"]?[^'\"]+['\"]?", "password=[REDACTED]"),
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[^'\"]+['\"]?", "api_key=[REDACTED]"),
    ]

    @classmethod
    def sanitize(cls, error: str, max_length: int = 200) -> str:
        """Sanitize an error message."""
        if not error:
            return "Unknown error"

        result = str(error)

        for pattern, replacement in cls.PATTERNS_TO_REMOVE:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        if len(result) > max_length:
            result = result[:max_length] + "..."

        return result


# =============================================================================
# CHAT ORCHESTRATOR
# =============================================================================
class ChatOrchestratorService:
    """
    Main orchestration service for chat + Overmind integration.
    Thread-safe, async-native, with full safety measures.
    """

    def __init__(self):
        self._async_tools = None
        self._async_overmind = None
        self._rate_limiter = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization to prevent circular imports."""
        if self._initialized:
            return

        try:
            from app.services.async_tool_bridge import get_async_overmind, get_async_tools

            self._async_tools = get_async_tools()
            self._async_overmind = get_async_overmind()
        except ImportError as e:
            logger.warning(f"Failed to load async bridges: {e}")

        try:
            from app.core.rate_limiter import get_rate_limiter

            self._rate_limiter = get_rate_limiter()
        except ImportError as e:
            logger.warning(f"Failed to load rate limiter: {e}")

        self._initialized = True

    def detect_intent(self, text: str) -> IntentResult:
        """Detect intent from user message."""
        return IntentDetector.detect(text)

    async def _check_rate_limit(self, user_id: int, tool_name: str) -> tuple[bool, str]:
        """Check rate limit for tool execution."""
        if not self._rate_limiter:
            return True, "ok"
        return self._rate_limiter.check(user_id, tool_name)

    # -------------------------------------------------------------------------
    # HANDLER: FILE READ
    # -------------------------------------------------------------------------
    async def handle_file_read(
        self,
        path: str,
        user_id: int,
    ) -> AsyncGenerator[str, None]:
        """Handle file read request with full safety."""
        self._ensure_initialized()

        # Validate path
        valid, reason = PathValidator.validate(path)
        if not valid:
            yield f"❌ مسار غير صالح: {reason}\n"
            return

        # Check rate limit
        allowed, msg = await self._check_rate_limit(user_id, "read_file")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        yield f"📂 قراءة الملف: `{path}`\n\n"

        if not self._async_tools or not self._async_tools.available:
            yield "⚠️ أدوات القراءة غير متاحة حالياً.\n"
            return

        try:
            async with asyncio.timeout(15):
                result = await self._async_tools.read_file(path=path, max_bytes=50000)
        except TimeoutError:
            yield "⏱️ انتهت المهلة أثناء قراءة الملف.\n"
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
                # Determine language for syntax highlighting
                ext = path.split(".")[-1] if "." in path else ""
                lang = {"py": "python", "js": "javascript", "ts": "typescript"}.get(ext, ext)
                yield f"```{lang}\n{content}\n```\n"
                if truncated:
                    yield "\n⚠️ الملف طويل - تم عرض جزء منه فقط.\n"
        else:
            error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
            yield f"❌ خطأ: {error}\n"

    # -------------------------------------------------------------------------
    # HANDLER: CODE SEARCH
    # -------------------------------------------------------------------------
    async def handle_code_search(
        self,
        query: str,
        user_id: int,
    ) -> AsyncGenerator[str, None]:
        """Handle code search request."""
        self._ensure_initialized()

        if len(query) < 2:
            yield "⚠️ استعلام البحث قصير جداً.\n"
            return

        if len(query) > 200:
            yield "⚠️ استعلام البحث طويل جداً.\n"
            return

        # Check rate limit
        allowed, msg = await self._check_rate_limit(user_id, "code_search")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        yield f"🔍 البحث عن: `{query}`\n\n"

        if not self._async_tools or not self._async_tools.available:
            yield "⚠️ أدوات البحث غير متاحة حالياً.\n"
            return

        try:
            async with asyncio.timeout(20):
                result = await self._async_tools.code_search_lexical(
                    query=query, limit=10, context_radius=3
                )
        except TimeoutError:
            yield "⏱️ انتهت المهلة أثناء البحث.\n"
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

    # -------------------------------------------------------------------------
    # HANDLER: MISSION
    # -------------------------------------------------------------------------
    async def handle_mission(
        self,
        objective: str,
        user_id: int,
        conversation_id: int,
    ) -> AsyncGenerator[str, None]:
        """Handle complex mission request with Overmind."""
        self._ensure_initialized()

        # Check rate limit (more restrictive for missions)
        allowed, msg = await self._check_rate_limit(user_id, "mission")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        yield "🚀 **إنشاء مهمة Overmind**\n\n"
        yield f"**الهدف:** {objective[:150]}{'...' if len(objective) > 150 else ''}\n\n"

        if not self._async_overmind or not self._async_overmind.available:
            yield "⚠️ نظام Overmind غير متاح.\n"
            yield "سأحاول المساعدة بدون تنفيذ المهام التلقائية.\n\n"
            return

        yield "⏳ جارٍ إنشاء المهمة...\n\n"

        try:
            # Create mission with timeout
            async with asyncio.timeout(15):
                result = await self._async_overmind.start_mission(
                    objective=objective, user_id=user_id
                )
        except TimeoutError:
            yield "⏱️ انتهت المهلة أثناء إنشاء المهمة.\n"
            return

        if not result.get("ok"):
            error = ErrorSanitizer.sanitize(result.get("error", "خطأ غير معروف"))
            yield f"❌ فشل إنشاء المهمة: {error}\n"
            return

        mission_id = result.get("mission_id")
        yield f"✅ تم إنشاء المهمة #{mission_id}\n"
        yield f"📋 الحالة: {result.get('status', 'pending')}\n\n"
        yield "ℹ️ المهمة تعمل في الخلفية. يمكنك متابعة حالتها من لوحة التحكم.\n"

    # -------------------------------------------------------------------------
    # HANDLER: HELP
    # -------------------------------------------------------------------------
    async def handle_help(self) -> AsyncGenerator[str, None]:
        """Show available commands."""
        yield """
## 🧠 Overmind CLI Mindgate - الأوامر المتاحة

### 📂 قراءة الملفات
- `read app/models.py` - قراءة محتوى ملف
- `اقرأ app/main.py` - (بالعربية)

### 🔍 البحث في الكود
- `search AdminMessage` - البحث عن كلمة في الكود
- `ابحث عن SessionLocal` - (بالعربية)

### 🚀 المهام المعقدة
- `analyze the project` - تحليل المشروع
- `حلل المشروع` - (بالعربية)

### 💬 الدردشة العادية
أي سؤال آخر سيتم الرد عليه بواسطة الذكاء الاصطناعي.
"""

    # -------------------------------------------------------------------------
    # MAIN ORCHESTRATION
    # -------------------------------------------------------------------------
    async def orchestrate(
        self,
        question: str,
        user_id: int,
        conversation_id: int,
        ai_client: AIClient,
        history_messages: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """
        Main orchestration method.
        Routes to appropriate handler based on detected intent.
        Falls back to LLM for unhandled intents.
        """
        self._ensure_initialized()

        # Detect intent
        intent_result = self.detect_intent(question)

        logger.info(
            f"Intent: {intent_result.intent.value} "
            f"(confidence={intent_result.confidence:.2f}) "
            f"user={user_id}"
        )

        # Route based on intent
        if intent_result.intent == ChatIntent.FILE_READ:
            path = intent_result.params.get("path", "")
            if path:
                async for chunk in self.handle_file_read(path, user_id):
                    yield chunk
                return

        elif intent_result.intent == ChatIntent.CODE_SEARCH:
            query = intent_result.params.get("query", "")
            if query:
                async for chunk in self.handle_code_search(query, user_id):
                    yield chunk
                return

        elif intent_result.intent == ChatIntent.MISSION_COMPLEX:
            async for chunk in self.handle_mission(question, user_id, conversation_id):
                yield chunk
            # If Overmind not available, continue to LLM
            if self._async_overmind and self._async_overmind.available:
                return

        elif intent_result.intent == ChatIntent.HELP:
            async for chunk in self.handle_help():
                yield chunk
            return

        # Default: Simple LLM chat
        async for chunk in ai_client.stream_chat(history_messages):
            if isinstance(chunk, dict):
                choices = chunk.get("choices", [])
                if choices:
                    content = choices[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
            elif isinstance(chunk, str):
                yield chunk


# Singleton
_orchestrator = ChatOrchestratorService()


def get_chat_orchestrator() -> ChatOrchestratorService:
    return _orchestrator
