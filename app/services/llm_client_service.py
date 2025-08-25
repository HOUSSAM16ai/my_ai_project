# app/services/llm_client_service.py - The Central Communications Ministry
# ======================================================================================
# ==                  LLM CLIENT SERVICE (v3.0 • Resilient Comms Core)                ==
# ======================================================================================
# PURPOSE:
#   نقطة الارتكاز (Single Source of Truth) لإنشاء عميل LLM واحد مُعاد استعماله
#   عبر النظام (Maestro / Planners / CLI) بدون الاعتماد الصارم على وجود
#   Flask Application Context دائمًا.
#
# CORE PROBLEMS SOLVED:
#   1. "Working outside of application context":
#        - الآن نستعمل has_app_context() قبل لمس current_app.
#        - إذا لا يوجد سياق، نقرأ المفاتيح من المتغيرات البيئية مباشرة.
#   2. غياب المفتاح OPENROUTER_API_KEY:
#        - دعم FALLBACK إلى OPENAI_API_KEY (إن وُجد).
#        - خيار تشغيل وضع Mock عبر LLM_FORCE_MOCK=1 أو LLM_MOCK_MODE=1.
#   3. تفادي إنشاء عميل جديد في كل نداء (Singleton + Lazy Init + Reset).
#   4. دعم تبديل الـ Base URL (OPENROUTER / OPENAI) تلقائياً حسب المفتاح والبيئة.
#
# ENV VARS (الاستخدام):
#   OPENROUTER_API_KEY          مفتاح OpenRouter (مُفضل لهذا المشروع).
#   OPENAI_API_KEY              مفتاح OpenAI (بديل احتياطي / dev).
#   LLM_BASE_URL                لتجاوز القيمة الافتراضية (مثلاً mock endpoint).
#   LLM_TIMEOUT_SECONDS         (افتراضي 90).
#   LLM_FORCE_MOCK=1            إجبار وضع المحاكاة حتى مع وجود مفاتيح.
#   LLM_MOCK_MODE=1             نفس تأثير FORCE_MOCK (للراحة).
#   LLM_DISABLE_CACHE=1         تعطيل التخزين المؤقت وإعادة البناء كل مرة (للاختبارات).
#
# API SURFACE:
#   get_llm_client()            -> يُعيد العميل (OpenAI / Mock)
#   reset_llm_client()          -> يُعيد تهيئة التخزين المؤقت
#   is_mock_client(client=None) -> هل هو عميل محاكاة؟
#   llm_health()                -> تقرير صحة بسيط
#
# MOCK BEHAVIOR:
#   - يُعيد استجابات متوافقة مع ما يتوقعه generation_service:
#       client.chat.completions.create(...) -> كائن يحتوي choices[0].message.content
#
# ======================================================================================

from __future__ import annotations

import os
import time
import threading
from typing import Any, Dict, Optional

try:
    import openai  # مكتبة OpenAI الرسمية (الإصدار الحديث يستخدم openai.OpenAI)
except Exception:  # pragma: no cover
    openai = None  # type: ignore

try:
    from flask import current_app, has_app_context
except Exception:  # pragma: no cover
    current_app = None  # type: ignore
    def has_app_context() -> bool:  # type: ignore
        return False

# --------------------------------------------------------------------------------------
# GLOBAL STATE (Singleton Management)
# --------------------------------------------------------------------------------------
_CLIENT_SINGLETON: Optional[Any] = None
_CLIENT_LOCK = threading.Lock()
_CLIENT_META: Dict[str, Any] = {}

# --------------------------------------------------------------------------------------
# MOCK CLIENT
# --------------------------------------------------------------------------------------
class MockLLMClient:
    """
    عميل محاكاة (لا يتصل بأي API حقيقي).
    يُنتج واجهة متوافقة مع:
        client.chat.completions.create(...)
    """
    def __init__(self, reason: str):
        self._reason = reason
        self._created_at = time.time()
        self._calls = 0
        self._model = "mock/virtual-model"

    class _ChatWrapper:
        def __init__(self, parent: "MockLLMClient"):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent: "MockLLMClient"):
                self._parent = parent

            def create(self, model: str, messages, tools=None, tool_choice=None, **kwargs):
                self._parent._calls += 1

                # Simulate possible tool calls absence
                class _Msg:
                    def __init__(self, content: str):
                        self.content = content
                        self.tool_calls = None  # Keep shape consistent

                class _Choice:
                    def __init__(self, msg):
                        self.message = msg

                mock_text = (
                    f"[MOCK RESPONSE] model={model} calls={self._parent._calls} "
                    f"(reason={self._parent._reason})\n"
                    f"Last user prompt: {next((m.get('content') for m in reversed(messages) if m.get('role')=='user'), '')}"
                )

                msg = _Msg(mock_text)
                return type("MockCompletion", (), {"choices": [_Choice(msg)], "usage": {"total_tokens": 42}})()

        @property
        def completions(self):
            return MockLLMClient._ChatWrapper._CompletionsWrapper(self._parent)

    @property
    def chat(self):
        return MockLLMClient._ChatWrapper(self)

    def meta(self) -> Dict[str, Any]:
        return {
            "mock": True,
            "reason": self._reason,
            "model": self._model,
            "created_at": self._created_at,
            "calls": self._calls
        }


# --------------------------------------------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------------------------------------------
def _read_config_key(key: str) -> Optional[str]:
    """
    Read from Flask config if context available; fallback to environment variables.
    """
    if has_app_context() and current_app:
        try:
            val = current_app.config.get(key)
            if val:
                return str(val)
        except Exception:
            pass
    return os.environ.get(key)


def _resolve_api_credentials() -> Dict[str, Any]:
    """
    Decide which provider credentials to use.
    Priority:
        1. OPENROUTER_API_KEY
        2. OPENAI_API_KEY
    """
    openrouter_key = _read_config_key("OPENROUTER_API_KEY")
    openai_key = _read_config_key("OPENAI_API_KEY")

    if openrouter_key:
        return {
            "provider": "openrouter",
            "api_key": openrouter_key,
            "base_url": _read_config_key("LLM_BASE_URL") or "https://openrouter.ai/api/v1",
        }
    if openai_key:
        # OpenAI default base
        return {
            "provider": "openai",
            "api_key": openai_key,
            "base_url": _read_config_key("LLM_BASE_URL") or None,
        }
    return {"provider": None, "api_key": None, "base_url": None}


def _should_force_mock() -> bool:
    return any(
        os.getenv(flag, "0") == "1"
        for flag in ("LLM_FORCE_MOCK", "LLM_MOCK_MODE")
    )


def _build_real_client(creds: Dict[str, Any], timeout: float):
    """
    Construct the real OpenAI/OpenRouter client. Returns None if openai lib missing.
    """
    if openai is None:
        return None

    # New SDK style: openai.OpenAI(...)
    kwargs: Dict[str, Any] = {
        "api_key": creds["api_key"],
        "timeout": timeout
    }
    if creds.get("base_url"):
        kwargs["base_url"] = creds["base_url"]

    try:
        client = openai.OpenAI(**kwargs)
        return client
    except Exception:
        return None


def _build_client() -> Any:
    """
    Core builder: constructs either a real client or a mock fallback.
    """
    creds = _resolve_api_credentials()
    timeout_s = float(_read_config_key("LLM_TIMEOUT_SECONDS") or 90.0)
    disable_cache = os.getenv("LLM_DISABLE_CACHE", "0") == "1"

    # Force mock explicitly
    if _should_force_mock():
        client = MockLLMClient("forced-mock-flag")
        _CLIENT_META.update({
            "provider": "mock",
            "forced": True,
            "timeout": timeout_s,
            "cached": not disable_cache
        })
        return client

    # Try real
    if creds["api_key"]:
        real_client = _build_real_client(creds, timeout_s)
        if real_client:
            _CLIENT_META.update({
                "provider": creds["provider"],
                "forced": False,
                "timeout": timeout_s,
                "base_url": creds.get("base_url"),
                "cached": not disable_cache
            })
            return real_client
        # Failure to build real client => fallback to mock
        client = MockLLMClient("real-client-init-failure")
        _CLIENT_META.update({
            "provider": "mock",
            "forced": False,
            "timeout": timeout_s,
            "fallback": "real-client-init-failure",
            "cached": not disable_cache
        })
        return client

    # No API key at all => mock
    client = MockLLMClient("no-api-key")
    _CLIENT_META.update({
        "provider": "mock",
        "forced": False,
        "timeout": timeout_s,
        "reason": "no-api-key",
        "cached": not disable_cache
    })
    return client


# --------------------------------------------------------------------------------------
# PUBLIC API
# --------------------------------------------------------------------------------------
def get_llm_client() -> Any:
    """
    Return the singleton LLM client (real or mock). Safe outside Flask context.
    If LLM_DISABLE_CACHE=1 => always rebuild.
    """
    global _CLIENT_SINGLETON
    disable_cache = os.getenv("LLM_DISABLE_CACHE", "0") == "1"

    if disable_cache:
        # Always rebuild new instance (testing / profiling)
        return _build_client()

    if _CLIENT_SINGLETON is not None:
        return _CLIENT_SINGLETON

    with _CLIENT_LOCK:
        if _CLIENT_SINGLETON is None:
            _CLIENT_SINGLETON = _build_client()
        return _CLIENT_SINGLETON


def reset_llm_client() -> None:
    """
    Clear the cached singleton (e.g., after changing env variables at runtime).
    """
    global _CLIENT_SINGLETON
    with _CLIENT_LOCK:
        _CLIENT_SINGLETON = None
        _CLIENT_META.clear()


def is_mock_client(client: Optional[Any] = None) -> bool:
    c = client or _CLIENT_SINGLETON
    return isinstance(c, MockLLMClient)


def llm_health() -> Dict[str, Any]:
    """
    Lightweight status for diagnostics endpoints / CLI.
    """
    client = _CLIENT_SINGLETON
    base = {
        "initialized": client is not None,
        "meta": dict(_CLIENT_META),
        "has_app_context": has_app_context(),
        "env_openrouter_key": bool(os.getenv("OPENROUTER_API_KEY")),
        "env_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "force_mock": _should_force_mock()
    }
    if isinstance(client, MockLLMClient):
        base["mock_details"] = client.meta()
    return base


# --------------------------------------------------------------------------------------
# SELF-TEST (manual invocation)
# --------------------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    print("=== LLM Client Service Self-Test ===")
    c1 = get_llm_client()
    print("Client 1 (type):", type(c1))
    print("Health:", llm_health())
    if hasattr(c1, "chat"):
        try:
            resp = c1.chat.completions.create(
                model="test-model",
                messages=[{"role": "user", "content": "Say hi briefly."}]
            )
            print("Response:", getattr(resp.choices[0].message, "content", None))
        except Exception as exc:
            print("Invocation failed:", exc)
    reset_llm_client()
    print("After reset -> Health:", llm_health())