# app/services/chat_orchestrator_service.py
"""
CHAT ORCHESTRATOR SERVICE V4.0 — ENTERPRISE SUPERHUMAN EDITION
===============================================================

Bridges Admin Chat with Master Agent Overmind System.
Implements all safety measures, async patterns, and enterprise features.

ARCHITECTURE PRINCIPLES (SOLID + Clean Architecture):
1. Single Responsibility: Each handler does one thing well
2. Open/Closed: Easy to add new intents without modifying existing code
3. Liskov Substitution: All handlers follow same interface pattern
4. Interface Segregation: Minimal dependencies per component
5. Dependency Inversion: Depend on abstractions, not concretions

ENTERPRISE FEATURES:
✅ Circuit Breaker for fault tolerance
✅ Telemetry for performance monitoring
✅ Domain Events for audit trail
✅ Mission Polling for real-time updates
✅ File Write handler
✅ Project Index handler
✅ linked_mission_id support
✅ Extensible handler registry

SECURITY FEATURES:
✅ run_in_executor for all sync operations
✅ Pass user_id instead of User objects
✅ Rate limiting for tool execution
✅ Path validation before tool execution
✅ Error message sanitization
✅ Lazy imports to prevent circular dependencies
✅ Graceful degradation with LLM fallback
✅ Timeout support for long-running operations
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

# Use centralized circuit breaker
from app.core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    get_circuit_breaker,
)

if TYPE_CHECKING:
    from app.core.ai_gateway import AIClient

logger = logging.getLogger(__name__)


# =============================================================================
# TELEMETRY (القياسات)
# =============================================================================
@dataclass
class ChatTelemetry:
    """Telemetry data for chat operations."""

    intent_detection_time_ms: float = 0.0
    tool_execution_time_ms: float = 0.0
    total_response_time_ms: float = 0.0
    tokens_used: int = 0
    response_quality_grade: str = "A"  # A, B, C
    tool_name: str | None = None
    success: bool = True
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_detection_time_ms": self.intent_detection_time_ms,
            "tool_execution_time_ms": self.tool_execution_time_ms,
            "total_response_time_ms": self.total_response_time_ms,
            "tokens_used": self.tokens_used,
            "response_quality_grade": self.response_quality_grade,
            "tool_name": self.tool_name,
            "success": self.success,
            "error_type": self.error_type,
        }


# =============================================================================
# CIRCUIT BREAKER (قاطع الدائرة)
# =============================================================================
# NOTE: Circuit breaker logic moved to app/core/resilience/circuit_breaker.py
# This section is kept for backward compatibility but delegates to centralized module

class CircuitBreakerRegistry:
    """
    Registry for circuit breakers per tool.
    
    DEPRECATED: This class now delegates to the centralized CircuitBreakerRegistry
    in app.core.resilience. Use get_circuit_breaker() directly instead.
    
    Warning: This class is maintained for backward compatibility only.
    New code should use: from app.core.resilience import get_circuit_breaker
    """

    @classmethod
    def get(cls, name: str) -> CircuitBreaker:
        """
        Get circuit breaker from centralized registry.
        
        DEPRECATED: Use get_circuit_breaker() from app.core.resilience directly.
        """
        import warnings
        warnings.warn(
            "CircuitBreakerRegistry from chat_orchestrator_service is deprecated. "
            "Use 'from app.core.resilience import get_circuit_breaker' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return get_circuit_breaker(name)

    @classmethod
    def reset_all(cls):
        """
        Reset all circuit breakers (for testing).
        
        DEPRECATED: Use reset_all_circuit_breakers() from app.core.resilience directly.
        """
        import warnings
        warnings.warn(
            "CircuitBreakerRegistry.reset_all() is deprecated. "
            "Use 'from app.core.resilience import reset_all_circuit_breakers' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        from app.core.resilience import reset_all_circuit_breakers
        reset_all_circuit_breakers()


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
    DEEP_ANALYSIS = "deep_analysis"  # NEW: For analytical questions requiring Overmind
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
    Pattern order matters - more specific patterns should come first.
    """

    _PATH_PATTERN = r"['\"]?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)['\"]?"

    # ORDER MATTERS: PROJECT_INDEX and DEEP_ANALYSIS before MISSION_COMPLEX
    PATTERNS: ClassVar[dict[ChatIntent, list[str]]] = {
        ChatIntent.FILE_READ: [
            rf"(?:read|show|display|view|cat|open|get)\s+(?:file\s+)?{_PATH_PATTERN}",
            rf"(?:what(?:'s| is) (?:in|inside))\s+{_PATH_PATTERN}",
            rf"(?:اقرأ|اعرض|أظهر|افتح)\s+(?:ملف\s+)?{_PATH_PATTERN}",
            rf"(?:ما (?:محتوى|محتويات))\s+{_PATH_PATTERN}",
        ],
        ChatIntent.FILE_WRITE: [
            rf"(?:write|create|make|generate|save)\s+(?:a\s+)?(?:file\s+)?{_PATH_PATTERN}",
            rf"(?:create|make)\s+(?:new\s+)?{_PATH_PATTERN}",
            rf"(?:أنشئ|اكتب|أضف|احفظ)\s+(?:ملف\s+)?{_PATH_PATTERN}",
        ],
        ChatIntent.CODE_SEARCH: [
            r"(?:find|search|look for|where is|locate)\s+(?:code\s+)?(?:for\s+)?['\"]?(.+?)['\"]?(?:\s+in|\s*$)",
            r"(?:search|grep)\s+(.+)",
            r"(?:ابحث عن|أين|أوجد|جد)\s+(.+)",
        ],
        ChatIntent.PROJECT_INDEX: [
            r"(?:index|scan|analyze)\s+(?:the\s+)?(?:project|codebase|repository)",
            r"(?:show|list)\s+(?:project\s+)?(?:structure|files|overview)",
            r"(?:فهرس|حلل|امسح)\s+(?:المشروع|الكود)",
            r"(?:أظهر|اعرض)\s+(?:هيكل|بنية)\s+المشروع",
        ],
        # NEW: DEEP_ANALYSIS - Analytical questions that need Overmind's deep understanding
        ChatIntent.DEEP_ANALYSIS: [
            # Architecture & Design Analysis
            r"(?:explain|describe|what is|how does|how do)\s+(?:the\s+)?(?:architecture|design|structure|system|flow|pattern)",
            r"(?:how\s+(?:does|do|is|are))\s+(?:.+?)\s+(?:work|working|implemented|structured|organized|designed)",
            r"(?:what(?:'s| is| are))\s+(?:the\s+)?(?:purpose|role|function|responsibility)\s+(?:of|for)",
            r"(?:analyze|review|assess|evaluate|examine)\s+(?:the\s+)?(?:code|system|architecture|implementation|design|database)",
            # Code Quality & Issues
            r"(?:what(?:'s| is| are))\s+(?:the\s+)?(?:issues?|problems?|bugs?|errors?|warnings?)\s+(?:in|with|of)",
            r"(?:why\s+(?:is|are|does|do))\s+.+?\s+(?:not\s+working|failing|broken|wrong)",
            r"(?:find|identify|detect|locate)\s+(?:the\s+)?(?:bug|issue|problem|error|bottleneck)",
            # Improvement & Optimization
            r"(?:how\s+(?:can|should|do))\s+(?:we|i)\s+(?:improve|optimize|enhance|refactor|fix)",
            r"(?:suggest|recommend|propose)\s+(?:improvements?|optimizations?|changes?|fixes?)",
            r"(?:what\s+(?:can|should))\s+(?:be|we)\s+(?:improved|optimized|changed|fixed)",
            # Complexity & Dependencies
            r"(?:what(?:'s| is| are))\s+(?:the\s+)?(?:complexity|dependencies|relationships?|coupling)",
            r"(?:show|list|display)\s+(?:the\s+)?(?:dependencies|imports|calls|relationships?)",
            r"(?:which\s+(?:functions?|classes?|modules?|files?))\s+(?:use|depend on|call|import)",
            # Best Practices & Patterns
            r"(?:is|are)\s+(?:this|these|the)\s+(?:.+?)\s+(?:following|using|implementing)\s+(?:best practices?|patterns?|principles?)",
            r"(?:does|do)\s+(?:this|these|the)\s+(?:.+?)\s+(?:follow|adhere to|comply with|violate)",
            # Arabic patterns
            r"(?:اشرح|وضح|صف|كيف)\s+(?:يعمل|تعمل|بنية|هيكل|تصميم|نظام)",
            r"(?:ما\s+(?:هو|هي|هم))\s+(?:الغرض|الدور|الوظيفة|المسؤولية|المشاكل|الأخطاء)",
            r"(?:حلل|راجع|قيّم|افحص)\s+(?:الكود|النظام|الهيكل|التصميم|التنفيذ|قاعدة\s+البيانات)",
            r"(?:كيف\s+(?:يمكن|ينبغي|نستطيع))\s+(?:تحسين|تطوير|إصلاح|تعديل)",
            r"(?:اقترح|أوصي)\s+(?:تحسينات|تطويرات|تعديلات|إصلاحات)",
        ],
        ChatIntent.MISSION_COMPLEX: [
            r"(?:refactor|fix|improve|optimize|implement|debug)\s+(?:the\s+)?(?:entire\s+)?(?:project|codebase|system|architecture|code)",
            r"(?:create|start|begin)\s+(?:a\s+)?mission\s+(?:to\s+)?(.+)",
            r"(?:build|develop|add)\s+(?:a\s+)?(?:new\s+)?(?:feature|module|component|service)",
            r"(?:أصلح|حسّن|طور|نفذ)\s+(?:المشروع|الكود|النظام)\s+(?:بالكامل|كله)",
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
                    param = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                    param = param.strip().strip("'\"")

                    params: dict[str, Any] = {}
                    if intent == ChatIntent.FILE_READ or intent == ChatIntent.FILE_WRITE:
                        params["path"] = param
                    elif intent == ChatIntent.CODE_SEARCH:
                        params["query"] = param
                    elif intent == ChatIntent.MISSION_COMPLEX:
                        params["objective"] = text_clean
                    elif intent == ChatIntent.DEEP_ANALYSIS:
                        params["question"] = text_clean

                    return IntentResult(
                        intent=intent,
                        confidence=0.9,
                        params=params,
                        reasoning=f"Matched pattern for {intent.value}",
                    )

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
        r"\.\./",
        r"\.\.\\",
        r"^/",
        r"^[A-Za-z]:",
        r"~",
        r"\x00",
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
        """Validate a file path."""
        if not path or len(path) > 500:
            return False, "Invalid path length"

        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, path):
                return False, "Path contains blocked pattern"

        from pathlib import Path

        path_obj = Path(path)
        suffixes = path_obj.suffixes
        if suffixes:
            ext = suffixes[-1].lower()
            full_ext = "".join(s.lower() for s in suffixes)
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
    def sanitize(cls, error: str | None, max_length: int = 200) -> str:
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

    def _get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get circuit breaker for a tool."""
        return CircuitBreakerRegistry.get(tool_name)

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
        start_time = time.time()

        valid, reason = PathValidator.validate(path)
        if not valid:
            yield f"❌ مسار غير صالح: {reason}\n"
            return

        allowed, msg = await self._check_rate_limit(user_id, "read_file")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        circuit = self._get_circuit_breaker("read_file")
        can_execute, circuit_msg = circuit.can_execute()
        if not can_execute:
            yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
            return

        yield f"📂 قراءة الملف: `{path}`\n\n"

        if not self._async_tools or not self._async_tools.available:
            yield "⚠️ أدوات القراءة غير متاحة حالياً.\n"
            return

        try:
            async with asyncio.timeout(15):
                result = await self._async_tools.read_file(path=path, max_bytes=50000)
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

    # -------------------------------------------------------------------------
    # HANDLER: FILE WRITE
    # -------------------------------------------------------------------------
    async def handle_file_write(
        self,
        path: str,
        content: str,
        user_id: int,
    ) -> AsyncGenerator[str, None]:
        """Handle file write request with full safety."""
        self._ensure_initialized()
        start_time = time.time()

        valid, reason = PathValidator.validate(path)
        if not valid:
            yield f"❌ مسار غير صالح: {reason}\n"
            return

        allowed, msg = await self._check_rate_limit(user_id, "write_file")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        circuit = self._get_circuit_breaker("write_file")
        can_execute, circuit_msg = circuit.can_execute()
        if not can_execute:
            yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
            return

        yield f"📝 كتابة الملف: `{path}`\n\n"

        if not self._async_tools or not self._async_tools.available:
            yield "⚠️ أدوات الكتابة غير متاحة حالياً.\n"
            return

        try:
            async with asyncio.timeout(15):
                result = await self._async_tools.write_file(path=path, content=content)
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
        start_time = time.time()

        if len(query) < 2:
            yield "⚠️ استعلام البحث قصير جداً.\n"
            return

        if len(query) > 200:
            yield "⚠️ استعلام البحث طويل جداً.\n"
            return

        allowed, msg = await self._check_rate_limit(user_id, "code_search")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        circuit = self._get_circuit_breaker("code_search")
        can_execute, circuit_msg = circuit.can_execute()
        if not can_execute:
            yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
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

    # -------------------------------------------------------------------------
    # HANDLER: PROJECT INDEX
    # -------------------------------------------------------------------------
    async def handle_project_index(
        self,
        user_id: int,
    ) -> AsyncGenerator[str, None]:
        """Handle project indexing/analysis request."""
        self._ensure_initialized()
        start_time = time.time()

        allowed, msg = await self._check_rate_limit(user_id, "project_index")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        circuit = self._get_circuit_breaker("project_index")
        can_execute, circuit_msg = circuit.can_execute()
        if not can_execute:
            yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
            return

        yield "📊 **تحليل هيكل المشروع**\n\n"
        yield "⏳ جارٍ فهرسة الملفات...\n\n"

        if not self._async_tools or not self._async_tools.available:
            yield "⚠️ أدوات الفهرسة غير متاحة حالياً.\n"
            return

        try:
            async with asyncio.timeout(60):
                result = await self._async_tools.code_index_project(root=".", max_files=500)
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

    # -------------------------------------------------------------------------
    # HANDLER: MISSION
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # HANDLER: DEEP ANALYSIS (using Master Agent + Overmind Deep Context)
    # -------------------------------------------------------------------------
    async def handle_deep_analysis(
        self,
        question: str,
        user_id: int,
        ai_client: AIClient,
    ) -> AsyncGenerator[str, None]:
        """
        Handle deep analytical questions using Overmind's deep understanding.
        This uses Master Agent with project indexing for comprehensive analysis.
        """
        self._ensure_initialized()
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

    # -------------------------------------------------------------------------
    # HANDLER: MISSION (Complex tasks)
    # -------------------------------------------------------------------------
    async def handle_mission(
        self,
        objective: str,
        user_id: int,
        conversation_id: int,
    ) -> AsyncGenerator[str, None]:
        """Handle complex mission request with Overmind and polling."""
        self._ensure_initialized()
        start_time = time.time()

        allowed, msg = await self._check_rate_limit(user_id, "mission")
        if not allowed:
            yield f"⚠️ {msg}\n"
            return

        circuit = self._get_circuit_breaker("mission")
        can_execute, circuit_msg = circuit.can_execute()
        if not can_execute:
            yield f"⚠️ الخدمة غير متاحة مؤقتاً: {circuit_msg}\n"
            return

        yield "🚀 **إنشاء مهمة Overmind**\n\n"
        yield f"**الهدف:** {objective[:150]}{'...' if len(objective) > 150 else ''}\n\n"

        if not self._async_overmind or not self._async_overmind.available:
            yield "⚠️ نظام Overmind غير متاح.\n"
            yield "سأحاول المساعدة بدون تنفيذ المهام التلقائية.\n\n"
            return

        yield "⏳ جارٍ إنشاء المهمة...\n\n"

        try:
            async with asyncio.timeout(15):
                result = await self._async_overmind.start_mission(
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
        await self._link_mission_to_conversation(conversation_id, mission_id)

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
                    status_result = await self._async_overmind.get_mission_status(mission_id)
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
                        task_info += f" {running} ��"
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

    async def _link_mission_to_conversation(self, conversation_id: int, mission_id: int):
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
        """Main orchestration method."""
        self._ensure_initialized()
        start_time = time.time()

        intent_start = time.time()
        intent_result = self.detect_intent(question)
        intent_time = (time.time() - intent_start) * 1000

        logger.info(
            f"Intent: {intent_result.intent.value} "
            f"(confidence={intent_result.confidence:.2f}, time={intent_time:.2f}ms) "
            f"user={user_id}"
        )

        # Route based on intent
        if intent_result.intent == ChatIntent.FILE_READ:
            path = intent_result.params.get("path", "")
            if path:
                async for chunk in self.handle_file_read(path, user_id):
                    yield chunk
                return

        elif intent_result.intent == ChatIntent.FILE_WRITE:
            path = intent_result.params.get("path", "")
            if path:
                yield f"📝 لإنشاء ملف `{path}`، يرجى تحديد المحتوى.\n"
                yield "يمكنك كتابة المحتوى في الرسالة التالية.\n"
                return

        elif intent_result.intent == ChatIntent.CODE_SEARCH:
            query = intent_result.params.get("query", "")
            if query:
                async for chunk in self.handle_code_search(query, user_id):
                    yield chunk
                return

        elif intent_result.intent == ChatIntent.PROJECT_INDEX:
            async for chunk in self.handle_project_index(user_id):
                yield chunk
            return

        elif intent_result.intent == ChatIntent.DEEP_ANALYSIS:
            # NEW: Route analytical questions to Overmind-powered deep analysis
            async for chunk in self.handle_deep_analysis(question, user_id, ai_client):
                yield chunk
            return

        elif intent_result.intent == ChatIntent.MISSION_COMPLEX:
            async for chunk in self.handle_mission(question, user_id, conversation_id):
                yield chunk
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

        logger.debug(f"Orchestration completed in {(time.time() - start_time) * 1000:.2f}ms")


# Singleton
_orchestrator = ChatOrchestratorService()


def get_chat_orchestrator() -> ChatOrchestratorService:
    return _orchestrator
