# app/core/ai_gateway.py
"""
The ENERGY-ENGINE (V3 - Hyper-Resilient).

This engine enforces the Law of Energetic Continuity, unifying AI service
communication into a lossless, monotonic, and self-healing stream. This
gateway abstracts the complexities of communicating with external AI
services using advanced Circuit Breaking and Exponential Backoff algorithms.
"""

import asyncio
import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import httpx

# --- Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
MAX_RETRIES = 3
BASE_TIMEOUT = 30.0
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 30.0  # Seconds

logger = logging.getLogger(__name__)


# --- Custom Exceptions ---
class AIError(Exception):
    """Base class for AI Gateway errors."""


class AIProviderError(AIError):
    """Upstream provider returned an error."""


class AICircuitOpenError(AIError):
    """The circuit breaker is open; request rejected fast."""


class AIConnectionError(AIError):
    """Network or connection failure."""


# --- Resilience Algorithms ---

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """
    A Finite State Machine implementing the Circuit Breaker pattern.
    Prevents cascading failures by stopping requests to a failing service.
    """

    def __init__(self, failure_threshold: int, recovery_timeout: float):
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def record_success(self):
        """Reset failure count on success."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit Breaker: Recovered to CLOSED state.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(
            f"Circuit Breaker: Failure recorded ({self.failure_count}/{self.threshold})"
        )

        if self.state == CircuitState.CLOSED and self.failure_count >= self.threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # If we fail in HALF_OPEN, we go back to OPEN immediately
            self._open_circuit()

    def _open_circuit(self):
        self.state = CircuitState.OPEN
        logger.error(f"Circuit Breaker: OPENED. Blocking requests for {self.recovery_timeout}s.")

    def allow_request(self) -> bool:
        """Check if request should be allowed to proceed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("Circuit Breaker: Probing (HALF_OPEN).")
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: We usually allow one probe request.
        # For simplicity in this implementation, we allow it (handled by logic above).
        return True


class ResilienceKernel:
    """
    Implements retry logic with Exponential Backoff and Jitter.
    """

    @staticmethod
    async def execute_with_retry(
        func, *args, retries: int = MAX_RETRIES, **kwargs
    ) -> Any:
        last_exception = None

        for attempt in range(1, retries + 2):
            try:
                return await func(*args, **kwargs)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                # Transient network errors
                last_exception = e
                if attempt > retries:
                    break
            except httpx.HTTPStatusError as e:
                # Retry on 5xx errors or 429
                last_exception = e
                if e.response.status_code in (429, 500, 502, 503, 504):
                    if attempt > retries:
                        break
                else:
                    # Client error (400, 401, etc.) - Do not retry
                    raise AIProviderError(f"Upstream Error: {e}") from e

            # Calculate Backoff: base * 2^(attempt-1) + jitter
            sleep_time = (2 ** (attempt - 1)) * 0.5 + random.uniform(0, 0.5)
            logger.warning(
                f"Attempt {attempt}/{retries} failed. Retrying in {sleep_time:.2f}s..."
            )
            await asyncio.sleep(sleep_time)

        raise AIConnectionError(f"Max retries exceeded. Last error: {last_exception}") from last_exception


# --- Connection Management ---

class ConnectionManager:
    """
    Manages a singleton HTTP client to ensure TCP connection reuse.
    """
    _instance: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._instance is None or cls._instance.is_closed:
            logger.info("Initializing new global AI HTTP Client.")
            cls._instance = httpx.AsyncClient(
                timeout=httpx.Timeout(BASE_TIMEOUT, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance and not cls._instance.is_closed:
            await cls._instance.aclose()


# --- Protocols ---
@runtime_checkable
class AIClient(Protocol):
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        ...

    async def __aiter__(self):
        return self


# --- Concrete Implementation ---
class OpenRouterAIClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cogniforge.local",  # Required by OpenRouter
            "X-Title": "CogniForge Reality Kernel"
        }
        # Each client instance shares the global circuit breaker for the provider
        # In a multi-provider setup, this would be keyed by provider domain.
        self.circuit_breaker = _GLOBAL_CIRCUIT_BREAKER

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """
        Streams chat completion with full resilience (Circuit Breaker + Retries).
        """
        if not self.circuit_breaker.allow_request():
            raise AICircuitOpenError(
                f"Circuit is OPEN. Recovering for {self.circuit_breaker.recovery_timeout}s."
            )

        client = ConnectionManager.get_client()

        # Inner generator to handle the stream logic
        async def _make_stream_request():
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={"model": self.model, "messages": messages, "stream": True},
            ) as response:
                response.raise_for_status()
                # If we got here, headers are fine. We consider this a "success"
                # for the circuit breaker regarding reachability.
                self.circuit_breaker.record_success()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            yield chunk
                        except json.JSONDecodeError:
                            continue

        # We wrap the generator execution in the Retry Kernel
        # Note: We can only retry the *setup* of the stream. Once we start yielding,
        # we can't retry cleanly without re-sending the whole context (which might duplicate tokens).
        # So we retry the connection phase.

        # Simulating retry logic for a generator is complex.
        # We try to establish the stream. If it fails before yielding, we retry.

        attempt = 0
        while attempt <= MAX_RETRIES:
            attempt += 1
            try:
                # We consume the generator here.
                # Ideally, we would separate connection from consumption,
                # but httpx.stream combines them contextually.

                # We use a flag to know if we successfully started streaming
                stream_started = False

                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={"model": self.model, "messages": messages, "stream": True},
                ) as response:
                    response.raise_for_status()
                    self.circuit_breaker.record_success()
                    stream_started = True

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                yield chunk
                            except json.JSONDecodeError:
                                continue

                # If we exit the context manager normally, we are done.
                return

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError) as e:
                # If we started streaming and THEN failed, we probably shouldn't auto-retry
                # blindly as it might confuse the user, but for now we assume
                # strict resilience is preferred if the stream dies early.
                # However, re-yielding duplicate chunks is bad.
                # A robust implementation checks if ANY data was yielded.

                if stream_started:
                    # We already sent data to the user. Abort retry to avoid duplication/confusion.
                    logger.error(f"Stream interrupted after start: {e}")
                    raise AIConnectionError("Stream interrupted.") from e

                # Analyze error for Circuit Breaker
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500:
                    self.circuit_breaker.record_failure()
                elif isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
                    self.circuit_breaker.record_failure()

                # Check if we should retry
                should_retry = False
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code in (429, 500, 502, 503, 504):
                    should_retry = True
                elif isinstance(e, (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)):
                    should_retry = True

                if not should_retry or attempt > MAX_RETRIES:
                    raise AIProviderError(f"Stream failed after {attempt} attempts: {e}") from e

                # Backoff
                sleep_time = (2 ** (attempt - 1)) * 0.5 + random.uniform(0, 0.5)
                logger.warning(f"Streaming setup failed (Attempt {attempt}). Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)


# --- Global Singletons ---
_GLOBAL_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=CIRCUIT_FAILURE_THRESHOLD,
    recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT
)

# --- Dependency Injectable Gateway ---
def get_ai_client() -> AIClient:
    if not OPENROUTER_API_KEY:
        # For development/testing without keys, we might want to warn or raise.
        # But existing code raised ValueError.
        raise ValueError("OPENROUTER_API_KEY is not set.")
    return OpenRouterAIClient(api_key=OPENROUTER_API_KEY)
