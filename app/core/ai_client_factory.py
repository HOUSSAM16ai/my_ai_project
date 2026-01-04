"""
مصنع عملاء الذكاء الاصطناعي الموحد (Unified AI Client Factory).

يوفر هذا الملف طريقة موحدة لإنشاء وإدارة عملاء الذكاء الاصطناعي عبر التطبيق بأكمله.
يلغي التكرار ويوحد تكوين العميل وإدارة دورة حياته.

المسؤوليات (Responsibilities):
✅ نقطة واحدة لإنشاء عملاء الذكاء الاصطناعي
✅ إدارة التكوين (Configuration)
✅ دورة حياة العميل (Singleton Pattern)
✅ تجريد المزود (Provider Abstraction)

المبادئ (Principles):
- Factory Pattern: إنشاء العملاء بناءً على التكوين.
- Singleton Pattern: مثيل عميل واحد لكل تكوين.
- Strategy Pattern: مزودون مختلفون (OpenRouter, OpenAI, etc.).
- Harvard CS50 2025: توثيق عربي، صرامة الأنواع.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
import uuid
from typing import Protocol, runtime_checkable

# Import requests inside methods to allow late binding/patching
try:
    import requests
except ImportError:
    requests = None

from app.config.ai_models import get_ai_config

logger = logging.getLogger(__name__)

# Thread-safe singleton management
_CLIENT_LOCK = threading.Lock()
_CLIENT_CACHE: dict[str, object] = {}
_CLIENT_META: dict[str, dict[str, object]] = {}

@runtime_checkable
class AIClientProtocol(Protocol):
    """
    بروتوكول يحدد واجهة عملاء الذكاء الاصطناعي.
    """

    def chat(self) -> object:
        """يعيد واجهة المحادثة."""
        ...

    def meta(self) -> dict[str, object]:
        """يعيد بيانات وصفية عن العميل."""
        ...

class AIClientFactory:
    """
    المصنع الموحد لإنشاء عملاء الذكاء الاصطناعي.
    يعالج جميع منطق المزودين في مكان واحد.
    """

    @staticmethod
    def create_client(
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 180.0,
        use_cache: bool = True,
    ) -> object:
        """
        إنشاء أو استرجاع عميل ذكاء اصطناعي.

        Args:
            provider: اسم المزود (مثل 'openrouter', 'openai').
            api_key: مفتاح الواجهة البرمجية.
            base_url: الرابط الأساسي للواجهة.
            timeout: مهلة الطلب بالثواني.
            use_cache: استخدام التخزين المؤقت للعميل.

        Returns:
            object: مثيل عميل الذكاء الاصطناعي (أو Mock/Fallback).
        """
        provider, api_key, base_url = AIClientFactory._resolve_config(provider, api_key, base_url)

        if not api_key:
            logger.info("⚠️ No API key available, defaulting to mock client.")
            return AIClientFactory._create_mock_client("no-api-key")

        cache_key = AIClientFactory._generate_cache_key(provider, api_key, base_url)

        if use_cache:
            cached = AIClientFactory._get_from_cache(cache_key)
            if cached:
                return cached

        return AIClientFactory._create_and_cache(
            provider, api_key, base_url, timeout, cache_key, use_cache
        )

    @staticmethod
    def _resolve_config(
        provider: str | None, api_key: str | None, base_url: str | None
    ) -> tuple[str, str | None, str]:
        """حل إعدادات التكوين باستخدام القيم الافتراضية إذا لزم الأمر."""
        if not provider or not api_key:
            config = get_ai_config()
            provider = provider or "openrouter"
            api_key = api_key or config.openrouter_api_key
            base_url = base_url or "https://openrouter.ai/api/v1"
        return provider, api_key, base_url  # type: ignore

    @staticmethod
    def _generate_cache_key(provider: str, api_key: str, base_url: str) -> str:
        """توليد مفتاح تخزين مؤقت فريد."""
        api_key_hash = hashlib.sha256(api_key.encode() if api_key else b"none").hexdigest()[:16]
        return f"{provider}:{api_key_hash}:{base_url}"

    @staticmethod
    def _get_from_cache(cache_key: str) -> object | None:
        """استرجاع العميل من الذاكرة المؤقتة."""
        if cache_key in _CLIENT_CACHE:
            logger.debug(f"♻️ Returning cached client for {cache_key.split(':')[0]}")
            return _CLIENT_CACHE[cache_key]
        return None

    @staticmethod
    def _create_and_cache(
        provider: str,
        api_key: str,
        base_url: str,
        timeout: float,
        cache_key: str,
        use_cache: bool,
    ) -> object:
        """إنشاء وتخزين عميل جديد."""
        with _CLIENT_LOCK:
            # Double-check after acquiring lock
            if use_cache and cache_key in _CLIENT_CACHE:
                return _CLIENT_CACHE[cache_key]

            client = AIClientFactory._create_new_client(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )

            if use_cache:
                _CLIENT_CACHE[cache_key] = client
                _CLIENT_META[cache_key] = {
                    "provider": provider,
                    "created_at": time.time(),
                    "client_id": str(uuid.uuid4()),
                }

            logger.info(f"✨ Created new AI client for provider: {provider}")
            return client

    @staticmethod
    def _create_new_client(
        provider: str,
        api_key: str,
        base_url: str,
        timeout: float,
    ) -> object:
        """إنشاء مثيل عميل جديد بناءً على المزود."""
        try:
            # Try to use OpenAI SDK
            import openai

            client_kwargs = {
                "api_key": api_key,
                "base_url": base_url,
                "timeout": timeout,
            }

            client = openai.OpenAI(**client_kwargs)
            logger.info(f"✅ Created OpenAI SDK client for {provider}")
            return client

        except ImportError:
            logger.warning("⚠️ OpenAI SDK not available, using fallback")
            return AIClientFactory._create_fallback_client(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )
        except Exception as e:
            logger.error(f"❌ Failed to create client: {e}")
            return AIClientFactory._create_fallback_client(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )

    @staticmethod
    def _create_fallback_client(
        api_key: str,
        base_url: str,
        timeout: float,
    ) -> object:
        """إنشاء عميل احتياطي بسيط يعتمد على HTTP."""
        if requests is None:
            logger.error("❌ Requests library not available")
            return AIClientFactory._create_mock_client("no-requests")

        return SimpleFallbackClient(api_key, base_url, timeout)

    @staticmethod
    def _create_mock_client(reason: str) -> object:
        """إنشاء عميل وهمي للاختبار والتطوير."""
        return MockClient(reason)

    @staticmethod
    def clear_cache() -> None:
        """مسح ذاكرة التخزين المؤقت للعملاء."""
        with _CLIENT_LOCK:
            _CLIENT_CACHE.clear()
            _CLIENT_META.clear()
            logger.info("🧹 Client cache cleared")

    @staticmethod
    def get_cached_clients() -> dict[str, dict[str, object]]:
        """الحصول على معلومات حول العملاء المخزنين مؤقتاً."""
        return dict(_CLIENT_META)

class SimpleFallbackClient:
    """عميل HTTP بسيط لطلبات API."""

    def __init__(self, api_key: str, base_url: str, timeout: float):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._id = str(uuid.uuid4())
        self._created_at = time.time()

    class _ChatWrapper:
        def __init__(self, parent: SimpleFallbackClient):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent):
                self._parent = parent

            def create(self, model: str, messages: list[object], **kwargs) -> object:
                """إجراء مكالمة API باستخدام requests."""
                if requests is None:
                    raise RuntimeError("Requests library not available")

                headers = {
                    "Authorization": f"Bearer {self._parent._parent.api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": model,
                    "messages": messages,
                    **kwargs,
                }

                try:
                    response = requests.post(
                        f"{self._parent._parent.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=self._parent._parent.timeout,
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logger.error(f"❌ API call failed: {e}")
                    raise

        @property
        def completions(self) -> object:
            return self._CompletionsWrapper(self)

    @property
    def chat(self) -> object:
        return self._ChatWrapper(self)

    def meta(self) -> dict[str, object]:
        return {
            "client_id": self._id,
            "created_at": self._created_at,
            "type": "fallback",
        }

class MockClient:
    """عميل وهمي يعيد استجابات اصطناعية."""

    def __init__(self, reason: str):
        self.reason = reason
        self._id = str(uuid.uuid4())
        self._created_at = time.time()
        self._is_mock_client = True

    class _ChatWrapper:
        def __init__(self, parent: MockClient):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent):
                self._parent = parent

            def create(self, model: str, messages: list[object], **kwargs) -> object:
                """إعادة استجابة وهمية."""

                class _Message:
                    def __init__(self, content: str):
                        self.content = content
                        self.tool_calls = None

                class _Choice:
                    def __init__(self, message: _Message):
                        self.message = message
                        self.finish_reason = "stop"

                class _Response:
                    def __init__(self, choices: list[_Choice]):
                        self.choices = choices
                        self.id = str(uuid.uuid4())
                        self.model = model
                        self.usage = {"total_tokens": 100}

                mock_content = f"[MOCK:{self._parent._parent.reason}] Response for model {model}"
                message = _Message(mock_content)
                choice = _Choice(message)
                return _Response([choice])

        @property
        def completions(self) -> object:
            return self._CompletionsWrapper(self)

    @property
    def chat(self) -> object:
        return self._ChatWrapper(self)

    def meta(self) -> dict[str, object]:
        return {
            "client_id": self._id,
            "created_at": self._created_at,
            "type": "mock",
            "reason": self.reason,
        }

# =============================================================================
# PUBLIC API
# =============================================================================

def get_ai_client(
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 180.0,
    use_cache: bool = True,
) -> object:
    """
    الحصول على مثيل عميل الذكاء الاصطناعي.

    هذه هي الدالة الأساسية للحصول على عملاء الذكاء الاصطناعي في جميع أنحاء التطبيق.

    Args:
        provider: اسم المزود.
        api_key: مفتاح الواجهة البرمجية.
        base_url: الرابط الأساسي.
        timeout: مهلة الطلب.
        use_cache: استخدام التخزين المؤقت.

    Returns:
        object: مثيل العميل.
    """
    return AIClientFactory.create_client(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        use_cache=use_cache,
    )

def clear_ai_client_cache() -> None:
    """مسح ذاكرة التخزين المؤقت لعملاء الذكاء الاصطناعي."""
    AIClientFactory.clear_cache()

def get_client_metadata() -> dict[str, dict[str, object]]:
    """الحصول على بيانات وصفية حول العملاء المخزنين."""
    return AIClientFactory.get_cached_clients()  # type: ignore

__all__ = [
    "AIClientFactory",
    "AIClientProtocol",
    "clear_ai_client_cache",
    "get_ai_client",
    "get_client_metadata",
]
