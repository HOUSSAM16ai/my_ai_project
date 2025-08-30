# app/services/llm_client_service.py - The Central Communications Ministry
# # -*- coding: utf-8 -*-
# ======================================================================================
#  LLM CLIENT SERVICE (v4.2.0 • "RESILIENT-COMMS-CORE+")
#  File: app/services/llm_client_service.py
# ======================================================================================
#  PURPOSE:
#    نقطة الارتكاز (Single Source of Truth) لإنشاء عميل LLM واحد مُعاد استعماله عبر النظام
#    (generation_service / maestro adapter / مخطط / CLI) مع:
#      - كشف تلقائي للمزود (OpenRouter أولاً ثم OpenAI).
#      - دعم وضع المحاكاة (Mock) لأغراض التطوير والاختبارات أو عند غياب المفاتيح.
#      - تصميم كسول (Lazy) + Singleton مع خيار تعطيل الكاش.
#      - واجهة متوافقة: client.chat.completions.create(...)
#      - ميتاداتا تشخيصية وشفافية كاملة (llm_health).
#      - أمان ضد العمل خارج سياق Flask (لا الاستيراد ولا التهشم).
#      - محاولة احتياطية (Fallback HTTP) إذا مكتبة openai غير متوفرة.
#
#  KEY FEATURES vs v3.0:
#      1. دعم تعدد نسخ مكتبة openai (الواجهة الحديثة openai.OpenAI والقديمة openai.ChatCompletion).
#      2. محرك Mock مُحسَّن مع تتبع usage (prompt_tokens / completion_tokens / total_tokens).
#      3. Fallback HTTP بسيط إلى OpenRouter إذا فشلت تهيئة مكتبة openai (بدون تبعية ثقيلة).
#      4. آلية reset مرنة + إمكانية فرض إعادة البناء (LLM_DISABLE_CACHE).
#      5. تلوين أسباب الانتقال إلى Mock (forced-mock-flag / no-api-key / real-client-init-failure / http-fallback).
#      6. خاصية حماية زمن التشغيل (Timeout) قابلة للتهيئة.
#      7. توحيد واجهة الاستدعاء حتى في أوضاع fallback.
#      8. وظائف: get_llm_client, reset_llm_client, is_mock_client, llm_health.
#
#  ENV VARS:
#      OPENROUTER_API_KEY          مفتاح OpenRouter (أولوية #1)
#      OPENAI_API_KEY              مفتاح OpenAI (أولوية #2)
#      LLM_BASE_URL                لتجاوز العنوان الافتراضي (OpenRouter أو OpenAI)
#      LLM_TIMEOUT_SECONDS         افتراضي 90
#      LLM_FORCE_MOCK=1            إجبار وضع المحاكاة
#      LLM_MOCK_MODE=1             نفس التأثير
#      LLM_DISABLE_CACHE=1         تعطيل التخزين المؤقت (كل نداء يبني عميل جديد)
#      LLM_HTTP_FALLBACK=1         السماح باستعمال requests كخطة طوارئ عند فشل مكتبة openai
#      LLM_LOG_LEVEL               افتراضي INFO
#
#  PUBLIC API:
#      get_llm_client()            -> يعيد العميل الموحد
#      reset_llm_client()          -> مسح الـ Singleton
#      is_mock_client(client=None) -> هل العميل محاكاة؟
#      llm_health()                -> تقرير تشخيصي
#
#  CLIENT INTERFACE EXPECTED BY CALLERS:
#      client.chat.completions.create(
#          model=..., messages=[{"role":"system","content":"..."}, ...],
#          tools=[...], tool_choice="auto", temperature=..., max_tokens=...
#      ) -> object يمتلك:
#          .choices[0].message.content
#          .choices[0].message.tool_calls (قد تكون None)
#          .usage = {"prompt_tokens": int?, "completion_tokens": int?, "total_tokens": int?}
#
#  NOTES:
#      - لا نحاول حساب tokens الحقيقية في Mock؛ نعيد أرقام تقديرية صغيرة
#      - إذا احتجت تسجيل أوسع يمكنك ربط logger الخارجي بالاسم: llm.client.service
#
# ======================================================================================

from __future__ import annotations

import json
import os
import time
import threading
import uuid
from typing import Any, Dict, Optional, List

# --------------------------------------------------------------------------------------
# Optional deps
# --------------------------------------------------------------------------------------
try:
    import openai  # المكتبة الحديثة (قد تكون v1.x ذات كلاس OpenAI)
except Exception:  # pragma: no cover
    openai = None  # type: ignore

try:
    import requests  # استعمل فقط في Fallback HTTP
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    from flask import current_app, has_app_context
except Exception:  # pragma: no cover
    current_app = None  # type: ignore
    def has_app_context() -> bool:  # type: ignore
        return False

import logging

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("llm.client.service")
_level = os.getenv("LLM_LOG_LEVEL", "INFO").upper()
try:
    _LOG.setLevel(getattr(logging, _level, logging.INFO))
except Exception:
    _LOG.setLevel(logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][llm.client] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# GLOBAL SINGLETON STATE
# --------------------------------------------------------------------------------------
_CLIENT_SINGLETON: Optional[Any] = None
_CLIENT_LOCK = threading.Lock()
_CLIENT_META: Dict[str, Any] = {}
_CLIENT_BUILD_SEQ = 0  # incremental identifier

# ======================================================================================
# MOCK CLIENT
# ======================================================================================

class MockLLMClient:
    """
    عميل محاكاة متوافق مع واجهة الدوال المطلوبة.
    """

    def __init__(self, reason: str, model_alias: str = "mock/virtual-model"):
        self._reason = reason
        self._created_at = time.time()
        self._calls = 0
        self._model = model_alias
        self._id = str(uuid.uuid4())

    class _ChatWrapper:
        def __init__(self, parent: "MockLLMClient"):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent: "MockLLMClient"):
                self._parent = parent

            def create(self, model: str, messages: List[Dict[str, str]], tools=None, tool_choice=None, **kwargs):
                self._parent._calls += 1
                # استخراج آخر رسالة مستخدم
                last_user = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_user = m.get("content", "")
                        break

                # بناء رد بسيط
                synthetic = f"[MOCK:{self._parent._reason}] model={model} calls={self._parent._calls}\nUser: {last_user[:400]}"

                # واجهات موازية للرسالة
                class _Msg:
                    def __init__(self, content: str):
                        self.content = content
                        self.tool_calls = None  # محجوزة لتوافق واجهة أدوات

                class _Choice:
                    def __init__(self, msg):
                        self.message = msg

                # تقدير usage تزويري
                prompt_tokens = max(1, sum(len(m.get("content", "")) for m in messages) // 16)
                completion_tokens = max(1, len(synthetic) // 18)
                usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }

                msg = _Msg(synthetic)
                return type("MockCompletion", (), {"choices": [_Choice(msg)], "usage": usage})()

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
            "calls": self._calls,
            "id": self._id
        }

# ======================================================================================
# FALLBACK HTTP CLIENT (Minimal OpenRouter Invocation)
# ======================================================================================

class _HttpFallbackClient:
    """
    عميل بسيط جداً يستعمل requests لاستدعاء OpenRouter إذا:
      - openai lib غير متاحة أو فشل تهيئتها.
      - LLM_HTTP_FALLBACK=1.
    يكتفي بتمثيل واجهة chat.completions.create (جزء صغير).
    """

    def __init__(self, api_key: str, base_url: str, timeout: float):
        self._api_key = api_key
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._calls = 0
        self._created_at = time.time()
        self._id = str(uuid.uuid4())

    class _ChatWrapper:
        def __init__(self, parent: "_HttpFallbackClient"):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent: "_HttpFallbackClient"):
                self._parent = parent

            def create(
                self,
                model: str,
                messages: List[Dict[str, str]],
                tools=None,
                tool_choice=None,
                temperature: float = 0.7,
                max_tokens: Optional[int] = None,
                **kwargs
            ):
                self._parent._calls += 1
                if requests is None:
                    raise RuntimeError("requests library not available for HTTP fallback.")
                url = f"{self._parent._base}/chat/completions"
                payload = {
                    "model": model,
                    "messages": messages,
                }
                if temperature is not None:
                    payload["temperature"] = temperature
                if max_tokens is not None:
                    payload["max_tokens"] = max_tokens
                # ملاحظة: تجاهل tools حالياً في fallback البسيط

                headers = {
                    "Authorization": f"Bearer {self._parent._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://localhost"),
                    "X-Title": os.getenv("OPENROUTER_TITLE", "Overmind"),
                }
                try:
                    resp = requests.post(url, json=payload, headers=headers, timeout=self._parent._timeout)
                except Exception as e:
                    raise RuntimeError(f"HTTP fallback request error: {e}")

                if resp.status_code >= 400:
                    raise RuntimeError(f"HTTP fallback bad status {resp.status_code}: {resp.text[:400]}")

                data = resp.json()
                # OpenRouter متوافق تقريباً مع شكل OpenAI
                # تأكد من وجود choices[0].message.content
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("HTTP fallback: no choices in response")

                first = choices[0]
                message = first.get("message", {})
                content = message.get("content", "")

                class _Msg:
                    def __init__(self, c):
                        self.content = c
                        self.tool_calls = None

                class _Choice:
                    def __init__(self, msg):
                        self.message = msg

                # usage (قد يكون موجوداً أو لا)
                usage_obj = data.get("usage") or {}
                usage = {
                    "prompt_tokens": usage_obj.get("prompt_tokens"),
                    "completion_tokens": usage_obj.get("completion_tokens"),
                    "total_tokens": usage_obj.get("total_tokens"),
                }

                msg = _Msg(content)
                return type("HttpFallbackCompletion", (), {"choices": [_Choice(msg)], "usage": usage})()

        @property
        def completions(self):
            return _HttpFallbackClient._ChatWrapper._CompletionsWrapper(self._parent)

    @property
    def chat(self):
        return _HttpFallbackClient._ChatWrapper(self)

    def meta(self) -> Dict[str, Any]:
        return {
            "mock": False,
            "http_fallback": True,
            "created_at": self._created_at,
            "calls": self._calls,
            "id": self._id,
            "base_url": self._base
        }

# ======================================================================================
# INTERNAL HELPERS
# ======================================================================================

def _read_config_key(key: str) -> Optional[str]:
    if has_app_context() and current_app:
        try:
            val = current_app.config.get(key)
            if val is not None:
                return str(val)
        except Exception:
            pass
    return os.environ.get(key)

def _resolve_api_credentials() -> Dict[str, Any]:
    """
    Priority:
      1) OPENROUTER_API_KEY (base default: https://openrouter.ai/api/v1)
      2) OPENAI_API_KEY     (base default: https://api.openai.com/v1)
    """
    openrouter_key = _read_config_key("OPENROUTER_API_KEY")
    openai_key = _read_config_key("OPENAI_API_KEY")
    base_url_env = _read_config_key("LLM_BASE_URL")

    if openrouter_key:
        return {
            "provider": "openrouter",
            "api_key": openrouter_key,
            "base_url": base_url_env or "https://openrouter.ai/api/v1"
        }
    if openai_key:
        return {
            "provider": "openai",
            "api_key": openai_key,
            "base_url": base_url_env or None  # OpenAI SDK سيختار الافتراضي
        }
    return {"provider": None, "api_key": None, "base_url": None}

def _should_force_mock() -> bool:
    return any(os.getenv(flag, "0") == "1" for flag in ("LLM_FORCE_MOCK", "LLM_MOCK_MODE"))

def _bool_env(name: str) -> bool:
    return os.getenv(name, "0") == "1"

# --------------------------------------------------------------------------------------
# REAL CLIENT BUILDERS
# --------------------------------------------------------------------------------------
def _build_openai_modern_client(creds: Dict[str, Any], timeout: float):
    """
    المحاولة الأساسية (لواجهة SDK الحديثة).
    """
    if openai is None:
        return None
    try:
        # واجهة v1.x
        client_kwargs: Dict[str, Any] = {"api_key": creds["api_key"]}
        if creds.get("base_url"):
            client_kwargs["base_url"] = creds["base_url"]
        # timeout الجديد في openai.OpenAI قد يسمى timeout
        client_kwargs["timeout"] = timeout
        client = openai.OpenAI(**client_kwargs)
        return client
    except Exception as e:
        _LOG.warning("Failed to build modern OpenAI client: %s", e)
        return None

def _build_openai_legacy_wrapper(creds: Dict[str, Any], timeout: float):
    """
    إذا النسخة قديمة (لا يوجد OpenAI class). نبني Wrapper يحاكي chat.completions.create.
    """
    if openai is None:
        return None

    # تحقق من وجود واجهة ChatCompletion
    if not hasattr(openai, "ChatCompletion"):
        return None

    class _LegacyChatWrapper:
        class _CompletionsWrapper:
            def create(self, model: str, messages, tools=None, tool_choice=None, temperature=0.7, max_tokens=None, **kwargs):
                # التوقيع الرئيسي: openai.ChatCompletion.create(...)
                try:
                    resp = openai.ChatCompletion.create(  # type: ignore
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except Exception as e:
                    raise RuntimeError(f"Legacy OpenAI call failed: {e}")
                # resp.choices[0].message["content"]
                # تهيئة شكل مقارب
                class _Msg:
                    def __init__(self, content: str):
                        self.content = content
                        self.tool_calls = None
                class _Choice:
                    def __init__(self, msg):
                        self.message = msg
                first = resp["choices"][0]["message"]["content"]
                msg = _Msg(first)
                usage = resp.get("usage", {})
                usage_norm = {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                }
                return type("LegacyCompletion", (), {"choices": [_Choice(msg)], "usage": usage_norm})()

        @property
        def completions(self):
            return _LegacyChatWrapper._CompletionsWrapper()

    class _LegacyClientWrapper:
        def __init__(self):
            self.chat = _LegacyChatWrapper()
            self._created_at = time.time()
            self._id = str(uuid.uuid4())
            self._calls = 0
        def meta(self):
            return {"legacy": True, "created_at": self._created_at, "id": self._id}

    # ضبط المفتاح والقيمة الأساسية (لو متاح)
    try:
        if creds["api_key"]:
            openai.api_key = creds["api_key"]  # type: ignore
        if creds.get("base_url"):
            openai.api_base = creds["base_url"]  # type: ignore
    except Exception:
        pass

    # (timeout) لا تتوفر طريقة مباشرة في الواجهة القديمة لإجباره لكل استدعاء.
    return _LegacyClientWrapper()

# --------------------------------------------------------------------------------------
# CORE BUILD PIPELINE
# --------------------------------------------------------------------------------------
def _build_real_client(creds: Dict[str, Any], timeout: float):
    """
    يحاول إنشاء عميل حقيقي (Modern -> Legacy -> HTTP fallback optional)
    وإلا يعيد None.
    """
    provider = creds["provider"]
    if provider not in ("openrouter", "openai"):
        return None

    # Modern
    client = _build_openai_modern_client(creds, timeout)
    if client:
        return client

    # Legacy
    client = _build_openai_legacy_wrapper(creds, timeout)
    if client:
        return client

    # Optional HTTP fallback (فقط إذا provider=openrouter & LLM_HTTP_FALLBACK=1)
    if provider == "openrouter" and _bool_env("LLM_HTTP_FALLBACK"):
        if requests is not None and creds.get("api_key"):
            try:
                return _HttpFallbackClient(creds["api_key"], creds["base_url"], timeout)
            except Exception as e:
                _LOG.warning("HTTP fallback init failed: %s", e)

    return None

# --------------------------------------------------------------------------------------
# HIGH LEVEL FACTORY
# --------------------------------------------------------------------------------------
def _build_client() -> Any:
    """
    يبني ويعيد عميل حقيقي أو Mock مع ضبط _CLIENT_META.
    """
    global _CLIENT_BUILD_SEQ
    _CLIENT_BUILD_SEQ += 1
    build_id = _CLIENT_BUILD_SEQ

    creds = _resolve_api_credentials()
    timeout_s = float(_read_config_key("LLM_TIMEOUT_SECONDS") or 90.0)
    disable_cache = _bool_env("LLM_DISABLE_CACHE")
    forced_mock = _should_force_mock()

    _CLIENT_META.clear()
    _CLIENT_META.update({
        "build_seq": build_id,
        "forced_mock": forced_mock,
        "provider_target": creds["provider"],
        "disable_cache": disable_cache,
        "timeout": timeout_s,
        "ts": time.time(),
    })

    # 1) Force mock
    if forced_mock:
        client = MockLLMClient("forced-mock-flag")
        _CLIENT_META.update({"provider_actual": "mock", "reason": "forced"})
        _LOG.info("[LLM] Using forced mock client.")
        return client

    # 2) Real attempt
    if creds["api_key"]:
        real = _build_real_client(creds, timeout_s)
        if real:
            # Detect fallback HTTP
            http_fb = isinstance(real, _HttpFallbackClient)
            _CLIENT_META.update({
                "provider_actual": creds["provider"],
                "base_url": creds.get("base_url"),
                "http_fallback_mode": http_fb,
            })
            mode = "HTTP-FALLBACK" if http_fb else "SDK"
            _LOG.info("[LLM] Real client established: provider=%s mode=%s", creds["provider"], mode)
            return real
        else:
            _LOG.warning("[LLM] Real client init failed, switching to mock.")

        # 3) fallback mock
        client = MockLLMClient("real-client-init-failure")
        _CLIENT_META.update({
            "provider_actual": "mock",
            "reason": "real-client-init-failure",
            "base_url": creds.get("base_url"),
        })
        return client

    # 4) No key → mock
    client = MockLLMClient("no-api-key")
    _CLIENT_META.update({
        "provider_actual": "mock",
        "reason": "no-api-key",
    })
    _LOG.info("[LLM] No API key detected; mock client in use.")
    return client

# ======================================================================================
# PUBLIC API
# ======================================================================================

def get_llm_client() -> Any:
    """
    يعيد العميل Singleton (أو يبنيه).
    إذا LLM_DISABLE_CACHE=1 → يُنشئ دائماً عميل جديد (للاختبارات).
    """
    global _CLIENT_SINGLETON
    disable_cache = _bool_env("LLM_DISABLE_CACHE")

    if disable_cache:
        return _build_client()

    if _CLIENT_SINGLETON is not None:
        return _CLIENT_SINGLETON

    with _CLIENT_LOCK:
        if _CLIENT_SINGLETON is None:
            _CLIENT_SINGLETON = _build_client()
        return _CLIENT_SINGLETON

def reset_llm_client() -> None:
    """
    مسح الـ Singleton ليُعاد بناؤه في النداء القادم.
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
    تقرير تشخيصي خفيف الوزن.
    """
    client = _CLIENT_SINGLETON
    base = {
        "initialized": client is not None,
        "meta": dict(_CLIENT_META),
        "has_app_context": has_app_context(),
        "env_openrouter_key": bool(os.getenv("OPENROUTER_API_KEY")),
        "env_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "forced_mock": _should_force_mock(),
        "disable_cache": _bool_env("LLM_DISABLE_CACHE"),
        "http_fallback_allowed": _bool_env("LLM_HTTP_FALLBACK"),
    }
    # إضافة تفاصيل إضافية
    if isinstance(client, MockLLMClient):
        base["client_kind"] = "mock"
        base["client_details"] = client.meta()
    elif isinstance(client, _HttpFallbackClient):
        base["client_kind"] = "http_fallback"
        base["client_details"] = client.meta()
    else:
        base["client_kind"] = "real_or_legacy"
    return base

# ======================================================================================
# SELF-TEST (manual execution)
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    print("=== LLM Client Service Self-Test ===")
    c1 = get_llm_client()
    print("Client Type:", type(c1))
    print("Health:", json.dumps(llm_health(), ensure_ascii=False, indent=2))
    if hasattr(c1, "chat"):
        try:
            resp = c1.chat.completions.create(
                model="test-model",
                messages=[{"role": "system", "content": "You are test."},
                          {"role": "user", "content": "Say ONLY OK."}]
            )
            print("Response:", getattr(resp.choices[0].message, "content", None))
            print("Usage:", getattr(resp, "usage", None))
        except Exception as exc:
            print("Invocation failed:", exc)
    reset_llm_client()
    print("After reset -> Health:", json.dumps(llm_health(), ensure_ascii=False, indent=2))