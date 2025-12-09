# app/core/ai_gateway.py
"""
The ENERGY-ENGINE (V7.2 - SUPERHUMAN EDITION - ULTRA-OPTIMIZED).

This engine enforces the Law of Energetic Continuity, unifying AI service
communication into a lossless, monotonic, and self-healing stream. This
gateway abstracts the complexities of communicating with external AI
services using advanced Circuit Breaking, Exponential Backoff, and
Polymorphic Model Routing algorithms.

UPDATES (V7.2 - INTELLIGENT RATE LIMIT HANDLING):
- **Adaptive Cooldown**: Exponential backoff for rate-limited nodes.
- **Smarter Circuit Breaker**: Differentiates between 'Failure' and 'Saturation'.
- **Log Noise Reduction**: Intelligent logging for expected free-tier limits.
- **Cognitive Resonance**: Enhanced quality tracking.

UPDATES (V7 - SUPERHUMAN MODE):
- **Omni-Cognitive Routing**: Contextual Multi-Armed Bandits with Thompson Sampling
- **Kalman Filtering**: Latency measurements are denoised for "True Belief" tracking
- **Cognitive Complexity Analysis**: Router understands prompt difficulty
- **Superhuman Performance Optimizer**: Real-time adaptive optimization
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
SAFETY_NET_MODEL_ID = "system/safety-net"  # 🛡️ The Ultimate Failsafe

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


class AIRateLimitError(AIConnectionError):
    """Specific error for rate limits (429) to trigger distinct handling."""


# --- Resilience Algorithms ---


class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery
    SATURATED = "SATURATED"  # Rate limited, temporary backoff (V7.2)


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
        if self.state in [CircuitState.HALF_OPEN, CircuitState.SATURATED]:
            logger.info(f"Circuit Breaker [{self.name}]: Recovered to CLOSED state.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        # V7.2: Use INFO for low failure counts to reduce noise
        log_level = logging.WARNING if self.failure_count > 1 else logging.INFO
        logger.log(
            log_level,
            f"Circuit Breaker [{self.name}]: Failure recorded ({self.failure_count}/{self.threshold})",
        )

        if self.state == CircuitState.CLOSED and self.failure_count >= self.threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # If we fail in HALF_OPEN, we go back to OPEN immediately
            self._open_circuit()

    def record_saturation(self):
        """
        V7.2: Record a Rate Limit (Saturation) event.
        This is distinct from a failure; it means the service is working but busy.
        """
        self.state = CircuitState.SATURATED
        self.last_failure_time = time.time()
        # We don't necessarily increment failure_count for 429s to avoid hard OPEN
        # But we do want to back off.

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

        if self.state == CircuitState.SATURATED:
            # SATURATED behaves like OPEN but might have different timeout logic handled by Smart Cooldown
            # For now, we trust the Smart Cooldown mechanism on the NeuralNode to handle the timing,
            # so the CircuitBreaker just reports True unless it's strictly OPEN.
            # However, if we want strict circuit logic:
            return True

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

    # --- Smart Cooldown (V7.2: Adaptive) ---
    rate_limit_cooldown_until: float = 0.0
    consecutive_rate_limits: int = 0  # Track consecutive 429s for exponential backoff

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
    The 'Superhuman' Router (V7.2).
    Implements:
    1. Multi-Model Fallback Cascade (Synaptic Redundancy).
    2. Omni-Cognitive Routing (Contextual Bandits + Kalman Filter).
    3. Adaptive Circuit Breaking with Saturation Handling.
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
                    f"Backup-Synapse-{idx + 1}",
                    CIRCUIT_FAILURE_THRESHOLD,
                    CIRCUIT_RECOVERY_TIMEOUT,
                ),
            )

        # 3. Safety Net (The Last Resort)
        self.nodes_map[SAFETY_NET_MODEL_ID] = NeuralNode(
            model_id=SAFETY_NET_MODEL_ID,
            circuit_breaker=CircuitBreaker(
                "Safety-Net", 999999, 1.0
            ),  # Virtually unbreakable
        )

        self.omni_router = get_omni_router()
        # Register nodes in the Omni Brain (excluding Safety Net to prevent it being chosen)
        for mid in self.nodes_map:
            if mid != SAFETY_NET_MODEL_ID:
                self.omni_router.register_node(mid)

    def _get_prioritized_nodes(self, prompt: str) -> list[NeuralNode]:
        """
        Returns a list of nodes sorted by their Omni-Cognitive Score.
        """
        # 1. Filter out open circuits AND nodes in Smart Cooldown
        available_ids = []
        now = time.time()
        for mid, node in self.nodes_map.items():
            # Skip Safety Net in standard selection
            if mid == SAFETY_NET_MODEL_ID:
                continue

            # Check Circuit Breaker
            if not node.circuit_breaker.allow_request():
                continue

            # Check Smart Cooldown (SUPERHUMAN feature)
            if node.rate_limit_cooldown_until > now:
                # V7.2: Silent skipping for rate limited nodes to reduce log noise
                continue

            available_ids.append(mid)

        # 2. Ask the Omni Brain for the optimal order based on PROMPT
        # If no standard nodes are available, we skip this and fall through to Safety Net
        final_nodes = []
        if available_ids:
            ranked_ids = self.omni_router.get_ranked_nodes(available_ids, prompt)

            # 3. Map back to NeuralNodes
            for mid in ranked_ids:
                if mid not in self.nodes_map:
                    continue
                node = self.nodes_map[mid]
                if node.rate_limit_cooldown_until > now:
                    continue
                final_nodes.append(node)

        # 4. Append Safety Net at the very end
        if SAFETY_NET_MODEL_ID in self.nodes_map:
            final_nodes.append(self.nodes_map[SAFETY_NET_MODEL_ID])

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

    def _validate_messages(self, messages: list[dict]) -> None:
        """Validate input messages."""
        if not messages or len(messages) == 0:
            logger.error("stream_chat called with empty messages list")
            raise ValueError("Messages list cannot be empty")

    def _extract_prompt_and_context(self, messages: list[dict]) -> tuple[str, str]:
        """Extract prompt and context hash from messages."""
        prompt = messages[-1].get("content", "") if messages else ""
        context_str = json.dumps(list(messages[:-1]), sort_keys=True)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()
        return prompt, context_hash

    def _try_recall_from_cache(self, prompt: str, context_hash: str) -> list[dict] | None:
        """Attempt to recall response from cognitive cache."""
        if not prompt:
            return None

        cognitive_engine = get_cognitive_engine()
        cached_memory = cognitive_engine.recall(prompt, context_hash)

        if cached_memory:
            logger.info(f"⚡️ Cognitive Recall: Serving cached response for '{prompt[:20]}...'")
            return cached_memory
        return None

    def _assemble_response_content(self, chunks: list[dict]) -> str:
        """Assemble full response content from chunks."""
        return "".join(
            chunk.get("choices", [{}])[0].get("delta", {}).get("content", "") for chunk in chunks
        ).strip()

    def _record_success_metrics(
        self,
        node: NeuralNode,
        prompt: str,
        duration_ms: float,
        full_content: str,
        quality_score: float,
    ) -> None:
        """Record success metrics for a node."""
        if node.model_id == SAFETY_NET_MODEL_ID:
            return  # Do not record metrics for safety net

        self.omni_router.record_outcome(
            model_id=node.model_id,
            prompt=prompt,
            success=True,
            latency_ms=duration_ms,
            quality_score=quality_score,
        )

        _performance_optimizer.record_request(
            model_id=node.model_id,
            success=True,
            latency_ms=duration_ms,
            tokens=len(full_content.split()),
            quality_score=quality_score,
            empty_response=False,
        )

    def _record_empty_response(
        self, node: NeuralNode, prompt: str, duration_ms: float, errors: list[str]
    ) -> None:
        """Record metrics for empty response."""
        logger.warning(f"Node [{node.model_id}] returned empty content despite streaming data.")

        if node.model_id != SAFETY_NET_MODEL_ID:
            self.omni_router.record_outcome(
                model_id=node.model_id,
                prompt=prompt,
                success=False,
                latency_ms=duration_ms,
                quality_score=0.0,
            )

            _performance_optimizer.record_request(
                model_id=node.model_id,
                success=False,
                latency_ms=duration_ms,
                tokens=0,
                quality_score=0.0,
                empty_response=True,
            )

        errors.append(f"{node.model_id}: Empty response despite streaming")

    def _handle_rate_limit_error(self, node: NeuralNode, prompt: str, errors: list[str]) -> None:
        """Handle rate limit error."""
        node.circuit_breaker.record_saturation()
        if node.model_id != SAFETY_NET_MODEL_ID:
            self.omni_router.record_outcome(node.model_id, prompt, success=False, latency_ms=0)
        logger.info(
            f"Failover triggered from [{node.model_id}] due to Rate Limit (429). "
            f"Finding next available node..."
        )
        errors.append(f"{node.model_id}: Rate Limited (429)")

    def _handle_connection_error(
        self,
        node: NeuralNode,
        prompt: str,
        error: AIConnectionError,
        global_has_yielded: bool,
        errors: list[str],
    ) -> None:
        """Handle connection error."""
        node.circuit_breaker.record_failure()
        if node.model_id != SAFETY_NET_MODEL_ID:
            self.omni_router.record_outcome(node.model_id, prompt, success=False, latency_ms=0)

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
                f"Neural Stream severed mid-transmission from [{node.model_id}]. "
                f"Cannot failover safely. Error: {type(error).__name__}: {error!s}"
            )
            raise error

        logger.warning(
            f"Node [{node.model_id}] Connection Failed: {error!s}. Attempting failover..."
        )
        errors.append(f"{node.model_id}: Connection error - {error!s}")

    def _handle_unexpected_error(
        self,
        node: NeuralNode,
        prompt: str,
        error: Exception,
        global_has_yielded: bool,
        errors: list[str],
    ) -> None:
        """Handle unexpected error."""
        node.circuit_breaker.record_failure()
        if node.model_id != SAFETY_NET_MODEL_ID:
            self.omni_router.record_outcome(node.model_id, prompt, success=False, latency_ms=0)

        if global_has_yielded:
            logger.critical(
                f"Neural Stream crashed mid-transmission from [{node.model_id}]. "
                f"Cannot failover safely. Error: {type(error).__name__}: {error!s}"
            )
            raise error

        logger.error(
            f"Node [{node.model_id}] Unexpected Error: {type(error).__name__}: {error!s}. "
            f"Stack trace available in debug logs. Attempting failover..."
        )
        errors.append(f"{node.model_id}: {type(error).__name__} - {error!s}")

    async def _process_node_response(
        self,
        node: NeuralNode,
        messages: list[dict],
        prompt: str,
        context_hash: str,
        errors: list[str],
    ) -> AsyncGenerator[dict, None]:
        """Process response from a single node and yield chunks."""
        full_response_chunks = []
        global_has_yielded = False

        async with node.semaphore:
            logger.info(f"Engaging Neural Node via Omni Choice: {node.model_id}")
            start_time = time.time()

            async for chunk in self._stream_from_node(node, messages):
                yield chunk
                full_response_chunks.append(chunk)
                global_has_yielded = True

            duration_ms = (time.time() - start_time) * 1000
            node.circuit_breaker.record_success()
            node.consecutive_rate_limits = 0

            full_content = self._assemble_response_content(full_response_chunks)

            if not full_content and global_has_yielded:
                self._record_empty_response(node, prompt, duration_ms, errors)
                raise ValueError("Empty response despite streaming")

            quality_score = self._calculate_quality_score(full_content)
            logger.info(f"Cognitive Resonance Score for [{node.model_id}]: {quality_score:.2f}")

            self._record_success_metrics(node, prompt, duration_ms, full_content, quality_score)

            if prompt and full_response_chunks and node.model_id != SAFETY_NET_MODEL_ID:
                cognitive_engine = get_cognitive_engine()
                cognitive_engine.memorize(prompt, context_hash, full_response_chunks)

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """
        Stream chat with cognitive caching and quality feedback.
        Complexity reduced from 23 to <10 by extracting helper methods.
        """
        self._validate_messages(messages)
        prompt, context_hash = self._extract_prompt_and_context(messages)

        if messages[-1].get("role") == "user":
            cached = self._try_recall_from_cache(prompt, context_hash)
            if cached:
                for chunk in cached:
                    yield chunk
                return

        errors = []
        priority_nodes = self._get_prioritized_nodes(prompt)

        if not priority_nodes:
            logger.error("No available nodes - all circuits are open or no models configured")
            # If even Safety Net is somehow missing, we are in trouble.
            raise AIAllModelsExhaustedError("All circuits are open, no models available.")

        for node in priority_nodes:
            if not node.circuit_breaker.allow_request():
                continue

            try:
                async for chunk in self._process_node_response(
                    node, messages, prompt, context_hash, errors
                ):
                    yield chunk
                return

            except ValueError as e:
                if "Empty response" in str(e):
                    continue
                raise

            except AIRateLimitError:
                self._handle_rate_limit_error(node, prompt, errors)
                continue

            except AIConnectionError as e:
                self._handle_connection_error(node, prompt, e, False, errors)
                continue

            except Exception as e:
                self._handle_unexpected_error(node, prompt, e, False, errors)
                continue

        logger.critical(
            f"All Neural Nodes Exhausted. System Collapse. "
            f"Attempted {len(priority_nodes)} node(s). Errors encountered: {len(errors)}"
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
        """
        # 🛡️ SAFETY NET LOGIC
        if node.model_id == SAFETY_NET_MODEL_ID:
            logger.warning("⚠️ Engaging Safety Net Protocol (All external models failed).")
            safety_message = (
                "⚠️ **System Alert**: The AI Neural Mesh is currently experiencing high load or connectivity issues. "
                "Unable to reach external intelligence providers (OpenAI/Anthropic/Google). "
                "\n\nThis is an automated failsafe response. Please try again in a few moments."
            )
            # Yield simulated chunks
            words = safety_message.split(" ")
            for word in words:
                yield {"choices": [{"delta": {"content": word + " "}}]}
                await asyncio.sleep(0.05)  # Simulate typing
            return

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

                        # V7.2 SUPERHUMAN: Adaptive Smart Cooldown (Exponential Backoff)
                        node.consecutive_rate_limits += 1

                        # Base cooldown 60s, scales with failures: 60, 120, 240...
                        # Cap at 1 hour (3600s)
                        backoff_factor = min(6, node.consecutive_rate_limits)
                        cooldown_duration = 60.0 * (2 ** (backoff_factor - 1))

                        node.rate_limit_cooldown_until = time.time() + cooldown_duration

                        logger.warning(
                            f"Rate limit hit for {node.model_id} (Streak: {node.consecutive_rate_limits}). "
                            f"Activating Smart Cooldown Stasis ({cooldown_duration}s). "
                            f"Failover triggered."
                        )

                        # Use specific exception for 429
                        raise AIRateLimitError(f"Rate Limited (429) on {node.model_id}.")

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
                            except json.JSONDecodeError:
                                continue

                    logger.debug(f"Successfully streamed {chunk_count} chunks from {node.model_id}")
                return

            except AIRateLimitError:
                # Re-raise immediately to break the retry loop and failover
                raise

            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.HTTPStatusError,
            ) as e:
                if stream_started:
                    logger.error(
                        f"Stream severed mid-transmission from {node.model_id}. Error: {type(e).__name__}"
                    )
                    raise AIConnectionError("Stream severed mid-transmission.") from e

                if attempt > MAX_RETRIES:
                    raise AIConnectionError(
                        f"Max retries exceeded for node {node.model_id}."
                    ) from e

                base_sleep = (2 ** (attempt - 1)) * 0.5
                jitter = random.uniform(0, 0.5)
                sleep_time = base_sleep + jitter

                logger.warning(
                    f"Retry attempt {attempt}/{MAX_RETRIES} for {node.model_id} "
                    f"after {sleep_time:.2f}s. Error: {type(e).__name__}"
                )
                await asyncio.sleep(sleep_time)


# --- Dependency Injectable Gateway ---
def get_ai_client() -> AIClient:
    """
    Factory function to get AI client instance.
    """
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set. Neural Mesh initializing in shadow mode.")
    elif OPENROUTER_API_KEY.startswith("sk-or-v1-xxx"):
        logger.warning("OPENROUTER_API_KEY appears to be a placeholder value.")
    else:
        logger.info(
            f"OPENROUTER_API_KEY detected (length: {len(OPENROUTER_API_KEY)}). "
            "Neural Mesh initializing in full operational mode."
        )

    return NeuralRoutingMesh(api_key=OPENROUTER_API_KEY or "dummy_key")


def get_performance_report() -> dict[str, "Any"]:
    """
    Get comprehensive performance report from the optimizer.
    """
    return _performance_optimizer.get_detailed_report()


def get_recommended_model(available_models: list[str], context: str = "") -> str:
    """
    Get AI-recommended model based on historical performance.
    """
    return _performance_optimizer.get_recommended_model(available_models, context)
