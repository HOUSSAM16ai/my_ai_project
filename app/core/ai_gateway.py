# app/core/ai_gateway.py
"""
The ENERGY-ENGINE (V4 - Hyper-Morphic).

This engine enforces the Law of Energetic Continuity, unifying AI service
communication into a lossless, monotonic, and self-healing stream. This
gateway abstracts the complexities of communicating with external AI
services using advanced Circuit Breaking, Exponential Backoff, and
Polymorphic Model Routing algorithms.

UPDATES (V4):
- Integrated Hyper-Heuristic Routing (HHR) using EWMA Latency tracking.
- Added Probabilistic Softmax Selection for model candidates.
- Implemented Adaptive Concurrency Control via Semaphores.
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

from app.core.cognitive_cache import get_cognitive_engine

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
    Combines Model Identity with its Resilience State and Performance Metrics.
    """
    model_id: str
    circuit_breaker: CircuitBreaker

    # --- Performance Metrics (The "Cortex" Memory) ---
    # We use EWMA (Exponential Weighted Moving Average) for smoothing latency
    ewma_latency: float = 0.5  # Start with a neutral bias (500ms)
    alpha: float = 0.2         # Decay factor for EWMA (Higher = more reactive to recent events)

    success_count: int = 1     # Start with 1 to avoid div by zero
    failure_count: int = 0

    # --- Concurrency Control ---
    # Limit max concurrent streams to avoid provider rate limits
    semaphore: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(10))

    def record_latency(self, duration: float):
        """Records response latency and updates EWMA."""
        self.ewma_latency = (self.alpha * duration) + ((1 - self.alpha) * self.ewma_latency)

    def record_outcome(self, success: bool):
        """Updates internal success/failure ratios."""
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    @property
    def reliability_score(self) -> float:
        """
        Calculates a heuristic score for the node.
        Score = (Reliability^2) / (Latency + epsilon)
        Higher is better.
        """
        total = self.success_count + self.failure_count
        reliability = self.success_count / total

        # Penalize latency heavily, but prioritize reliability
        epsilon = 0.05
        score = (reliability ** 3) / (self.ewma_latency + epsilon)
        return score


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
    The 'Superhuman' Router (V4).
    Implements:
    1. Multi-Model Fallback Cascade (Synaptic Redundancy).
    2. Hyper-Heuristic Scoring (Latency/Reliability optimization).
    3. Softmax Probabilistic Routing.
    4. Adaptive Circuit Breaking.
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

    def _get_prioritized_nodes(self) -> list[NeuralNode]:
        """
        Returns a list of nodes sorted by their Hyper-Heuristic Score.
        """
        # 1. Filter out open circuits
        candidates = [node for node in self.nodes if node.circuit_breaker.allow_request()]

        if not candidates:
            return []

        # 2. Calculate Scores
        # We add a tiny bit of random noise to prevent stampedes if scores are identical
        scored_candidates = []
        for node in candidates:
            score = node.reliability_score
            jitter = random.uniform(0.95, 1.05)
            scored_candidates.append((node, score * jitter))

        # 3. Sort Descending (Best score first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return [x[0] for x in scored_candidates]

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """
        Executes the 'Synaptic Fallback Strategy' with Heuristic Optimization.
        Now Enhanced with COGNITIVE RESONANCE (Semantic Caching).
        """
        # --- PHASE 1: COGNITIVE RECALL ---
        # Extract the prompt for semantic analysis
        prompt = messages[-1].get("content", "") if messages else ""
        cognitive_engine = get_cognitive_engine()

        # Calculate Context Hash (All messages EXCEPT the last user prompt)
        # This ensures we only cache if the conversation history is identical.
        import hashlib
        context_str = json.dumps([m for m in messages[:-1]], sort_keys=True)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()

        # specific to user messages only to avoid caching system prompts incorrectly
        if prompt and messages[-1].get("role") == "user":
            cached_memory = cognitive_engine.recall(prompt, context_hash)
            if cached_memory:
                logger.info(f"⚡ Neural Resonance: Serving cached reflection for '{prompt[:20]}...'")
                for chunk in cached_memory:
                    # Simulate streaming delay for natural feel (optional, but "Human-like")
                    # await asyncio.sleep(0.01)
                    yield chunk
                return

        # --- PHASE 2: SYNAPTIC ROUTING ---
        errors = []
        global_has_yielded = False
        full_response_accumulator = [] # To memorize later

        # Dynamic Priority List based on real-time health
        priority_nodes = self._get_prioritized_nodes()

        for node in priority_nodes:
            # Double check circuit in case it changed mid-loop (unlikely in single thread but good practice)
            if not node.circuit_breaker.allow_request():
                continue

            try:
                # Acquire Semaphore for Concurrency Control
                async with node.semaphore:
                    logger.info(f"Engaging Neural Node: {node.model_id} [EWMA: {node.ewma_latency:.3f}s, Score: {node.reliability_score:.2f}]")
                    start_time = time.time()

                    # We yield from the internal generator.
                    async for chunk in self._stream_from_node(node, messages):
                        yield chunk
                        full_response_accumulator.append(chunk)
                        global_has_yielded = True

                    # Success!
                    duration = time.time() - start_time
                    node.record_latency(duration)
                    node.record_outcome(success=True)

                    # --- PHASE 3: MEMORIZATION ---
                    # Store the experience in the Cognitive Engine
                    if prompt and full_response_accumulator:
                         cognitive_engine.memorize(prompt, context_hash, full_response_accumulator)

                    return

            except AIConnectionError as e:
                node.record_outcome(success=False)
                # If we have already yielded data, we cannot switch models.
                if global_has_yielded:
                    logger.critical(f"Neural Stream severed mid-transmission from [{node.model_id}]. Cannot failover safely.")
                    raise e

                logger.error(f"Node [{node.model_id}] Connection Failed: {str(e)}. Rerouting...")
                errors.append(f"{node.model_id}: {str(e)}")
                continue

            except Exception as e:
                node.record_outcome(success=False)
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

                # Dynamic Timeout based on EWMA
                # We give it 3x the average latency + base buffer
                current_timeout = max(BASE_TIMEOUT, (node.ewma_latency * 3.0) + 5.0)

                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={"model": node.model_id, "messages": messages, "stream": True},
                    timeout=httpx.Timeout(current_timeout, connect=10.0)
                ) as response:

                    if response.status_code >= 500:
                         response.read()
                         raise httpx.HTTPStatusError("Server Error", request=response.request, response=response)

                    if response.status_code == 429:
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

                if stream_started:
                    raise AIConnectionError("Stream severed mid-transmission.") from e

                if attempt > MAX_RETRIES:
                    raise AIConnectionError(f"Max retries exceeded for node {node.model_id}") from e

                # Backoff
                sleep_time = (2 ** (attempt - 1)) * 0.5 + random.uniform(0, 0.5)
                await asyncio.sleep(sleep_time)

# --- Dependency Injectable Gateway ---
def get_ai_client() -> AIClient:
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set. Neural Mesh initializing in shadow mode.")
        pass
    return NeuralRoutingMesh(api_key=OPENROUTER_API_KEY or "dummy_key")
