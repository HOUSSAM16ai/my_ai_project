"""
Neural Routing Mesh Module.
Simplified for reliability and performance.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

import httpx

# Config imports
from app.config.ai_models import get_ai_config
from app.core.cognitive_cache import get_cognitive_engine
from app.core.gateway.circuit_breaker import CircuitBreaker
from app.core.gateway.connection import BASE_TIMEOUT, ConnectionManager

# Import new atomic modules
from app.core.gateway.exceptions import (
    AIAllModelsExhaustedError,
    AIConnectionError,
    AIRateLimitError,
)
from app.core.gateway.node import NeuralNode

logger = logging.getLogger(__name__)

# Constants
_ai_config = get_ai_config()
PRIMARY_MODEL = _ai_config.gateway_primary
FALLBACK_MODELS = _ai_config.get_fallback_models()
SAFETY_NET_MODEL_ID = "system/safety-net"
MAX_RETRIES = 3
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 30.0

@runtime_checkable
class AIClient(Protocol):
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]: ...

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7
    ) -> str: ...

    async def __aiter__(self):
        return self

class NeuralRoutingMesh:
    """
    The 'Overmind' Router.
    Refactored for Simplicity and Reliability.
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

        self.nodes_map: dict[str, NeuralNode] = self._initialize_nodes()

    def _initialize_nodes(self) -> dict[str, NeuralNode]:
        nodes = {}
        # 1. Primary Cortex
        nodes[PRIMARY_MODEL] = NeuralNode(
            model_id=PRIMARY_MODEL,
            circuit_breaker=CircuitBreaker(
                "Primary-Cortex", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT
            ),
        )

        # 2. Backup Synapses (Fallbacks)
        for idx, model_id in enumerate(FALLBACK_MODELS):
            nodes[model_id] = NeuralNode(
                model_id=model_id,
                circuit_breaker=CircuitBreaker(
                    f"Backup-Synapse-{idx + 1}",
                    CIRCUIT_FAILURE_THRESHOLD,
                    CIRCUIT_RECOVERY_TIMEOUT,
                ),
            )

        # 3. Safety Net (The Last Resort)
        nodes[SAFETY_NET_MODEL_ID] = NeuralNode(
            model_id=SAFETY_NET_MODEL_ID,
            circuit_breaker=CircuitBreaker(
                "Safety-Net", 999999, 1.0
            ),  # Virtually unbreakable
        )
        return nodes

    def _get_prioritized_nodes(self, prompt: str) -> list[NeuralNode]:
        """
        Returns a list of nodes sorted by priority (Primary -> Fallback -> Safety Net).
        """
        final_nodes = []
        now = time.time()

        # Check Primary
        if PRIMARY_MODEL in self.nodes_map:
            node = self.nodes_map[PRIMARY_MODEL]
            if node.circuit_breaker.allow_request() and node.rate_limit_cooldown_until <= now:
                final_nodes.append(node)

        # Check Fallbacks
        for model_id in FALLBACK_MODELS:
            if model_id in self.nodes_map:
                node = self.nodes_map[model_id]
                if node.circuit_breaker.allow_request() and node.rate_limit_cooldown_until <= now:
                    final_nodes.append(node)

        # Always append Safety Net at the end
        if SAFETY_NET_MODEL_ID in self.nodes_map:
            final_nodes.append(self.nodes_map[SAFETY_NET_MODEL_ID])

        return final_nodes

    def _record_metrics(
        self,
        node: NeuralNode,
        prompt: str,
        duration_ms: float,
        success: bool,
    ):
        if node.model_id == SAFETY_NET_MODEL_ID:
            return

        # Simple logging instead of complex analytics
        log_method = logger.info if success else logger.warning
        log_method(
            f"AI Request: {node.model_id} | Success: {success} | Latency: {duration_ms:.2f}ms"
        )

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        if not messages:
            raise ValueError("Messages list cannot be empty")

        prompt = messages[-1].get("content", "")
        context_str = json.dumps(list(messages[:-1]), sort_keys=True)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()

        # Check Cache
        if messages[-1].get("role") == "user":
            cached_memory = get_cognitive_engine().recall(prompt, context_hash)
            if cached_memory:
                logger.info(f"⚡️ Cognitive Recall: Serving cached response for '{prompt[:20]}...'")
                for chunk in cached_memory:
                    yield chunk
                return

        priority_nodes = self._get_prioritized_nodes(prompt)
        if not priority_nodes:
            raise AIAllModelsExhaustedError("All circuits are open, no models available.")

        errors = []

        for node in priority_nodes:
            if not node.circuit_breaker.allow_request():
                continue

            start_time = time.time()
            try:
                # Use a dedicated processor/helper to stream from this node
                full_response_chunks = []
                chunks_yielded = 0

                async for chunk in self._stream_from_node_with_retry(node, messages):
                    yield chunk
                    full_response_chunks.append(chunk)
                    chunks_yielded += 1

                duration = (time.time() - start_time) * 1000
                node.circuit_breaker.record_success()
                self._record_metrics(node, prompt, duration, True)

                if node.model_id != SAFETY_NET_MODEL_ID:
                     get_cognitive_engine().memorize(prompt, context_hash, full_response_chunks)

                return

            except AIRateLimitError:
                duration = (time.time() - start_time) * 1000
                node.circuit_breaker.record_saturation()
                self._record_metrics(node, prompt, duration, False)
                errors.append(f"{node.model_id}: Rate Limited")
                continue

            except (AIConnectionError, ValueError, Exception) as e:
                duration = (time.time() - start_time) * 1000
                # IMPORTANT FIX: If we have already yielded data, we CANNOT failover.
                if 'chunks_yielded' in locals() and chunks_yielded > 0:
                    logger.critical(f"Stream severed mid-transmission from {node.model_id}. Cannot failover safely.")
                    node.circuit_breaker.record_failure()
                    self._record_metrics(node, prompt, duration, False)
                    raise e

                node.circuit_breaker.record_failure()
                self._record_metrics(node, prompt, duration, False)
                errors.append(f"{node.model_id}: {e!s}")
                logger.warning(f"Node {node.model_id} failed: {e}")
                continue

        raise AIAllModelsExhaustedError(f"All models failed. Errors: {errors}")

    async def _stream_from_node_with_retry(
        self, node: NeuralNode, messages: list[dict]
    ) -> AsyncGenerator[dict, None]:
        """
        Streams from a node with retry logic.
        """
        # Safety Net Implementation
        if node.model_id == SAFETY_NET_MODEL_ID:
            logger.warning("⚠️ Engaging Safety Net Protocol.")
            safety_msg = "⚠️ System Alert: Unable to reach external intelligence providers."
            for word in safety_msg.split(" "):
                yield {"choices": [{"delta": {"content": word + " "}}]}
                await asyncio.sleep(0.05)
            return

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
                    timeout=httpx.Timeout(BASE_TIMEOUT, connect=10.0),
                ) as response:

                    if response.status_code == 429:
                        # Adaptive Cooldown Logic
                        node.consecutive_rate_limits += 1
                        backoff = min(6, node.consecutive_rate_limits)
                        cooldown = 60.0 * (2 ** (backoff - 1))
                        node.rate_limit_cooldown_until = time.time() + cooldown
                        raise AIRateLimitError(f"Rate limit 429 on {node.model_id}")

                    if response.status_code >= 400:
                        raise httpx.HTTPStatusError(
                            f"HTTP {response.status_code}", request=response.request, response=response
                        )

                    stream_started = True
                    node.consecutive_rate_limits = 0

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

                    if chunk_count == 0:
                        raise ValueError("Empty response from provider")

                    return

            except AIRateLimitError:
                raise

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError, ValueError) as e:
                if stream_started:
                    raise AIConnectionError("Stream severed") from e

                if attempt > MAX_RETRIES:
                     raise AIConnectionError("Max retries exceeded") from e

                await asyncio.sleep(0.5 * attempt)

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7
    ) -> str:
        """
        دالة مساعدة لإرسال رسالة وتلقي رد كامل (غير متدفق).
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        full_response = []
        try:
            async for chunk in self.stream_chat(messages):
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    full_response.append(content)
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            raise

        return "".join(full_response)

def get_ai_client() -> AIClient:
    """
    Factory function to get AI client instance.
    """
    api_key = _ai_config.openrouter_api_key
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. Neural Mesh initializing in shadow mode.")
    elif api_key.startswith("sk-or-v1-xxx"):
        logger.warning("OPENROUTER_API_KEY appears to be a placeholder value.")
    else:
        logger.info(
            f"OPENROUTER_API_KEY detected (length: {len(api_key)}). "
            "Neural Mesh initializing in full operational mode."
        )

    return NeuralRoutingMesh(api_key=api_key or "dummy_key")
