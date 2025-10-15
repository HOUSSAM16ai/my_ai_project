# app/services/llm_client_service.py - The Central Communications Ministry
# =================================================================================================
#  LLM CLIENT SERVICE – HYPER PRO EDITION
#  Version: 4.7.0  •  Codename: "RESILIENT-COMMS-ULTRA / RETRY+STREAM / COST / CIRCUIT / HOOKS"
# =================================================================================================
#  PURPOSE
#    Single Authoritative Gateway for all LLM invocations across the Overmind stack:
#      - Unified construction & reuse (lazy singleton; optional cache disable).
#      - Automatic multi-provider credential detection (OpenRouter → OpenAI).
#      - Modern + legacy OpenAI SDK compatibility + lightweight HTTP fallback.
#      - Resilient high-level interface invoke_chat() + optional streaming.
#      - Structured response envelope (content / usage / latency / cost / meta).
#      - Retries with exponential backoff + jitter + error taxonomy.
#      - Circuit breaker for repeated transient failures.
#      - Cumulative usage & (optional) cost estimation (per model rate table).
#      - Hooks (pre / post) for dynamic policy injection, tracing, sanitization.
#      - Output sanitization (sensitive marker redaction).
#      - Force-model override, configurable timeouts, mock fallback modes.
#      - Health diagnostics (llm_health) enriched with latency & breaker state.
#
#  COMPATIBILITY
#    - Backward compatible with legacy direct usage: client.chat.completions.create(...)
#    - New advanced consumers should prefer invoke_chat() or invoke_chat_stream().
#
#  NEW vs 4.6.0
#    + Dedicated invoke_chat_stream() helper.
#    + Circuit Breaker (configurable window / threshold / cooldown).
#    + Budget Guard (session cost ceiling).
#    + Smart Retry Policy (skip retry for auth_error / parse unless configured).
#    + Selective Retry Error Classes.
#    + Cost Budget Hard-Fail vs Soft Warn.
#    + Model alias normalization (optional mapping).
#    + Expanded Sanitization patterns + optional regex redaction.
#    + Fine-grained logging levels for attempts & breaker events.
#    + Minimal internal stats snapshot (for external orchestrators).
#
#  ENV VARS (Key Subset)
#    OPENROUTER_API_KEY                Primary key (priority #1)
#    OPENAI_API_KEY                    Secondary key
#    LLM_BASE_URL                      Override base URL
#    LLM_TIMEOUT_SECONDS=180            # Increased from 90 to handle long/complex questions
#    LLM_FORCE_MOCK=0|1
#    LLM_MOCK_MODE=0|1                 (alias)
#    LLM_DISABLE_CACHE=0|1
#    LLM_HTTP_FALLBACK=0|1
#
#    LLM_MAX_RETRIES=2
#    LLM_RETRY_BACKOFF_BASE=1.3
#    LLM_RETRY_JITTER=1
#    LLM_RETRY_ON_AUTH=0              (auth_error normally not retried)
#    LLM_RETRY_ON_PARSE=0
#
#    LLM_ENABLE_STREAM=0
#    LLM_FORCE_MODEL=""               Force override model name
#    LLM_SANITIZE_OUTPUT=0
#    LLM_SANITIZE_REGEXES_JSON='["OPENAI_API_KEY=[A-Za-z0-9_-]+"]'
#
#    MODEL_COST_TABLE_JSON='{"openai/gpt-4o":{"prompt":0.000002,"completion":0.000006}}'
#    MODEL_ALIAS_MAP_JSON='{"gpt-4o":"openai/gpt-4o"}'
#
#    LLM_COST_BUDGET_SESSION=0        (0 => disabled; else numeric USD upper limit)
#    LLM_COST_BUDGET_HARD_FAIL=0      (if 1 and budget exceeded → raise error)
#
#    # Circuit Breaker
#    LLM_BREAKER_WINDOW=60            (seconds)
#    LLM_BREAKER_ERROR_THRESHOLD=6
#    LLM_BREAKER_COOLDOWN=30
#
#    # Logging
#    LLM_LOG_LEVEL=INFO
#    LLM_LOG_ATTEMPTS=1
#
#  PUBLIC API
#    get_llm_client()
#    reset_llm_client()
#    is_mock_client(client=None)
#    llm_health()
#    invoke_chat(...)
#    invoke_chat_stream(... generator ...)
#    register_llm_pre_hook(fn)
#    register_llm_post_hook(fn)
#
#  RESPONSE ENVELOPE (invoke_chat)
#    {
#      "content": str,
#      "tool_calls": list|None,
#      "usage": {prompt_tokens, completion_tokens, total_tokens},
#      "model": str,
#      "provider": str|None,
#      "latency_ms": float,
#      "cost": float|None,
#      "raw": <original completion object>,
#      "meta": {
#          "attempts": int,
#          "forced_model": bool,
#          "http_fallback": bool|None,
#          "build_seq": int,
#          "stream": bool,
#          "start_ts": float,
#          "end_ts": float,
#          "circuit_breaker_open": bool,
#          "retry_schedule": [<floats>]
#      }
#    }
#
#  LICENSE / NOTE
#    Internal proprietary orchestration layer snippet – adapt carefully.
# =================================================================================================

from __future__ import annotations

import json
import os
import random
import re
import threading
import time
import uuid
from collections.abc import Callable, Generator
from typing import Any

# --------------------------------------------------------------------------------------
# Optional dependencies
# --------------------------------------------------------------------------------------
try:
    import openai  # Modern SDK (v1.x with class OpenAI) OR legacy structure
except Exception:  # pragma: no cover
    openai = None  # type: ignore

try:
    import requests  # For HTTP fallback
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    from flask import current_app, has_app_context
except Exception:  # pragma: no cover
    current_app = None  # type: ignore

    def has_app_context() -> bool:  # type: ignore
        return False


import contextlib
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

_LOG_ATTEMPTS = os.getenv("LLM_LOG_ATTEMPTS", "1") == "1"

# --------------------------------------------------------------------------------------
# GLOBAL SINGLETON STATE
# --------------------------------------------------------------------------------------
_CLIENT_SINGLETON: Any | None = None
_CLIENT_LOCK = threading.Lock()
_CLIENT_META: dict[str, Any] = {}
_CLIENT_BUILD_SEQ = 0

# ======================================================================================
# MOCK CLIENT
# ======================================================================================


class MockLLMClient:
    """
    Mock client with minimal compatibility.
    """

    def __init__(self, reason: str, model_alias: str = "mock/virtual-model"):
        self._reason = reason
        self._created_at = time.time()
        self._calls = 0
        self._model = model_alias
        self._id = str(uuid.uuid4())

    class _ChatWrapper:
        def __init__(self, parent: MockLLMClient):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent: MockLLMClient):
                self._parent = parent

            def create(
                self,
                model: str,
                messages: list[dict[str, str]],
                tools=None,
                tool_choice=None,
                **kwargs,
            ):
                self._parent._calls += 1
                last_user = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_user = m.get("content", "")
                        break

                synthetic = (
                    f"[MOCK:{self._parent._reason}] model={model} calls={self._parent._calls}\n"
                    f"User: {last_user[:400]}"
                )

                class _Msg:
                    def __init__(self, content: str):
                        self.content = content
                        self.tool_calls = None

                class _Choice:
                    def __init__(self, msg):
                        self.message = msg

                prompt_tokens = max(1, sum(len(m.get("content", "")) for m in messages) // 16)
                completion_tokens = max(1, len(synthetic) // 18)
                usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                }

                msg = _Msg(synthetic)
                return type("MockCompletion", (), {"choices": [_Choice(msg)], "usage": usage})()

        @property
        def completions(self):
            return MockLLMClient._ChatWrapper._CompletionsWrapper(self._parent)

    @property
    def chat(self):
        return MockLLMClient._ChatWrapper(self)

    def meta(self) -> dict[str, Any]:
        return {
            "mock": True,
            "reason": self._reason,
            "model": self._model,
            "created_at": self._created_at,
            "calls": self._calls,
            "id": self._id,
        }


# ======================================================================================
# FALLBACK HTTP CLIENT
# ======================================================================================


class _HttpFallbackClient:
    """
    Minimal HTTP fallback (OpenRouter style).
    """

    def __init__(self, api_key: str, base_url: str, timeout: float):
        self._api_key = api_key
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._calls = 0
        self._created_at = time.time()
        self._id = str(uuid.uuid4())

    class _ChatWrapper:
        def __init__(self, parent: _HttpFallbackClient):
            self._parent = parent

        class _CompletionsWrapper:
            def __init__(self, parent: _HttpFallbackClient):
                self._parent = parent

            def create(
                self,
                model: str,
                messages: list[dict[str, str]],
                tools=None,
                tool_choice=None,
                temperature: float = 0.7,
                max_tokens: int | None = None,
                **kwargs,
            ):
                self._parent._calls += 1
                if requests is None:
                    raise RuntimeError("requests not available for HTTP fallback.")
                url = f"{self._parent._base}/chat/completions"
                payload = {
                    "model": model,
                    "messages": messages,
                }
                if temperature is not None:
                    payload["temperature"] = temperature
                if max_tokens is not None:
                    payload["max_tokens"] = max_tokens

                headers = {
                    "Authorization": f"Bearer {self._parent._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://localhost"),
                    "X-Title": os.getenv("OPENROUTER_TITLE", "Overmind"),
                }
                try:
                    resp = requests.post(
                        url, json=payload, headers=headers, timeout=self._parent._timeout
                    )
                except Exception as e:
                    raise RuntimeError(f"HTTP fallback request error: {e}")

                if resp.status_code >= 400:
                    # Enhanced error handling with better context
                    error_text = resp.text[:400] if resp.text else "No error details"
                    if resp.status_code == 500:
                        raise RuntimeError(
                            f"server_error_500: OpenRouter API returned internal server error. "
                            f"This may be due to invalid API key, service issues, or request problems. "
                            f"Details: {error_text}"
                        )
                    elif resp.status_code == 401 or resp.status_code == 403:
                        raise RuntimeError(
                            f"authentication_error: Invalid or missing API key. "
                            f"Status {resp.status_code}: {error_text}"
                        )
                    elif resp.status_code == 429:
                        raise RuntimeError(
                            f"rate_limit_error: Too many requests. "
                            f"Status {resp.status_code}: {error_text}"
                        )
                    else:
                        raise RuntimeError(
                            f"HTTP fallback bad status {resp.status_code}: {error_text}"
                        )

                data = resp.json()
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

                usage_obj = data.get("usage") or {}
                usage = {
                    "prompt_tokens": usage_obj.get("prompt_tokens"),
                    "completion_tokens": usage_obj.get("completion_tokens"),
                    "total_tokens": usage_obj.get("total_tokens"),
                }

                msg = _Msg(content)
                return type(
                    "HttpFallbackCompletion", (), {"choices": [_Choice(msg)], "usage": usage}
                )()

        @property
        def completions(self):
            return _HttpFallbackClient._ChatWrapper._CompletionsWrapper(self._parent)

    @property
    def chat(self):
        return _HttpFallbackClient._ChatWrapper(self)

    def meta(self) -> dict[str, Any]:
        return {
            "mock": False,
            "http_fallback": True,
            "created_at": self._created_at,
            "calls": self._calls,
            "id": self._id,
            "base_url": self._base,
        }


# ======================================================================================
# INTERNAL CONFIG HELPERS
# ======================================================================================


def _read_config_key(key: str) -> str | None:
    if has_app_context() and current_app:
        try:
            val = current_app.config.get(key)
            if val is not None:
                return str(val)
        except Exception:
            pass
    return os.environ.get(key)


def _resolve_api_credentials() -> dict[str, Any]:
    """
    Priority:
      1) OPENROUTER_API_KEY (base default: https://openrouter.ai/api/v1)
      2) OPENAI_API_KEY
    """
    openrouter_key = _read_config_key("OPENROUTER_API_KEY")
    openai_key = _read_config_key("OPENAI_API_KEY")
    base_url_env = _read_config_key("LLM_BASE_URL")

    if openrouter_key:
        return {
            "provider": "openrouter",
            "api_key": openrouter_key,
            "base_url": base_url_env or "https://openrouter.ai/api/v1",
        }
    if openai_key:
        return {"provider": "openai", "api_key": openai_key, "base_url": base_url_env or None}
    return {"provider": None, "api_key": None, "base_url": None}


def _should_force_mock() -> bool:
    return any(os.getenv(flag, "0") == "1" for flag in ("LLM_FORCE_MOCK", "LLM_MOCK_MODE"))


def _bool_env(name: str) -> bool:
    return os.getenv(name, "0") == "1"


# ======================================================================================
# REAL CLIENT BUILDERS
# ======================================================================================


def _build_openai_modern_client(creds: dict[str, Any], timeout: float):
    if openai is None:
        return None
    try:
        client_kwargs: dict[str, Any] = {"api_key": creds["api_key"]}
        if creds.get("base_url"):
            client_kwargs["base_url"] = creds["base_url"]
        client_kwargs["timeout"] = timeout
        return openai.OpenAI(**client_kwargs)  # type: ignore
    except Exception as e:
        _LOG.warning("Failed to build modern OpenAI client: %s", e)
        return None


def _build_openai_legacy_wrapper(creds: dict[str, Any], timeout: float):
    if openai is None:
        return None
    if not hasattr(openai, "ChatCompletion"):
        return None

    class _LegacyChatWrapper:
        class _CompletionsWrapper:
            def create(
                self,
                model: str,
                messages,
                tools=None,
                tool_choice=None,
                temperature=0.7,
                max_tokens=None,
                **kwargs,
            ):
                try:
                    resp = openai.ChatCompletion.create(  # type: ignore
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except Exception as e:
                    raise RuntimeError(f"Legacy OpenAI call failed: {e}")

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
                return type(
                    "LegacyCompletion", (), {"choices": [_Choice(msg)], "usage": usage_norm}
                )()

        @property
        def completions(self):
            return _LegacyChatWrapper._CompletionsWrapper()

    class _LegacyClientWrapper:
        def __init__(self):
            self.chat = _LegacyChatWrapper()
            self._created_at = time.time()
            self._id = str(uuid.uuid4())

        def meta(self):
            return {"legacy": True, "created_at": self._created_at, "id": self._id}

    try:
        if creds["api_key"]:
            openai.api_key = creds["api_key"]  # type: ignore
        if creds.get("base_url"):
            openai.api_base = creds["base_url"]  # type: ignore
    except Exception:
        pass
    return _LegacyClientWrapper()


def _build_real_client(creds: dict[str, Any], timeout: float):
    provider = creds["provider"]
    if provider not in ("openrouter", "openai"):
        return None

    client = _build_openai_modern_client(creds, timeout)
    if client:
        return client

    client = _build_openai_legacy_wrapper(creds, timeout)
    if client:
        return client

    if provider == "openrouter" and _bool_env("LLM_HTTP_FALLBACK"):
        if requests is not None and creds.get("api_key"):
            try:
                return _HttpFallbackClient(creds["api_key"], creds["base_url"], timeout)
            except Exception as e:
                _LOG.warning("HTTP fallback init failed: %s", e)

    return None


# ======================================================================================
# BUILD / FACTORY
# ======================================================================================


def _build_client() -> Any:
    global _CLIENT_BUILD_SEQ
    _CLIENT_BUILD_SEQ += 1
    build_id = _CLIENT_BUILD_SEQ

    creds = _resolve_api_credentials()
    timeout_s = float(
        _read_config_key("LLM_TIMEOUT_SECONDS") or 180.0
    )  # Increased from 90 to 180 for long questions
    disable_cache = _bool_env("LLM_DISABLE_CACHE")
    forced_mock = _should_force_mock()

    _CLIENT_META.clear()
    _CLIENT_META.update(
        {
            "build_seq": build_id,
            "forced_mock": forced_mock,
            "provider_target": creds["provider"],
            "disable_cache": disable_cache,
            "timeout": timeout_s,
            "ts": time.time(),
        }
    )

    if forced_mock:
        client = MockLLMClient("forced-mock-flag")
        _CLIENT_META.update({"provider_actual": "mock", "reason": "forced"})
        _LOG.info("[LLM] Using forced mock client.")
        return client

    if creds["api_key"]:
        real = _build_real_client(creds, timeout_s)
        if real:
            http_fb = isinstance(real, _HttpFallbackClient)
            _CLIENT_META.update(
                {
                    "provider_actual": creds["provider"],
                    "base_url": creds.get("base_url"),
                    "http_fallback_mode": http_fb,
                }
            )
            mode = "HTTP-FALLBACK" if http_fb else "SDK"
            _LOG.info("[LLM] Real client established: provider=%s mode=%s", creds["provider"], mode)
            return real
        else:
            _LOG.warning("[LLM] Real client init failed, switching to mock.")
        client = MockLLMClient("real-client-init-failure")
        _CLIENT_META.update(
            {
                "provider_actual": "mock",
                "reason": "real-client-init-failure",
                "base_url": creds.get("base_url"),
            }
        )
        return client

    client = MockLLMClient("no-api-key")
    _CLIENT_META.update(
        {
            "provider_actual": "mock",
            "reason": "no-api-key",
        }
    )
    _LOG.info("[LLM] No API key detected; mock client in use.")
    return client


# ======================================================================================
# PUBLIC CORE ACCESS
# ======================================================================================


def get_llm_client() -> Any:
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
    global _CLIENT_SINGLETON
    with _CLIENT_LOCK:
        _CLIENT_SINGLETON = None
        _CLIENT_META.clear()


def is_mock_client(client: Any | None = None) -> bool:
    c = client or _CLIENT_SINGLETON
    return isinstance(c, MockLLMClient)


# ======================================================================================
# METRICS / STATE / COST / HOOKS / BREAKER
# ======================================================================================

_LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
_LLM_RETRY_BACKOFF_BASE = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.3"))
_LLM_RETRY_JITTER = os.getenv("LLM_RETRY_JITTER", "1") == "1"
_LLM_ENABLE_STREAM = os.getenv("LLM_ENABLE_STREAM", "0") == "1"
_LLM_FORCE_MODEL = os.getenv("LLM_FORCE_MODEL", "").strip() or None
_LLM_SANITIZE_OUTPUT = os.getenv("LLM_SANITIZE_OUTPUT", "0") == "1"
_LLM_RETRY_ON_AUTH = os.getenv("LLM_RETRY_ON_AUTH", "0") == "1"
_LLM_RETRY_ON_PARSE = os.getenv("LLM_RETRY_ON_PARSE", "0") == "1"

try:
    _MODEL_COST_TABLE = json.loads(os.getenv("MODEL_COST_TABLE_JSON", "{}"))
except Exception:
    _MODEL_COST_TABLE = {}

try:
    _MODEL_ALIAS_MAP = json.loads(os.getenv("MODEL_ALIAS_MAP_JSON", "{}"))
except Exception:
    _MODEL_ALIAS_MAP = {}

_COST_BUDGET_SESSION = float(os.getenv("LLM_COST_BUDGET_SESSION", "0") or 0.0)
_COST_BUDGET_HARD_FAIL = os.getenv("LLM_COST_BUDGET_HARD_FAIL", "0") == "1"

# Circuit Breaker
_BREAKER_WINDOW = float(os.getenv("LLM_BREAKER_WINDOW", "60") or 60.0)
_BREAKER_THRESHOLD = int(os.getenv("LLM_BREAKER_ERROR_THRESHOLD", "6") or 6)
_BREAKER_COOLDOWN = float(os.getenv("LLM_BREAKER_COOLDOWN", "30") or 30.0)
_BREAKER_STATE = {
    "errors": [],  # list[timestamps]
    "open_until": 0.0,  # timestamp if open
    "open_events": 0,
}

# Sanitization regex list
try:
    _SANITIZE_REGEXES = json.loads(os.getenv("LLM_SANITIZE_REGEXES_JSON", "[]"))
except Exception:
    _SANITIZE_REGEXES = []

_PRE_HOOKS: list[Callable[[dict[str, Any]], None]] = []
_POST_HOOKS: list[Callable[[dict[str, Any], dict[str, Any]], None]] = []


def register_llm_pre_hook(fn: Callable[[dict[str, Any]], None]) -> None:
    _PRE_HOOKS.append(fn)


def register_llm_post_hook(fn: Callable[[dict[str, Any], dict[str, Any]], None]) -> None:
    _POST_HOOKS.append(fn)


# Cumulative stats
_LLMTOTAL = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "calls": 0,
    "errors": 0,
    "last_error_kind": None,
    "latencies_ms": [],
    "cost_usd": 0.0,
}
_LAT_WIN = 300

_SENSITIVE_MARKERS = ("OPENAI_API_KEY=", "sk-or-", "sk-")


def _classify_error(exc: Exception) -> str:
    msg = str(exc).lower()
    # Check for specific error patterns (order matters - most specific first)
    if "server_error_500" in msg or "500" in msg or "internal server error" in msg:
        return "server_error"
    if "rate" in msg and "limit" in msg:
        return "rate_limit"
    if "authentication_error" in msg or "unauthorized" in msg or "api key" in msg or "invalid api key" in msg or "401" in msg or "403" in msg:
        return "auth_error"
    if "timeout" in msg:
        return "timeout"
    if "connection" in msg or "network" in msg or "dns" in msg:
        return "network"
    if "parse" in msg or "json" in msg:
        return "parse"
    return "unknown"


def _retry_allowed(kind: str) -> bool:
    if kind == "auth_error" and not _LLM_RETRY_ON_AUTH:
        return False
    if kind == "parse" and not _LLM_RETRY_ON_PARSE:
        return False
    return kind in ("rate_limit", "network", "timeout", "parse") or True  # 'unknown' fallback


def _estimate_cost(
    model: str, prompt_tokens: int | None, completion_tokens: int | None
) -> float | None:
    if not model:
        return None
    model_key = _MODEL_ALIAS_MAP.get(model, model)
    data = _MODEL_COST_TABLE.get(model_key)
    if not data:
        return None
    p_rate = data.get("prompt", 0)
    c_rate = data.get("completion", 0)
    pt = prompt_tokens or 0
    ct = completion_tokens or 0
    return round(pt * p_rate + ct * c_rate, 6)


def _sanitize(text: str) -> str:
    if not _LLM_SANITIZE_OUTPUT or not isinstance(text, str):
        return text
    sanitized = text.replace("\r", "")
    for marker in _SENSITIVE_MARKERS:
        if marker in sanitized:
            sanitized = sanitized.replace(marker, f"[REDACTED:{marker}]")
    # Regex patterns
    for pattern in _SANITIZE_REGEXES:
        with contextlib.suppress(Exception):
            sanitized = re.sub(pattern, "[REDACTED_PATTERN]", sanitized)
    return sanitized


def _apply_force_model(payload: dict[str, Any]) -> None:
    if _LLM_FORCE_MODEL:
        payload["model"] = _LLM_FORCE_MODEL


def _maybe_stream_simulated(full_text: str, chunk_size: int = 100) -> Generator[str, None, None]:
    for i in range(0, len(full_text), chunk_size):
        yield full_text[i : i + chunk_size]


def _circuit_allowed() -> bool:
    now = time.time()
    return not _BREAKER_STATE["open_until"] > now


def _note_error_for_breaker():
    now = time.time()
    _BREAKER_STATE["errors"].append(now)
    cutoff = now - _BREAKER_WINDOW
    _BREAKER_STATE["errors"] = [t for t in _BREAKER_STATE["errors"] if t >= cutoff]
    if len(_BREAKER_STATE["errors"]) >= _BREAKER_THRESHOLD and _BREAKER_STATE["open_until"] <= now:
        _BREAKER_STATE["open_until"] = now + _BREAKER_COOLDOWN
        _BREAKER_STATE["open_events"] += 1
        _LOG.warning(
            "LLM Circuit Breaker OPEN (errors=%d threshold=%d cooldown=%ds)",
            len(_BREAKER_STATE["errors"]),
            _BREAKER_THRESHOLD,
            _BREAKER_COOLDOWN,
        )


def _maybe_close_breaker():
    now = time.time()
    if _BREAKER_STATE["open_until"] and _BREAKER_STATE["open_until"] <= now:
        # Passive closure
        pass


def _enforce_cost_budget(new_cost: float | None):
    if not new_cost:
        return
    if _COST_BUDGET_SESSION <= 0:
        return
    projected = _LLMTOTAL["cost_usd"] + new_cost
    if projected > _COST_BUDGET_SESSION:
        msg = (
            f"LLM session cost budget exceeded: projected={projected:.6f} > "
            f"budget={_COST_BUDGET_SESSION:.6f}"
        )
        if _COST_BUDGET_HARD_FAIL:
            raise RuntimeError(msg)
        _LOG.warning("[LLM] %s (soft warn).", msg)


# ======================================================================================
# HIGH LEVEL INVOCATION
# ======================================================================================


def invoke_chat(
    model: str,
    messages: list[dict[str, str]],
    *,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    stream: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | Generator[dict[str, Any], None, None]:
    """
    High-level resilient call.
    If stream True (and enabled), returns generator that yields partial {"delta": "..."} pieces,
    followed by final envelope on completion.
    """
    if not _circuit_allowed():
        raise RuntimeError("LLM circuit breaker OPEN – rejecting invocation temporarily.")

    client = get_llm_client()
    start_build = time.time()
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": tool_choice,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "extra": extra or {},
    }
    _apply_force_model(payload)

    for hook in _PRE_HOOKS:
        try:
            hook(payload)
        except Exception as e:
            _LOG.warning("LLM pre_hook error: %s", e)

    use_stream = stream if stream is not None else _LLM_ENABLE_STREAM
    attempts = 0
    last_exc: Exception | None = None
    backoff = _LLM_RETRY_BACKOFF_BASE
    retry_schedule: list[float] = []

    def _do_call():
        return client.chat.completions.create(
            model=payload["model"],
            messages=payload["messages"],
            tools=payload["tools"],
            tool_choice=payload["tool_choice"],
            temperature=payload["temperature"],
            max_tokens=payload["max_tokens"],
        )

    def _complete_once() -> dict[str, Any]:
        nonlocal attempts, last_exc, backoff
        while attempts <= _LLM_MAX_RETRIES:
            attempts += 1
            t0 = time.perf_counter()
            try:
                completion = _do_call()
                latency_ms = (time.perf_counter() - t0) * 1000.0
                content = getattr(completion.choices[0].message, "content", "")
                tool_calls = getattr(completion.choices[0].message, "tool_calls", None)
                usage = getattr(completion, "usage", {}) or {}
                pt = usage.get("prompt_tokens")
                ct = usage.get("completion_tokens")
                total = usage.get("total_tokens")
                _LLMTOTAL["calls"] += 1
                if pt:
                    _LLMTOTAL["prompt_tokens"] += pt
                if ct:
                    _LLMTOTAL["completion_tokens"] += ct
                if total:
                    _LLMTOTAL["total_tokens"] += total
                _LLMTOTAL["latencies_ms"].append(latency_ms)
                if len(_LLMTOTAL["latencies_ms"]) > _LAT_WIN:
                    _LLMTOTAL["latencies_ms"] = _LLMTOTAL["latencies_ms"][-_LAT_WIN:]
                content = _sanitize(content)
                cost = _estimate_cost(payload["model"], pt, ct)
                _enforce_cost_budget(cost)
                if cost:
                    _LLMTOTAL["cost_usd"] += cost
                envelope = {
                    "content": content,
                    "tool_calls": tool_calls,
                    "usage": usage,
                    "model": payload["model"],
                    "provider": _CLIENT_META.get("provider_actual"),
                    "latency_ms": round(latency_ms, 2),
                    "cost": cost,
                    "raw": completion,
                    "meta": {
                        "attempts": attempts,
                        "forced_model": bool(_LLM_FORCE_MODEL),
                        "http_fallback": _CLIENT_META.get("http_fallback_mode"),
                        "build_seq": _CLIENT_META.get("build_seq"),
                        "stream": False,
                        "start_ts": start_build,
                        "end_ts": time.time(),
                        "circuit_breaker_open": False,
                        "retry_schedule": retry_schedule,
                    },
                }
                for hook in _POST_HOOKS:
                    try:
                        hook(payload, envelope)
                    except Exception as e:
                        _LOG.warning("LLM post_hook error: %s", e)
                return envelope
            except Exception as exc:
                kind = _classify_error(exc)
                _LLMTOTAL["errors"] += 1
                _LLMTOTAL["last_error_kind"] = kind
                _note_error_for_breaker()
                last_exc = exc
                if attempts > _LLM_MAX_RETRIES or not _retry_allowed(kind):
                    if _LOG_ATTEMPTS:
                        _LOG.error(
                            "LLM final failure attempt=%d kind=%s err=%s", attempts, kind, exc
                        )
                    break
                sleep_for = backoff
                if _LLM_RETRY_JITTER:
                    sleep_for += random.random() * 0.25
                retry_schedule.append(round(sleep_for, 3))
                if _LOG_ATTEMPTS:
                    _LOG.warning(
                        "LLM retry #%d (kind=%s in %.2fs) err=%s", attempts, kind, sleep_for, exc
                    )
                time.sleep(sleep_for)
                backoff *= _LLM_RETRY_BACKOFF_BASE
        raise RuntimeError(f"LLM invocation failed after {attempts} attempts: {last_exc}")

    if not use_stream:
        result = _complete_once()
        _maybe_close_breaker()
        return result

    def _stream_gen() -> Generator[dict[str, Any], None, None]:
        # Simulated streaming: first full call → break content into deltas.
        # After simulation, we still produce a final envelope (fresh call or reuse).
        envelope = _complete_once()
        full = envelope["content"]
        for chunk in _maybe_stream_simulated(full):
            yield {"delta": _sanitize(chunk)}
        # Produce final (mark stream)
        envelope["meta"]["stream"] = True
        _maybe_close_breaker()
        yield envelope

    return _stream_gen()


def invoke_chat_stream(*args, **kwargs) -> Generator[dict[str, Any], None, None]:
    """
    Explicit streaming helper. Forces stream=True.
    """
    kwargs["stream"] = True
    result = invoke_chat(*args, **kwargs)
    if not isinstance(result, Generator):
        raise RuntimeError("invoke_chat_stream expected a generator; streaming not enabled.")
    return result  # type: ignore


# ======================================================================================
# HEALTH & SNAPSHOT
# ======================================================================================


def llm_health() -> dict[str, Any]:
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
    if isinstance(client, MockLLMClient):
        base["client_kind"] = "mock"
        base["client_details"] = client.meta()
    elif isinstance(client, _HttpFallbackClient):
        base["client_kind"] = "http_fallback"
        base["client_details"] = client.meta()
    else:
        base["client_kind"] = "real_or_legacy"
    lat = _LLMTOTAL["latencies_ms"]
    avg_lat = round(sum(lat) / len(lat), 2) if lat else None
    base["cumulative"] = {
        "prompt_tokens": _LLMTOTAL["prompt_tokens"],
        "completion_tokens": _LLMTOTAL["completion_tokens"],
        "total_tokens": _LLMTOTAL["total_tokens"],
        "calls": _LLMTOTAL["calls"],
        "errors": _LLMTOTAL["errors"],
        "last_error_kind": _LLMTOTAL["last_error_kind"],
        "avg_latency_ms": avg_lat,
        "cost_usd": round(_LLMTOTAL["cost_usd"], 6),
    }
    now = time.time()
    base["circuit_breaker"] = {
        "open": _BREAKER_STATE["open_until"] > now,
        "open_until": _BREAKER_STATE["open_until"],
        "recent_error_count": len(
            [t for t in _BREAKER_STATE["errors"] if t >= now - _BREAKER_WINDOW]
        ),
        "window": _BREAKER_WINDOW,
        "threshold": _BREAKER_THRESHOLD,
        "cooldown": _BREAKER_COOLDOWN,
        "open_events": _BREAKER_STATE["open_events"],
    }
    base["features"] = {
        "retry": _LLM_MAX_RETRIES > 0,
        "stream_enabled": _LLM_ENABLE_STREAM,
        "force_model": _LLM_FORCE_MODEL,
        "sanitize_output": _LLM_SANITIZE_OUTPUT,
        "pre_hooks": len(_PRE_HOOKS),
        "post_hooks": len(_POST_HOOKS),
        "cost_table_loaded": bool(_MODEL_COST_TABLE),
        "model_alias_map": bool(_MODEL_ALIAS_MAP),
        "cost_budget_session": _COST_BUDGET_SESSION,
        "cost_budget_hard_fail": _COST_BUDGET_HARD_FAIL,
    }
    return base


# ======================================================================================
# INTERNAL / DEBUG UTILS
# ======================================================================================


def _debug_snapshot() -> dict[str, Any]:
    return {
        "client_kind": llm_health().get("client_kind"),
        "cumulative": llm_health().get("cumulative"),
        "breaker": llm_health().get("circuit_breaker"),
    }


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "get_llm_client",
    "reset_llm_client",
    "is_mock_client",
    "llm_health",
    "invoke_chat",
    "invoke_chat_stream",
    "register_llm_pre_hook",
    "register_llm_post_hook",
]

# ======================================================================================
# SELF-TEST (manual execution)
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    print("=== LLM Client Service Self-Test (v4.7.0) ===")
    c1 = get_llm_client()
    print("Client Type:", type(c1))
    print("Health (initial):", json.dumps(llm_health(), ensure_ascii=False, indent=2))

    try:
        resp = invoke_chat(
            model="test-model",
            messages=[
                {"role": "system", "content": "You are test."},
                {"role": "user", "content": "Say ONLY OK."},
            ],
        )
        if isinstance(resp, dict):
            print("Response content:", resp.get("content"))
            print("Usage:", resp.get("usage"))
            print("Meta:", resp.get("meta"))
        else:
            print("Streaming generator unexpected in self-test (skipped).")
    except Exception as exc:
        print("Invocation failed:", exc)

    # Streaming simulation (if enabled)
    if _LLM_ENABLE_STREAM:
        print("\n-- Streaming Test --")
        try:
            for part in invoke_chat_stream(
                model="test-model", messages=[{"role": "user", "content": "Stream test please."}]
            ):
                print("STREAM PART:", part)
        except Exception as se:
            print("Streaming failed:", se)

    print("After calls -> Health:", json.dumps(llm_health(), ensure_ascii=False, indent=2))
    reset_llm_client()
    print("After reset -> Health:", json.dumps(llm_health(), ensure_ascii=False, indent=2))
# =================================================================================================
# END OF FILE
# =================================================================================================
