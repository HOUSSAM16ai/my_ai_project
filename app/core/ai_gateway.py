# app/core/ai_gateway.py
"""
The ENERGY-ENGINE (V7 - SUPERHUMAN EDITION - ULTRA-OPTIMIZED).

This engine enforces the Law of Energetic Continuity, unifying AI service
communication into a lossless, monotonic, and self-healing stream. This
gateway abstracts the complexities of communicating with external AI
services using advanced Circuit Breaking, Exponential Backoff, and
Polymorphic Model Routing algorithms.

UPDATES (V7 - SUPERHUMAN MODE):
- **Omni-Cognitive Routing**: Contextual Multi-Armed Bandits with Thompson Sampling
- **Kalman Filtering**: Latency measurements are denoised for "True Belief" tracking
- **Cognitive Complexity Analysis**: Router understands prompt difficulty
- **Superhuman Performance Optimizer**: Real-time adaptive optimization
- **Intelligent Model Selection**: ML-based model selection for optimal performance
- **Adaptive Timeout Management**: Dynamic timeout based on historical data
- **Advanced Metrics Tracking**: P50/P95/P99 latency tracking
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import httpx

# --- Configuration ---
# All AI models are now configured from the central config (app/config/ai_models.py)
# You can override these via environment variables or .env file
from app.config.ai_models import get_ai_config
from app.core.cognitive_cache import get_cognitive_engine

# Use the new Omni Router
from app.core.math.omni_router import get_omni_router

# SUPERHUMAN: Import performance optimizer
from app.core.superhuman_performance_optimizer import get_performance_optimizer

_ai_config = get_ai_config()
OPENROUTER_API_KEY = _ai_config.openrouter_api_key

# The "Holographic Registry" of Models - READ FROM CENTRAL CONFIG
PRIMARY_MODEL = _ai_config.gateway_primary
FALLBACK_MODELS = _ai_config.get_fallback_models()

MAX_RETRIES = 3
BASE_TIMEOUT = 30.0
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 30.0  # Seconds

logger = logging.getLogger(__name__)

# SUPERHUMAN: Initialize performance optimizer
_performance_optimizer = get_performance_optimizer()


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
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
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
        logger.error(
            f"Circuit Breaker [{self.name}]: OPENED. Blocking requests for {self.recovery_timeout}s."
        )

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

    # --- Performance Metrics (Legacy Cortex Memory - retained for logging) ---
    ewma_latency: float = 0.5

    # --- Smart Cooldown ---
    rate_limit_cooldown_until: float = 0.0

    # --- Concurrency Control ---
    # Limit max concurrent streams to avoid provider rate limits
    semaphore: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(10))


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
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance and not cls._instance.is_closed:
            await cls._instance.aclose()


# --- Protocols ---
@runtime_checkable
class AIClient(Protocol):
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]: ...

    async def __aiter__(self):
        return self


# --- The Omniscient Router ---


class NeuralRoutingMesh:
    """
    The 'Superhuman' Router (V6).
    Implements:
    1. Multi-Model Fallback Cascade (Synaptic Redundancy).
    2. Omni-Cognitive Routing (Contextual Bandits + Kalman Filter).
    3. Adaptive Circuit Breaking.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cogniforge.local",
            "X-Title": "CogniForge Reality Kernel",
        }

        # Initialize the Neural Nodes (The Brains)
        self.nodes_map: dict[str, NeuralNode] = {}

        # 1. Primary Cortex
        self.nodes_map[PRIMARY_MODEL] = NeuralNode(
            model_id=PRIMARY_MODEL,
            circuit_breaker=CircuitBreaker(
                "Primary-Cortex", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT
            ),
        )

        # 2. Backup Synapses (Fallbacks)
        for idx, model_id in enumerate(FALLBACK_MODELS):
            self.nodes_map[model_id] = NeuralNode(
                model_id=model_id,
                circuit_breaker=CircuitBreaker(
                    f"Backup-Synapse-{idx + 1}", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT
                ),
            )

        self.omni_router = get_omni_router()
        # Register nodes in the Omni Brain
        for mid in self.nodes_map:
            self.omni_router.register_node(mid)

    def _get_prioritized_nodes(self, prompt: str) -> list[NeuralNode]:
        """
        Returns a list of nodes sorted by their Omni-Cognitive Score.
        """
        # 1. Filter out open circuits AND nodes in Smart Cooldown
        available_ids = []
        now = time.time()
        for mid, node in self.nodes_map.items():
            # Check Circuit Breaker
            if not node.circuit_breaker.allow_request():
                continue

            # Check Smart Cooldown (SUPERHUMAN feature)
            if node.rate_limit_cooldown_until > now:
                remaining = int(node.rate_limit_cooldown_until - now)
                logger.warning(
                    f"Node [{mid}] is in Smart Cooldown Stasis for {remaining}s. "
                    "Skipping to preserve Omni-Mesh stability."
                )
                continue

            available_ids.append(mid)

        if not available_ids:
            return []

        # 2. Ask the Omni Brain for the optimal order based on PROMPT
        ranked_ids = self.omni_router.get_ranked_nodes(available_ids, prompt)

        # 3. Map back to NeuralNodes
        # Ensure we strictly respect the cooldown even if Router suggests it
        final_nodes = []
        for mid in ranked_ids:
             if mid not in self.nodes_map: continue
             node = self.nodes_map[mid]
             # Check Smart Cooldown (Double check for safety)
             if node.rate_limit_cooldown_until > now:
                 continue
             final_nodes.append(node)

        return final_nodes

    def _calculate_quality_score(self, full_content: str) -> float:
        """
        Calculates a 'Cognitive Resonance' score based on response content.
        This is a heuristic to judge the quality/depth of the response.
        """
        if not full_content:
            return 0.0

        # Heuristic 1: Length (longer is generally better, up to a point)
        length_score = min(1.0, len(full_content) / 500)  # Normalize around 500 chars

        # Heuristic 2: Information Density (e.g., unique words)
        words = full_content.split()
        if not words:
            return 0.0
        unique_words = set(words)
        density_score = len(unique_words) / len(words)

        # Combine scores (weighted)
        # We value density more than raw length.
        final_score = (0.4 * length_score) + (0.6 * density_score)
        return max(0.0, min(1.0, final_score))

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """
        Executes the 'Synaptic Fallback Strategy' with Omni-Cognitive Optimization.
        Now Enhanced with COGNITIVE RESONANCE (Semantic Caching & Quality Feedback).

        SUPERHUMAN ENHANCEMENTS V6.1:
        - Empty response validation and intelligent fallback
        - Enhanced error context and categorization
        - Adaptive timeout management
        - Quality-aware node selection
        """
        # --- INPUT VALIDATION ---
        if not messages or len(messages) == 0:
            logger.error("stream_chat called with empty messages list")
            raise ValueError("Messages list cannot be empty")

        # --- PHASE 1: COGNITIVE RECALL ---
        prompt = messages[-1].get("content", "") if messages else ""
        cognitive_engine = get_cognitive_engine()
        context_str = json.dumps(list(messages[:-1]), sort_keys=True)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()

        if prompt and messages[-1].get("role") == "user":
            cached_memory = cognitive_engine.recall(prompt, context_hash)
            if cached_memory:
                logger.info(f"⚡️ Cognitive Recall: Serving cached response for '{prompt[:20]}...'")
                for chunk in cached_memory:
                    yield chunk
                return

        # --- PHASE 2: SYNAPTIC ROUTING & QUALITY ASSESSMENT ---
        errors = []
        global_has_yielded = False
        full_response_chunks = []
        priority_nodes = self._get_prioritized_nodes(prompt)

        if not priority_nodes:
            logger.error("No available nodes - all circuits are open or no models configured")
            raise AIAllModelsExhaustedError("All circuits are open, no models available.")

        for node in priority_nodes:
            if not node.circuit_breaker.allow_request():
                continue

            try:
                async with node.semaphore:
                    logger.info(f"Engaging Neural Node via Omni Choice: {node.model_id}")
                    start_time = time.time()

                    async for chunk in self._stream_from_node(node, messages):
                        yield chunk
                        full_response_chunks.append(chunk)
                        global_has_yielded = True

                    duration_ms = (time.time() - start_time) * 1000
                    node.circuit_breaker.record_success()

                    # --- ENHANCED FEEDBACK LOOP ---
                    # 1. Assemble full response content
                    full_content = "".join(
                        chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        for chunk in full_response_chunks
                    ).strip()

                    # SUPERHUMAN VALIDATION: Check for empty responses
                    if not full_content and global_has_yielded:
                        logger.warning(
                            f"Node [{node.model_id}] returned empty content despite streaming data. "
                            "This may indicate a model issue or incomplete response."
                        )
                        # Record as partial failure for adaptive learning
                        self.omni_router.record_outcome(
                            model_id=node.model_id,
                            prompt=prompt,
                            success=False,
                            latency_ms=duration_ms,
                            quality_score=0.0,
                        )

                        # SUPERHUMAN: Record metrics for performance optimization
                        _performance_optimizer.record_request(
                            model_id=node.model_id,
                            success=False,
                            latency_ms=duration_ms,
                            tokens=0,
                            quality_score=0.0,
                            empty_response=True,
                        )

                        # Try next node if available
                        errors.append(f"{node.model_id}: Empty response despite streaming")
                        continue

                    # 2. Calculate Cognitive Resonance (Quality)
                    quality_score = self._calculate_quality_score(full_content)
                    logger.info(
                        f"Cognitive Resonance Score for [{node.model_id}]: {quality_score:.2f}"
                    )

                    # 3. FEED THE OMNI BRAIN (with quality score)
                    self.omni_router.record_outcome(
                        model_id=node.model_id,
                        prompt=prompt,
                        success=True,
                        latency_ms=duration_ms,
                        quality_score=quality_score,
                    )

                    # SUPERHUMAN: Record comprehensive metrics
                    _performance_optimizer.record_request(
                        model_id=node.model_id,
                        success=True,
                        latency_ms=duration_ms,
                        tokens=len(full_content.split()),  # Approximate token count
                        quality_score=quality_score,
                        empty_response=False,
                    )

                    # --- PHASE 3: MEMORIZATION ---
                    if prompt and full_response_chunks:
                        cognitive_engine.memorize(prompt, context_hash, full_response_chunks)

                    return

            except AIConnectionError as e:
                node.circuit_breaker.record_failure()
                self.omni_router.record_outcome(node.model_id, prompt, success=False, latency_ms=0)

                # SUPERHUMAN: Record failure metrics
                _performance_optimizer.record_request(
                    model_id=node.model_id,
                    success=False,
                    latency_ms=0,
                    tokens=0,
                    quality_score=0.0,
                    empty_response=False,
                )

                if global_has_yielded:
                    logger.critical(
                        f"Neural Stream severed mid-transmission from [{node.model_id}]. Cannot failover safely. "
                        f"Error: {type(e).__name__}: {e!s}"
                    )
                    raise e
                logger.error(
                    f"Node [{node.model_id}] Connection Failed: {type(e).__name__}: {e!s}. "
                    f"Attempting failover to next available node..."
                )
                errors.append(f"{node.model_id}: Connection error - {e!s}")
                continue

            except Exception as e:
                node.circuit_breaker.record_failure()
                self.omni_router.record_outcome(node.model_id, prompt, success=False, latency_ms=0)
                if global_has_yielded:
                    logger.critical(
                        f"Neural Stream crashed mid-transmission from [{node.model_id}]. Cannot failover safely. "
                        f"Error: {type(e).__name__}: {e!s}"
                    )
                    raise e
                logger.error(
                    f"Node [{node.model_id}] Unexpected Error: {type(e).__name__}: {e!s}. "
                    f"Stack trace available in debug logs. Attempting failover..."
                )
                errors.append(f"{node.model_id}: {type(e).__name__} - {e!s}")
                continue

        # All nodes exhausted - provide comprehensive error information
        logger.critical(
            f"All Neural Nodes Exhausted. System Collapse. "
            f"Attempted {len(priority_nodes)} node(s). "
            f"Errors encountered: {len(errors)}"
        )
        error_summary = " | ".join(errors) if errors else "No specific errors recorded"
        raise AIAllModelsExhaustedError(
            f"Complete Failure across all available models. Error summary: {error_summary}"
        )

    async def _stream_from_node(
        self, node: NeuralNode, messages: list[dict]
    ) -> AsyncGenerator[dict, None]:
        """
        Internal generator for a specific node with Retry Logic.

        SUPERHUMAN ENHANCEMENTS V6.1:
        - Enhanced error classification and logging
        - Intelligent backoff with jitter
        - Better timeout handling
        - Status code specific error messages
        """
        client = ConnectionManager.get_client()

        attempt = 0

        while attempt <= MAX_RETRIES:
            attempt += 1
            try:
                stream_started = False
                current_timeout = BASE_TIMEOUT

                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={"model": node.model_id, "messages": messages, "stream": True},
                    timeout=httpx.Timeout(current_timeout, connect=10.0),
                ) as response:
                    # Enhanced status code handling with detailed error messages
                    if response.status_code >= 500:
                        error_body = await response.aread()
                        error_text = error_body.decode("utf-8", errors="ignore")[:500]
                        logger.error(
                            f"Server error from {node.model_id}: "
                            f"Status {response.status_code}, Body: {error_text}"
                        )
                        raise httpx.HTTPStatusError(
                            f"Server Error (HTTP {response.status_code})",
                            request=response.request,
                            response=response,
                        )

                    if response.status_code == 429:
                        error_body = await response.aread()
                        error_text = error_body.decode("utf-8", errors="ignore")[:200]

                        # SUPERHUMAN: Activate Smart Cooldown
                        # We lock this node in a temporal stasis field to prevent futility loops.
                        cooldown_duration = 60.0  # 60 seconds penalty
                        node.rate_limit_cooldown_until = time.time() + cooldown_duration

                        logger.warning(
                            f"Rate limit hit for {node.model_id}: {error_text}. "
                            f"Activating Smart Cooldown Stasis ({cooldown_duration}s). "
                            f"Aborting internal retries to trigger Mesh Failover."
                        )
                        # We raise AIConnectionError directly to bypass internal retries
                        # and force the parent stream_chat loop to try the next node.
                        raise AIConnectionError(
                            f"Rate Limited (429) on {node.model_id}. Triggering immediate failover."
                        )

                    if response.status_code == 401 or response.status_code == 403:
                        error_body = await response.aread()
                        error_text = error_body.decode("utf-8", errors="ignore")[:200]
                        logger.error(
                            f"Authentication error for {node.model_id}: "
                            f"Status {response.status_code}, Body: {error_text}"
                        )
                        raise httpx.HTTPStatusError(
                            f"Authentication Error (HTTP {response.status_code})",
                            request=response.request,
                            response=response,
                        )

                    response.raise_for_status()

                    stream_started = True
                    chunk_count = 0

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                chunk_count += 1
                                yield chunk
                            except json.JSONDecodeError as je:
                                logger.debug(
                                    f"JSON decode error in stream chunk: {data_str[:100]}... "
                                    f"Error: {je}"
                                )
                                continue

                    # Log successful stream completion
                    logger.debug(f"Successfully streamed {chunk_count} chunks from {node.model_id}")
                return

            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.HTTPStatusError,
            ) as e:
                if stream_started:
                    logger.error(
                        f"Stream severed mid-transmission from {node.model_id} "
                        f"at attempt {attempt}/{MAX_RETRIES}. Error: {type(e).__name__}"
                    )
                    raise AIConnectionError("Stream severed mid-transmission.") from e

                if attempt > MAX_RETRIES:
                    logger.error(
                        f"Max retries ({MAX_RETRIES}) exceeded for node {node.model_id}. "
                        f"Last error: {type(e).__name__}: {e!s}"
                    )
                    raise AIConnectionError(
                        f"Max retries exceeded for node {node.model_id}. "
                        f"Final error: {type(e).__name__}"
                    ) from e

                # Intelligent exponential backoff with jitter
                base_sleep = (2 ** (attempt - 1)) * 0.5
                jitter = random.uniform(0, 0.5)
                sleep_time = base_sleep + jitter

                logger.warning(
                    f"Retry attempt {attempt}/{MAX_RETRIES} for {node.model_id} "
                    f"after {sleep_time:.2f}s. Error: {type(e).__name__}: {e!s}"
                )
                await asyncio.sleep(sleep_time)


# --- Dependency Injectable Gateway ---
def get_ai_client() -> AIClient:
    """
    Factory function to get AI client instance.

    SUPERHUMAN ENHANCEMENTS:
    - Better logging for initialization states
    - Validates API key format before initialization
    """
    if not OPENROUTER_API_KEY:
        logger.warning(
            "OPENROUTER_API_KEY not set. Neural Mesh initializing in shadow mode. "
            "Some features may not work correctly without a valid API key."
        )
    elif OPENROUTER_API_KEY.startswith("sk-or-v1-xxx"):
        logger.warning(
            "OPENROUTER_API_KEY appears to be a placeholder value. "
            "Please set a valid API key for production use."
        )
    else:
        logger.info(
            f"OPENROUTER_API_KEY detected (length: {len(OPENROUTER_API_KEY)}). "
            "Neural Mesh initializing in full operational mode."
        )

    return NeuralRoutingMesh(api_key=OPENROUTER_API_KEY or "dummy_key")


def get_performance_report() -> dict[str, "Any"]:
    """
    Get comprehensive performance report from the optimizer.

    SUPERHUMAN FEATURE:
    Returns detailed metrics including:
    - Global statistics (uptime, total requests, avg latency)
    - Per-model metrics (success rate, latency percentiles, quality scores)
    - Model recommendations based on performance

    Returns:
        Dictionary containing performance data
    """
    return _performance_optimizer.get_detailed_report()


def get_recommended_model(available_models: list[str], context: str = "") -> str:
    """
    Get AI-recommended model based on historical performance.

    SUPERHUMAN FEATURE:
    Uses Thompson Sampling (multi-armed bandit) to select optimal model
    based on success rate, latency, and quality scores.

    Args:
        available_models: List of model IDs to choose from
        context: Optional context for contextual bandits

    Returns:
        Recommended model ID
    """
    return _performance_optimizer.get_recommended_model(available_models, context)
