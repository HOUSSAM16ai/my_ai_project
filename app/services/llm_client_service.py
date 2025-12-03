# app/services/llm_client_service.py
"""
LLM Client Service - Pure FastAPI/Python Edition
================================================
Central authoritative gateway for all LLM invocations.
Refactored to be completely independent of Flask globals.
Uses `pydantic-settings` for configuration via `app.core.config`.

REFACTORED: Now delegates actual client creation to centralized
app.core.ai_client_factory module. This service maintains backward
compatibility while using the new centralized infrastructure.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import random
import re
import threading
import time
import uuid
from collections.abc import Callable, Generator
from typing import Any

from app.core.ai_client_factory import (
    clear_ai_client_cache,
)

# Import centralized AI client factory
from app.core.ai_client_factory import (
    get_ai_client as _get_centralized_client,
)

# Use requests for HTTP fallback if available
try:
    import requests  # type: ignore
except ImportError:
    requests = None  # type: ignore

try:
    import openai
except ImportError:
    openai = None  # type: ignore

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# GLOBAL SINGLETON STATE (LEGACY - Now delegates to centralized factory)
# --------------------------------------------------------------------------------------
_CLIENT_SINGLETON: Any | None = None
_CLIENT_LOCK = threading.Lock()
_CLIENT_META: dict[str, Any] = {}
_CLIENT_BUILD_SEQ = 0

# NOTE: The actual client creation is now handled by app.core.ai_client_factory
# This module maintains these globals for backward compatibility only

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
        self._is_mock_client = True  # Protocol marker for detection

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
                tools: Any = None,
                tool_choice: Any = None,
                **kwargs: Any,
            ) -> Any:
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
                    def __init__(self, msg: _Msg):
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
        def completions(self) -> _CompletionsWrapper:
            return MockLLMClient._ChatWrapper._CompletionsWrapper(self._parent)

    @property
    def chat(self) -> _ChatWrapper:
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
                tools: Any = None,
                tool_choice: Any = None,
                temperature: float = 0.7,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> Any:
                self._parent._calls += 1
                if requests is None:
                    raise RuntimeError("requests not available for HTTP fallback.")
                url = f"{self._parent._base}/chat/completions"
                payload: dict[str, Any] = {
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
                except requests.exceptions.Timeout as e:
                    raise RuntimeError(
                        f"HTTP fallback timeout after {self._parent._timeout}s: {e}"
                    ) from e
                except requests.exceptions.ConnectionError as e:
                    raise RuntimeError(f"HTTP fallback connection error: {e}") from e
                except Exception as e:
                    raise RuntimeError(
                        f"HTTP fallback request error: {type(e).__name__}: {e}"
                    ) from e

                if resp.status_code >= 400:
                    error_text = resp.text[:400] if resp.text else "No error details"

                    if resp.status_code >= 500:
                        raise RuntimeError(
                            f"server_error_500: OpenRouter API returned server error. "
                            f"Status {resp.status_code}: {error_text}"
                        )
                    elif resp.status_code in (401, 403):
                        raise RuntimeError(
                            f"authentication_error: Invalid or missing API key. "
                            f"Status {resp.status_code}: {error_text}"
                        )
                    elif resp.status_code == 429:
                        raise RuntimeError(
                            f"rate_limit_error: Too many requests. "
                            f"Status {resp.status_code}: {error_text}"
                        )
                    elif resp.status_code == 400:
                        raise RuntimeError(
                            f"bad_request_error: Invalid request parameters. "
                            f"Status {resp.status_code}: {error_text}"
                        )
                    else:
                        raise RuntimeError(f"HTTP error {resp.status_code}: {error_text}")

                try:
                    data = resp.json()
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to parse JSON response: {type(e).__name__}: {e}. "
                        f"Response text: {resp.text[:200]}"
                    ) from e

                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError(
                        f"HTTP fallback: no choices in response. Response keys: {list(data.keys())}"
                    )

                first = choices[0]
                message = first.get("message", {})
                content = message.get("content", "")

                # SUPERHUMAN CHECK: Validate content
                if content is None:
                    _LOG.warning(
                        "HTTP fallback received None content from API. Converting to empty string."
                    )
                    content = ""

                class _Msg:
                    def __init__(self, c: str):
                        self.content = c
                        self.tool_calls = None

                class _Choice:
                    def __init__(self, msg: _Msg):
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
        def completions(self) -> _CompletionsWrapper:
            return _HttpFallbackClient._ChatWrapper._CompletionsWrapper(self._parent)

    @property
    def chat(self) -> _ChatWrapper:
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
    """
    Reads configuration from environment variables.
    Previously fell back to Flask config; now strictly environment or Pydantic settings.
    """
    return os.environ.get(key)


def _resolve_api_credentials() -> dict[str, Any]:
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


def _build_openai_modern_client(creds: dict[str, Any], timeout: float) -> Any:
    if openai is None:
        return None
    try:
        client_kwargs: dict[str, Any] = {"api_key": creds["api_key"]}
        if creds.get("base_url"):
            client_kwargs["base_url"] = creds["base_url"]
        client_kwargs["timeout"] = timeout
        return openai.OpenAI(**client_kwargs)
    except Exception as e:
        _LOG.warning("Failed to build modern OpenAI client: %s", e)
        return None


def _build_openai_legacy_wrapper(creds: dict[str, Any], timeout: float) -> Any:
    if openai is None:
        return None
    if not hasattr(openai, "ChatCompletion"):
        return None

    class _LegacyChatWrapper:
        class _CompletionsWrapper:
            def create(
                self,
                model: str,
                messages: list[dict[str, str]],
                tools: Any = None,
                tool_choice: Any = None,
                temperature: float = 0.7,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> Any:
                try:
                    # Legacy OpenAI usage (hypothetical if using very old lib version)
                    resp = openai.ChatCompletion.create(  # type: ignore
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except Exception as e:
                    raise RuntimeError(f"Legacy OpenAI call failed: {e}") from e

                class _Msg:
                    def __init__(self, content: str):
                        self.content = content
                        self.tool_calls = None

                class _Choice:
                    def __init__(self, msg: _Msg):
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
        def completions(self) -> _CompletionsWrapper:
            return _LegacyChatWrapper._CompletionsWrapper()

    class _LegacyClientWrapper:
        def __init__(self) -> None:
            self.chat = _LegacyChatWrapper()
            self._created_at = time.time()
            self._id = str(uuid.uuid4())

        def meta(self) -> dict[str, Any]:
            return {"legacy": True, "created_at": self._created_at, "id": self._id}

    try:
        if creds["api_key"]:
            openai.api_key = creds["api_key"]
        if creds.get("base_url"):
            openai.api_base = creds["base_url"]
    except Exception:
        pass
    return _LegacyClientWrapper()


def _build_real_client(creds: dict[str, Any], timeout: float) -> Any:
    provider = creds["provider"]
    if provider not in ("openrouter", "openai"):
        return None

    client = _build_openai_modern_client(creds, timeout)
    if client:
        return client

    client = _build_openai_legacy_wrapper(creds, timeout)
    if client:
        return client

    if (
        provider == "openrouter"
        and _bool_env("LLM_HTTP_FALLBACK")
        and requests is not None
        and creds.get("api_key")
    ):
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
    _LLM_EXTREME_MODE = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"
    _LLM_ULTIMATE_MODE = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"

    default_timeout = 1800.0 if _LLM_ULTIMATE_MODE else (600.0 if _LLM_EXTREME_MODE else 180.0)
    timeout_s = float(_read_config_key("LLM_TIMEOUT_SECONDS") or default_timeout)

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
# PUBLIC CORE ACCESS (REFACTORED - Now delegates to centralized factory)
# ======================================================================================


def get_llm_client() -> Any:
    """
    Get LLM client instance.

    REFACTORED: Now delegates to centralized app.core.ai_client_factory.
    Maintains backward compatibility with legacy code.
    """
    global _CLIENT_SINGLETON
    disable_cache = _bool_env("LLM_DISABLE_CACHE")
    forced_mock = _should_force_mock()

    if forced_mock:
        # Bypass factory logic if forced mock is requested via legacy env var
        if _CLIENT_SINGLETON is None or not is_mock_client(_CLIENT_SINGLETON):
             # We can't easily ask factory for "forced mock", so we use legacy MockLLMClient directly
             # or better, use factory's _create_mock_client if exposed, but it is private.
             # We will stick to legacy MockLLMClient for forced mode to satisfy tests
             _CLIENT_SINGLETON = MockLLMClient("forced-mock-flag")
             _CLIENT_META.update({"reason": "forced"})
        return _CLIENT_SINGLETON

    if disable_cache:
        # Use centralized factory without caching
        return _get_centralized_client(use_cache=False)

    if _CLIENT_SINGLETON is not None:
        return _CLIENT_SINGLETON

    with _CLIENT_LOCK:
        if _CLIENT_SINGLETON is None:
            # Delegate to centralized factory
            _CLIENT_SINGLETON = _get_centralized_client(use_cache=True)
            _LOG.info("LLM client created via centralized factory")
        return _CLIENT_SINGLETON


def reset_llm_client() -> None:
    """
    Reset the LLM client singleton.

    REFACTORED: Also clears centralized factory cache.
    """
    global _CLIENT_SINGLETON
    with _CLIENT_LOCK:
        _CLIENT_SINGLETON = None
        _CLIENT_META.clear()
        # Clear centralized factory cache too
        clear_ai_client_cache()
        _LOG.info("LLM client reset (including centralized cache)")


def is_mock_client(client: Any | None = None) -> bool:
    """
    Check if client is a mock client.

    Uses multiple strategies to detect mock clients:
    1. Check if it's our MockLLMClient type
    2. Check if it has a 'mock' attribute
    3. Check class name as fallback
    """
    c = client or _CLIENT_SINGLETON

    # Strategy 1: Check instanceof MockLLMClient
    if isinstance(c, MockLLMClient):
        return True

    # Strategy 2: Check for mock attribute (protocol-based)
    if hasattr(c, "_is_mock_client") and c._is_mock_client:
        return True

    # Strategy 3: Check class name (fallback, less reliable)
    return bool(hasattr(c, "__class__") and "Mock" in c.__class__.__name__)


# ======================================================================================
# METRICS / STATE / COST / HOOKS / BREAKER
# ======================================================================================

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

_PRE_HOOKS: list[Callable[[dict[str, Any]], None]] = []
_POST_HOOKS: list[Callable[[dict[str, Any], dict[str, Any]], None]] = []

# Circuit Breaker State
_BREAKER_STATE: dict[str, Any] = {
    "errors": [],  # list[timestamps]
    "open_until": 0.0,  # timestamp if open
    "open_events": 0,
}


def register_llm_pre_hook(fn: Callable[[dict[str, Any]], None]) -> None:
    _PRE_HOOKS.append(fn)


def register_llm_post_hook(fn: Callable[[dict[str, Any], dict[str, Any]], None]) -> None:
    _POST_HOOKS.append(fn)


def _classify_error(exc: Exception) -> str:
    """
    Classify errors for intelligent retry and reporting.

    SUPERHUMAN ENHANCEMENTS V2.0:
    - More granular error classification
    - Better pattern matching
    - Support for new error types
    """
    msg = str(exc).lower()
    exc_type = type(exc).__name__.lower()

    # Server errors (5xx)
    if any(
        x in msg for x in ["server_error_500", "500", "internal server error", "502", "503", "504"]
    ):
        return "server_error"

    # Rate limiting
    if ("rate" in msg and "limit" in msg) or "429" in msg or "too many requests" in msg:
        return "rate_limit"

    # Authentication & Authorization errors
    if any(
        x in msg
        for x in [
            "authentication_error",
            "unauthorized",
            "api key",
            "invalid api key",
            "401",
            "403",
            "forbidden",
            "invalid_api_key",
        ]
    ):
        return "auth_error"

    # Timeout errors
    if "timeout" in msg or "timed out" in msg or "timeouterror" in exc_type:
        return "timeout"

    # Connection & Network errors
    if any(x in msg for x in ["connection", "network", "dns", "connect", "refused"]):
        return "network"

    # Parsing errors
    if ("parse" in msg or "json" in msg or "decode" in msg) and "error" in msg:
        return "parse"

    # Empty response errors
    if "empty" in msg or "no content" in msg or "null" in msg:
        return "empty_response"

    # Model-specific errors
    if "model" in msg and ("not found" in msg or "unavailable" in msg):
        return "model_error"

    return "unknown"


def _retry_allowed(kind: str) -> bool:
    """
    Determine if retry is allowed for this error type.

    SUPERHUMAN ENHANCEMENTS:
    - More intelligent retry decisions
    - Configurable retry policies
    """
    _LLM_RETRY_ON_AUTH = os.getenv("LLM_RETRY_ON_AUTH", "0") == "1"
    _LLM_RETRY_ON_PARSE = os.getenv("LLM_RETRY_ON_PARSE", "0") == "1"
    _LLM_RETRY_ON_EMPTY = os.getenv("LLM_RETRY_ON_EMPTY", "1") == "1"

    # Never retry auth errors unless explicitly enabled
    if kind == "auth_error" and not _LLM_RETRY_ON_AUTH:
        _LOG.debug("Auth error detected - retry disabled by config")
        return False

    # Conditional retry on parse errors
    if kind == "parse" and not _LLM_RETRY_ON_PARSE:
        _LOG.debug("Parse error detected - retry disabled by config")
        return False

    # Conditional retry on empty responses
    if kind == "empty_response" and not _LLM_RETRY_ON_EMPTY:
        _LOG.debug("Empty response detected - retry disabled by config")
        return False

    # Always retry these types
    retry_always = ["rate_limit", "network", "timeout", "server_error", "model_error"]
    if kind in retry_always:
        return True

    # For unknown errors, allow retry by default (defensive programming)
    return True


def _estimate_cost(
    model: str, prompt_tokens: int | None, completion_tokens: int | None
) -> float | None:
    try:
        _MODEL_COST_TABLE = json.loads(os.getenv("MODEL_COST_TABLE_JSON", "{}"))
        _MODEL_ALIAS_MAP = json.loads(os.getenv("MODEL_ALIAS_MAP_JSON", "{}"))
    except Exception:
        _MODEL_COST_TABLE = {}
        _MODEL_ALIAS_MAP = {}

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
    _LLM_SANITIZE_OUTPUT = os.getenv("LLM_SANITIZE_OUTPUT", "0") == "1"
    if not _LLM_SANITIZE_OUTPUT or not isinstance(text, str):
        return text

    sanitized = text.replace("\r", "")
    for marker in _SENSITIVE_MARKERS:
        if marker in sanitized:
            sanitized = sanitized.replace(marker, f"[REDACTED:{marker}]")

    try:
        _SANITIZE_REGEXES = json.loads(os.getenv("LLM_SANITIZE_REGEXES_JSON", "[]"))
    except Exception:
        _SANITIZE_REGEXES = []

    for pattern in _SANITIZE_REGEXES:
        with contextlib.suppress(Exception):
            sanitized = re.sub(pattern, "[REDACTED_PATTERN]", sanitized)
    return sanitized


def _apply_force_model(payload: dict[str, Any]) -> None:
    _LLM_FORCE_MODEL = os.getenv("LLM_FORCE_MODEL", "").strip() or None
    if _LLM_FORCE_MODEL:
        payload["model"] = _LLM_FORCE_MODEL


def _maybe_stream_simulated(full_text: str, chunk_size: int = 100) -> Generator[str, None, None]:
    for i in range(0, len(full_text), chunk_size):
        yield full_text[i : i + chunk_size]


def _circuit_allowed() -> bool:
    now = time.time()
    return not _BREAKER_STATE["open_until"] > now


def _note_error_for_breaker() -> None:
    now = time.time()
    _BREAKER_WINDOW = float(os.getenv("LLM_BREAKER_WINDOW", "60") or 60.0)
    _BREAKER_THRESHOLD = int(os.getenv("LLM_BREAKER_ERROR_THRESHOLD", "6") or 6)
    _BREAKER_COOLDOWN = float(os.getenv("LLM_BREAKER_COOLDOWN", "30") or 30.0)

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


def _maybe_close_breaker() -> None:
    now = time.time()
    if _BREAKER_STATE["open_until"] and _BREAKER_STATE["open_until"] <= now:
        pass


def _enforce_cost_budget(new_cost: float | None) -> None:
    if not new_cost:
        return
    _COST_BUDGET_SESSION = float(os.getenv("LLM_COST_BUDGET_SESSION", "0") or 0.0)
    _COST_BUDGET_HARD_FAIL = os.getenv("LLM_COST_BUDGET_HARD_FAIL", "0") == "1"

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
    if not _circuit_allowed():
        raise RuntimeError("LLM circuit breaker OPEN – rejecting invocation temporarily.")

    _LLM_EXTREME_MODE = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"
    _LLM_ULTIMATE_MODE = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"

    _LLM_MAX_RETRIES = int(
        os.getenv(
            "LLM_MAX_RETRIES", "20" if _LLM_ULTIMATE_MODE else ("8" if _LLM_EXTREME_MODE else "2")
        )
    )
    _LLM_RETRY_BACKOFF_BASE = float(
        os.getenv(
            "LLM_RETRY_BACKOFF_BASE",
            "1.8" if _LLM_ULTIMATE_MODE else ("1.5" if _LLM_EXTREME_MODE else "1.3"),
        )
    )
    _LLM_RETRY_JITTER = os.getenv("LLM_RETRY_JITTER", "1") == "1"
    _LLM_ENABLE_STREAM = os.getenv("LLM_ENABLE_STREAM", "0") == "1"
    _LLM_FORCE_MODEL = os.getenv("LLM_FORCE_MODEL", "").strip() or None

    _LOG_ATTEMPTS = os.getenv("LLM_LOG_ATTEMPTS", "1") == "1"

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

    def _do_call() -> Any:
        return client.chat.completions.create(
            model=payload["model"],
            messages=payload["messages"],
            tools=payload["tools"],
            tool_choice=payload["tool_choice"],
            temperature=payload["temperature"],
            max_tokens=payload["max_tokens"],
        )

    def _complete_once() -> dict[str, Any]:
        """
        Complete a single LLM request with retry logic.

        SUPERHUMAN ENHANCEMENTS:
        - Empty response detection and handling
        - Better error context
        - Response validation
        """
        nonlocal attempts, last_exc, backoff
        while attempts <= _LLM_MAX_RETRIES:
            attempts += 1
            t0 = time.perf_counter()
            try:
                completion = _do_call()
                latency_ms = (time.perf_counter() - t0) * 1000.0

                # Extract response data with validation
                content = getattr(completion.choices[0].message, "content", "")
                tool_calls = getattr(completion.choices[0].message, "tool_calls", None)
                usage = getattr(completion, "usage", {}) or {}
                pt = usage.get("prompt_tokens")
                ct = usage.get("completion_tokens")
                total = usage.get("total_tokens")

                # SUPERHUMAN CHECK: Detect empty responses and handle intelligently
                if (
                    content is None or (isinstance(content, str) and content.strip() == "")
                ) and not tool_calls:
                    # Empty response with no tool calls - this is problematic
                    _LOG.warning(
                        f"Empty response received from model {payload['model']} "
                        f"at attempt {attempts}/{_LLM_MAX_RETRIES}. "
                        f"No content and no tool calls."
                    )

                    # Treat as retriable error if we have retries left
                    if attempts < _LLM_MAX_RETRIES:
                        empty_exc = RuntimeError(
                            f"Empty response from model (no content, no tool calls). "
                            f"Attempt {attempts}/{_LLM_MAX_RETRIES}"
                        )
                        kind = _classify_error(empty_exc)
                        if _retry_allowed(kind):
                            sleep_for = backoff
                            if _LLM_RETRY_JITTER:
                                sleep_for += random.random() * 0.25
                            retry_schedule.append(round(sleep_for, 3))
                            _LOG.warning(f"Retrying after empty response in {sleep_for:.2f}s...")
                            time.sleep(sleep_for)
                            backoff *= _LLM_RETRY_BACKOFF_BASE
                            continue

                    # No retries left or retry not allowed - return error envelope
                    _LLMTOTAL["calls"] += 1
                    _LLMTOTAL["errors"] += 1
                    _note_error_for_breaker()

                    return {
                        "content": "",
                        "tool_calls": None,
                        "usage": usage,
                        "model": payload["model"],
                        "provider": _CLIENT_META.get("provider_actual"),
                        "latency_ms": round(latency_ms, 2),
                        "cost": None,
                        "error": "Empty response from model",
                        "meta": {
                            "attempts": attempts,
                            "success": False,
                            "empty_response": True,
                        },
                    }

                # Update metrics
                _LLMTOTAL["calls"] += 1
                if pt:
                    _LLMTOTAL["prompt_tokens"] += pt
                if ct:
                    _LLMTOTAL["completion_tokens"] += ct
                if total:
                    _LLMTOTAL["total_tokens"] += total
                _LLMTOTAL["latencies_ms"].append(latency_ms)
                if len(_LLMTOTAL["latencies_ms"]) > _LAT_WIN:
                    _LLMTOTAL["latencies_ms"][:] = _LLMTOTAL["latencies_ms"][-_LAT_WIN:]

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

                # Enhanced error logging
                if _LOG_ATTEMPTS:
                    _LOG.warning(
                        f"LLM attempt #{attempts}/{_LLM_MAX_RETRIES} failed. "
                        f"Error kind: {kind}, Type: {type(exc).__name__}, "
                        f"Message: {exc!s}"
                    )

                if attempts > _LLM_MAX_RETRIES or not _retry_allowed(kind):
                    if _LOG_ATTEMPTS:
                        _LOG.error(
                            f"LLM final failure after {attempts} attempts. "
                            f"Error kind: {kind}, Exception: {type(exc).__name__}: {exc!s}"
                        )
                    break

                sleep_for = backoff
                if _LLM_RETRY_JITTER:
                    sleep_for += random.random() * 0.25
                retry_schedule.append(round(sleep_for, 3))

                if _LOG_ATTEMPTS:
                    _LOG.warning(
                        f"Retrying LLM call (attempt {attempts + 1}/{_LLM_MAX_RETRIES + 1}) "
                        f"after {sleep_for:.2f}s. Error kind: {kind}"
                    )

                time.sleep(sleep_for)
                backoff *= _LLM_RETRY_BACKOFF_BASE

        # Build comprehensive error message
        error_details = f"Error kind: {_classify_error(last_exc) if last_exc else 'unknown'}"
        if last_exc:
            error_details += f", Type: {type(last_exc).__name__}, Message: {last_exc!s}"

        raise RuntimeError(f"LLM invocation failed after {attempts} attempts. {error_details}")

    if not use_stream:
        result = _complete_once()
        _maybe_close_breaker()
        return result

    def _stream_gen() -> Generator[dict[str, Any], None, None]:
        envelope = _complete_once()
        full = envelope["content"]
        for chunk in _maybe_stream_simulated(full):
            yield {"delta": _sanitize(chunk)}
        envelope["meta"]["stream"] = True
        _maybe_close_breaker()
        yield envelope

    return _stream_gen()


def invoke_chat_stream(*args: Any, **kwargs: Any) -> Generator[dict[str, Any], None, None]:
    kwargs["stream"] = True
    result = invoke_chat(*args, **kwargs)
    if not isinstance(result, Generator):
        raise RuntimeError("invoke_chat_stream expected a generator; streaming not enabled.")
    return result


def llm_health() -> dict[str, Any]:
    client = _CLIENT_SINGLETON
    _BREAKER_WINDOW = float(os.getenv("LLM_BREAKER_WINDOW", "60") or 60.0)
    _BREAKER_THRESHOLD = int(os.getenv("LLM_BREAKER_ERROR_THRESHOLD", "6") or 6)
    _BREAKER_COOLDOWN = float(os.getenv("LLM_BREAKER_COOLDOWN", "30") or 30.0)

    _LLM_ENABLE_STREAM = os.getenv("LLM_ENABLE_STREAM", "0") == "1"
    _LLM_FORCE_MODEL = os.getenv("LLM_FORCE_MODEL", "").strip() or None
    _LLM_SANITIZE_OUTPUT = os.getenv("LLM_SANITIZE_OUTPUT", "0") == "1"
    _LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
    _COST_BUDGET_SESSION = float(os.getenv("LLM_COST_BUDGET_SESSION", "0") or 0.0)
    _COST_BUDGET_HARD_FAIL = os.getenv("LLM_COST_BUDGET_HARD_FAIL", "0") == "1"

    try:
        _MODEL_COST_TABLE = json.loads(os.getenv("MODEL_COST_TABLE_JSON", "{}"))
        _MODEL_ALIAS_MAP = json.loads(os.getenv("MODEL_ALIAS_MAP_JSON", "{}"))
    except Exception:
        _MODEL_COST_TABLE = {}
        _MODEL_ALIAS_MAP = {}

    base = {
        "initialized": client is not None,
        "meta": dict(_CLIENT_META),
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


__all__ = [
    "get_llm_client",
    "invoke_chat",
    "invoke_chat_stream",
    "is_mock_client",
    "llm_health",
    "register_llm_post_hook",
    "register_llm_pre_hook",
    "reset_llm_client",
]
