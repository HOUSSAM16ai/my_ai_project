# app/core/ai_gateway.py
"""
The ENERGY-ENGINE (V3 - Hyper-Resilient).

This engine enforces the Law of Energetic Continuity, unifying AI service
communication into a lossless, monotonic, and self-healing stream. This
gateway abstracts the complexities of communicating with external AI
services using advanced Circuit Breaking, Exponential Backoff, and
Polymorphic Model Routing algorithms.
"""

import asyncio
import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import httpx

# --- Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# The "Holographic Registry" of Models
# We prioritize "Intelligence" (Sonnet) -> "Versatility" (GPT-4o) -> "Speed" (Haiku/Instant)
PRIMARY_MODEL = "anthropic/claude-3.5-sonnet"
FALLBACK_MODELS = [
    "openai/gpt-4o",
    "anthropic/claude-instant-1.2"
]

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

class AIAllModelsExhaustedError(AIError):
    """All available AI models in the Neural Mesh have failed."""


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

    def __init__(self, name: str, failure_threshold: int, recovery_timeout: float):
        self.name = name
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def record_success(self):
        """Reset failure count on success."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit Breaker [{self.name}]: Recovered to CLOSED state.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(
            f"Circuit Breaker [{self.name}]: Failure recorded ({self.failure_count}/{self.threshold})"
        )

        if self.state == CircuitState.CLOSED and self.failure_count >= self.threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # If we fail in HALF_OPEN, we go back to OPEN immediately
            self._open_circuit()

    def _open_circuit(self):
        self.state = CircuitState.OPEN
        logger.error(f"Circuit Breaker [{self.name}]: OPENED. Blocking requests for {self.recovery_timeout}s.")

    def allow_request(self) -> bool:
        """Check if request should be allowed to proceed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit Breaker [{self.name}]: Probing (HALF_OPEN).")
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        return True


@dataclass
class NeuralNode:
    """
    Represents a single node in the AI Intelligence Mesh.
    Combines Model Identity with its Resilience State (Circuit Breaker).
    """
    model_id: str
    circuit_breaker: CircuitBreaker
    latency_history: list[float] = field(default_factory=list)

    def record_latency(self, duration: float):
        """Records response latency for predictive optimization (Future Use)."""
        self.latency_history.append(duration)
        if len(self.latency_history) > 100:
            self.latency_history.pop(0)


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


# --- The Omniscient Router ---

class NeuralRoutingMesh:
    """
    The 'Superhuman' Router.
    Implements:
    1. Multi-Model Fallback Cascade (Synaptic Redundancy).
    2. Adaptive Circuit Breaking per Model.
    3. Self-Healing Stream Recovery.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cogniforge.local",
            "X-Title": "CogniForge Reality Kernel"
        }

        # Initialize the Neural Nodes (The Brains)
        self.nodes: list[NeuralNode] = []

        # 1. Primary Cortex
        self.nodes.append(NeuralNode(
            model_id=PRIMARY_MODEL,
            circuit_breaker=CircuitBreaker("Primary-Cortex", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT)
        ))

        # 2. Backup Synapses (Fallbacks)
        for idx, model_id in enumerate(FALLBACK_MODELS):
            self.nodes.append(NeuralNode(
                model_id=model_id,
                circuit_breaker=CircuitBreaker(f"Backup-Synapse-{idx+1}", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT)
            ))

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """
        Executes the 'Synaptic Fallback Strategy'.
        If the Primary Cortex fails, it instantly reroutes to Backup Synapses.
        """
        errors = []
        global_has_yielded = False

        for node in self.nodes:
            # 1. Check Circuit Health
            if not node.circuit_breaker.allow_request():
                logger.warning(f"Skipping [{node.model_id}]: Circuit OPEN.")
                continue

            try:
                # 2. Attempt Connection
                logger.info(f"Engaging Neural Node: {node.model_id}")
                start_time = time.time()

                # We yield from the internal generator.
                async for chunk in self._stream_from_node(node, messages):
                    yield chunk
                    global_has_yielded = True

                # Success!
                duration = time.time() - start_time
                node.record_latency(duration)
                return

            except AIConnectionError as e:
                # If we have already yielded data, we cannot switch models as it would
                # corrupt the stream (duplicate data). We must abort.
                if global_has_yielded:
                    logger.critical(f"Neural Stream severed mid-transmission from [{node.model_id}]. Cannot failover safely.")
                    raise e

                # Otherwise, log and continue to next node
                logger.error(f"Node [{node.model_id}] Connection Failed: {str(e)}. Rerouting...")
                errors.append(f"{node.model_id}: {str(e)}")
                continue

            except Exception as e:
                if global_has_yielded:
                     logger.critical(f"Neural Stream crashed mid-transmission from [{node.model_id}]. Cannot failover safely.")
                     raise e

                logger.error(f"Node [{node.model_id}] Unexpected Error: {str(e)}. Rerouting...")
                errors.append(f"{node.model_id}: {str(e)}")
                continue

        # If we get here, ALL nodes failed.
        logger.critical("All Neural Nodes Exhausted. System Collapse.")
        raise AIAllModelsExhaustedError(f"Complete Failure. Errors: {errors}")

    async def _stream_from_node(self, node: NeuralNode, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """
        Internal generator for a specific node with Retry Logic.
        """
        client = ConnectionManager.get_client()

        attempt = 0
        while attempt <= MAX_RETRIES:
            attempt += 1
            try:
                stream_started = False
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={"model": node.model_id, "messages": messages, "stream": True},
                ) as response:

                    if response.status_code >= 500:
                         # Server Error - Retryable, but counts as failure for Circuit
                         response.read() # Consume to ensure connection close
                         raise httpx.HTTPStatusError("Server Error", request=response.request, response=response)

                    if response.status_code == 429:
                        # Rate Limit - Retryable
                        response.read()
                        raise httpx.HTTPStatusError("Rate Limited", request=response.request, response=response)

                    response.raise_for_status()

                    # Connection established - Circuit is healthy
                    node.circuit_breaker.record_success()
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
                return

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError) as e:
                # Update Circuit Breaker
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500:
                    node.circuit_breaker.record_failure()
                elif isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
                    node.circuit_breaker.record_failure()

                # Safety Check: If we already sent data, we CANNOT retry seamlessly.
                if stream_started:
                    # We raise a specific error that the parent catches
                    raise AIConnectionError("Stream severed mid-transmission.") from e

                # Check Max Retries
                if attempt > MAX_RETRIES:
                    # Re-raise to trigger fallback to next Node
                    # Wrap in generic Exception if needed, but raising the original is fine
                    # as long as the parent catches it.
                    # We wrap in AIConnectionError to signify it's a "connection attempt" failure
                    raise AIConnectionError(f"Max retries exceeded for node {node.model_id}") from e

                # Backoff
                sleep_time = (2 ** (attempt - 1)) * 0.5 + random.uniform(0, 0.5)
                await asyncio.sleep(sleep_time)

# --- Dependency Injectable Gateway ---
def get_ai_client() -> AIClient:
    if not OPENROUTER_API_KEY:
        # Fallback for CI/Test environments where key might be missing
        # We allow instantiation but it will fail on request if not mocked
        logger.warning("OPENROUTER_API_KEY not set. Neural Mesh initializing in shadow mode.")
        pass
    return NeuralRoutingMesh(api_key=OPENROUTER_API_KEY or "dummy_key")
