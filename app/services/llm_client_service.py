# app/services/llm_client_service.py
"""
LLM Client Service - Pure FastAPI/Python Edition
================================================
Central authoritative gateway for all LLM invocations.
Refactored to be completely independent of Flask globals.
Uses `pydantic-settings` for configuration via `app.config.settings`.

REFACTORED: Now delegates actual client creation to centralized
app.core.ai_client_factory module. This service maintains backward
compatibility while using the new centralized infrastructure.
"""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from collections.abc import Callable, Generator
from typing import Any

# Import centralized AI client factory
from app.core.ai_client_factory import (
    MockClient,
    clear_ai_client_cache,
)
from app.core.ai_client_factory import (
    get_ai_client as _get_centralized_client,
)

# New Modular Helpers
from app.ai.application.payload_builder import PayloadBuilder
from app.ai.application.response_normalizer import ResponseNormalizer
from app.services.llm.circuit_breaker import CircuitBreaker
from app.services.llm.cost_manager import CostManager
from app.services.llm.retry_strategy import RetryStrategy

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# GLOBAL SINGLETON STATE (LEGACY - Now delegates to centralized factory)
# --------------------------------------------------------------------------------------
_CLIENT_SINGLETON: Any | None = None
_CLIENT_LOCK = threading.Lock()
# _CLIENT_META is kept for backward compatibility in reporting
_CLIENT_META: dict[str, Any] = {}

# Alias for compatibility with old tests that might check type
MockLLMClient = MockClient

# ======================================================================================
# INTERNAL HELPERS
# ======================================================================================


def _should_force_mock() -> bool:
    return any(os.getenv(flag, "0") == "1" for flag in ("LLM_FORCE_MOCK", "LLM_MOCK_MODE"))


def _bool_env(name: str) -> bool:
    return os.getenv(name, "0") == "1"


def _maybe_stream_simulated(full_text: str, chunk_size: int = 100) -> Generator[str, None, None]:
    for i in range(0, len(full_text), chunk_size):
        yield full_text[i : i + chunk_size]


# ======================================================================================
# PUBLIC CORE ACCESS
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
        if _CLIENT_SINGLETON is None or not is_mock_client(_CLIENT_SINGLETON):
            # Force mock via factory logic manually
            _CLIENT_SINGLETON = MockClient("forced-mock-flag")
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
    """
    c = client or _CLIENT_SINGLETON

    # Check protocol/attribute first (most reliable)
    if hasattr(c, "_is_mock_client") and c._is_mock_client:
        return True

    # Check class name
    return bool(hasattr(c, "__class__") and "Mock" in c.__class__.__name__)


# ======================================================================================
# HOOKS
# ======================================================================================

_PRE_HOOKS: list[Callable[[dict[str, Any]], None]] = []
_POST_HOOKS: list[Callable[[dict[str, Any], dict[str, Any]], None]] = []


def register_llm_pre_hook(fn: Callable[[dict[str, Any]], None]) -> None:
    _PRE_HOOKS.append(fn)


def register_llm_post_hook(fn: Callable[[dict[str, Any], dict[str, Any]], None]) -> None:
    _POST_HOOKS.append(fn)


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
    breaker = CircuitBreaker()
    if not breaker.is_allowed:
        raise RuntimeError("LLM circuit breaker OPEN – rejecting invocation temporarily.")

    # Configuration extraction
    _LLM_EXTREME_MODE = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"
    _LLM_ULTIMATE_MODE = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"

    default_retries = "20" if _LLM_ULTIMATE_MODE else ("8" if _LLM_EXTREME_MODE else "2")
    _LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", default_retries))

    default_backoff = "1.8" if _LLM_ULTIMATE_MODE else ("1.5" if _LLM_EXTREME_MODE else "1.3")
    _LLM_RETRY_BACKOFF_BASE = float(os.getenv("LLM_RETRY_BACKOFF_BASE", default_backoff))

    _LLM_RETRY_JITTER = os.getenv("LLM_RETRY_JITTER", "1") == "1"
    _LLM_ENABLE_STREAM = os.getenv("LLM_ENABLE_STREAM", "0") == "1"
    _LOG_ATTEMPTS = os.getenv("LLM_LOG_ATTEMPTS", "1") == "1"

    client = get_llm_client()
    cost_manager = CostManager()

    # REFACTORED: Use PayloadBuilder
    builder = PayloadBuilder()
    payload = builder.build(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        temperature=temperature,
        max_tokens=max_tokens,
        extra=extra,
    )

    # Pre-hooks
    for hook in _PRE_HOOKS:
        try:
            hook(payload)
        except Exception as e:
            _LOG.warning("LLM pre_hook error: %s", e)

    use_stream = stream if stream is not None else _LLM_ENABLE_STREAM

    start_build = time.time()
    retry_schedule: list[float] = []

    # REFACTORED: Use ResponseNormalizer
    normalizer = ResponseNormalizer(cost_manager=cost_manager)

    def _execute_request_with_retry() -> dict[str, Any]:
        attempts = 0
        backoff = _LLM_RETRY_BACKOFF_BASE
        last_exc: Exception | None = None

        while attempts <= _LLM_MAX_RETRIES:
            attempts += 1
            t0 = time.perf_counter()
            try:
                # Actual Call
                completion = client.chat.completions.create(
                    model=payload["model"],
                    messages=payload["messages"],
                    tools=payload["tools"],
                    tool_choice=payload["tool_choice"],
                    temperature=payload["temperature"],
                    max_tokens=payload["max_tokens"],
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0

                # REFACTORED: Delegate normalization to ResponseNormalizer
                envelope = normalizer.normalize(
                    completion=completion,
                    payload=payload,
                    latency_ms=latency_ms,
                    start_ts=start_build,
                    end_ts=time.time(),
                    retry_schedule=retry_schedule,
                    attempts=attempts,
                )

                # Post-hooks
                for hook in _POST_HOOKS:
                    try:
                        hook(payload, envelope)
                    except Exception as e:
                        _LOG.warning("LLM post_hook error: %s", e)

                return envelope

            except Exception as exc:
                last_exc = exc
                kind = RetryStrategy.classify_error(exc)
                breaker.note_error()
                cost_manager.update_metrics(None, None, None, 0, None, error_kind=kind)

                if _LOG_ATTEMPTS:
                    _LOG.warning(f"LLM attempt #{attempts} failed. Kind: {kind}. Msg: {exc}")

                if attempts > _LLM_MAX_RETRIES or not RetryStrategy.is_retry_allowed(kind):
                    if _LOG_ATTEMPTS:
                        _LOG.error(f"LLM final failure. Kind: {kind}")
                    break

                # Sleep Calculation
                sleep_for = backoff
                if _LLM_RETRY_JITTER:
                    sleep_for += random.random() * 0.25
                retry_schedule.append(round(sleep_for, 3))

                time.sleep(sleep_for)
                backoff *= _LLM_RETRY_BACKOFF_BASE

        # Final Error
        raise RuntimeError(
            f"LLM invocation failed after {attempts} attempts. Last error: {last_exc}"
        )

    if not use_stream:
        return _execute_request_with_retry()

    def _stream_gen() -> Generator[dict[str, Any], None, None]:
        envelope = _execute_request_with_retry()
        full = envelope["content"]
        for chunk in _maybe_stream_simulated(full):
            # _sanitize is now internal to normalizer, but _stream_gen needs access.
            # We can re-use normalizer._sanitize or expose it.
            # Since _maybe_stream_simulated simulates chunks from FULL content which is already sanitized in envelope["content"],
            # we don't strictly need to sanitize chunks again.
            # However, `_sanitize` was called on each chunk in original code.
            # But envelope["content"] IS sanitized.
            # So `full` is sanitized.
            # `_maybe_stream_simulated` yields substrings of `full`.
            # So they are already sanitized.
            # BUT the original code called `_sanitize(chunk)`.
            # If `full` is "ab", sanitize("a") and sanitize("b") vs sanitize("ab").
            # Usually redundant.
            # To be safe and identical:
            sanitized_chunk = normalizer._sanitize(chunk)
            yield {"delta": sanitized_chunk}
        envelope["meta"]["stream"] = True
        yield envelope

    return _stream_gen()


def invoke_chat_stream(*args: Any, **kwargs: Any) -> Generator[dict[str, Any], None, None]:
    kwargs["stream"] = True
    result = invoke_chat(*args, **kwargs)
    if not isinstance(result, Generator):
        raise RuntimeError("invoke_chat_stream expected a generator; streaming not enabled.")
    return result


def llm_health() -> dict[str, Any]:
    """
    Get health status and metrics.
    Refactored to gather data from the distributed modules.
    """
    client = _CLIENT_SINGLETON
    cost_manager = CostManager()
    breaker = CircuitBreaker()

    stats = cost_manager.get_stats()
    breaker_state = breaker.get_state()

    base = {
        "initialized": client is not None,
        "forced_mock": _should_force_mock(),
        "disable_cache": _bool_env("LLM_DISABLE_CACHE"),
    }

    # Merge stats
    base.update(stats)
    base["circuit_breaker"] = breaker_state

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
