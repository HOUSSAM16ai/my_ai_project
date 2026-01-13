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
from app.core.ai_config import get_ai_config
from app.caching.semantic import get_semantic_cache
from app.core.gateway.circuit_breaker import CircuitBreaker
from app.core.gateway.connection import BASE_TIMEOUT, ConnectionManager

# Import new atomic modules
from app.core.gateway.exceptions import (
    AIAllModelsExhaustedError,
    AIConnectionError,
    AIRateLimitError,
    StreamInterruptedError,
)
from app.core.gateway.node import NeuralNode
from app.core.types import JSONDict

logger = logging.getLogger(__name__)

# Constants
_ai_config = get_ai_config()
PRIMARY_MODEL = _ai_config.gateway_primary
FALLBACK_MODELS = _ai_config.get_fallback_models()
SAFETY_NET_MODEL_ID = "system/safety-net"
MAX_RETRIES = 3
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 30.0


class OmniRouter:
    """موجّه ذكي يعيد ترتيب العقد وفق أولوية ديناميكية."""

    def __init__(self, nodes_map: dict[str, "NeuralNode"] | None = None) -> None:
        self._nodes_map = nodes_map or {}

    def get_ranked_nodes(self, prompt: str | None = None) -> list[str]:
        """
        إرجاع قائمة معرفات العقد بترتيب افتراضي قابل للتخصيص.

        يتم الحفاظ على تسلسل منطقي (الأساسي، ثم الاحتياطي، ثم شبكة الأمان)
        مع السماح للطبقات العليا بحقن ترتيب خاص عبر الاختبارات أو التهيئة.
        """

        del prompt  # يُترك للسيناريوهات المستقبلية الخاصة بتحليل التعقيد.
        return list(self._nodes_map.keys())


def get_omni_router(nodes_map: dict[str, "NeuralNode"] | None = None) -> OmniRouter:
    """مصنع موجّه يحافظ على كائن واحد قابل للاختبار بسهولة."""

    return OmniRouter(nodes_map)


@runtime_checkable
class AIClient(Protocol):
    def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]: ...

    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
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
        self.omni_router = get_omni_router(self.nodes_map)

    async def __aiter__(self):
        """Allow the client to be used as an async iterator context if needed."""
        return self

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
            circuit_breaker=CircuitBreaker("Safety-Net", 999999, 1.0),  # Virtually unbreakable
        )
        return nodes

    def _get_prioritized_nodes(self, prompt: str) -> list[NeuralNode]:
        """
        Returns a list of nodes sorted by priority (Primary -> Fallback -> Safety Net).
        """
        final_nodes = []
        now = time.time()

        ranked_models: list[str] | None = None
        try:
            ranked_models = self.omni_router.get_ranked_nodes(prompt)
        except Exception as exc:  # pragma: no cover - protective fallback
            logger.warning("OmniRouter ranking failed; falling back to static order", exc_info=exc)

        if ranked_models:
            candidates = [model_id for model_id in ranked_models if model_id in self.nodes_map]
        else:
            candidates = [PRIMARY_MODEL, *FALLBACK_MODELS, SAFETY_NET_MODEL_ID]

        for model_id in candidates:
            node = self.nodes_map.get(model_id)
            if node is None:
                continue

            if model_id == SAFETY_NET_MODEL_ID:
                final_nodes.append(node)
                continue

            if node.circuit_breaker.allow_request() and node.rate_limit_cooldown_until <= now:
                final_nodes.append(node)

        if (
            SAFETY_NET_MODEL_ID in self.nodes_map
            and self.nodes_map[SAFETY_NET_MODEL_ID] not in final_nodes
        ):
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

    async def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]:
        if not messages:
            raise ValueError("Messages list cannot be empty")

        prompt = str(messages[-1].get("content", ""))
        context_hash = self._get_context_hash(messages)

        # 1. Check Cache
        if messages[-1].get("role") == "user":
            cached_memory = await get_semantic_cache().recall(prompt, context_hash)
            if cached_memory:
                async for chunk in self._yield_cached_response(cached_memory, prompt):
                    yield chunk  # type: ignore
                return

        # 2. Get Prioritized Nodes
        priority_nodes = self._get_prioritized_nodes(prompt)
        if not priority_nodes:
            raise AIAllModelsExhaustedError("All circuits are open, no models available.")

        # 3. Attempt Nodes
        errors = []
        for node in priority_nodes:
            if not node.circuit_breaker.allow_request():
                continue

            try:
                # We need to yield from the generator, so we can't easily put this in a separate function
                # that yields, unless we iterate over it.
                async for chunk in self._attempt_node_stream(node, messages, prompt, context_hash):
                    yield chunk
                return
            except StreamInterruptedError:
                # CRITICAL: Stream failed mid-transmission.
                # Do NOT failover to another node, as this would result in duplicate/corrupted output.
                # Re-raise immediately.
                logger.critical(
                    f"Stream interrupted for {node.model_id}. Aborting without failover."
                )
                raise
            except (AIConnectionError, ValueError, AIRateLimitError, Exception) as e:
                # Error handling is now inside _attempt_node_stream mostly, but it re-raises
                # for the loop to continue or stop.
                errors.append(f"{node.model_id}: {e!s}")
                # Rate limits are handled inside _attempt_node_stream logging
                # Connection errors are handled inside _attempt_node_stream logging
                # Critical failures (partial stream) raise through and stop everything
                continue

        raise AIAllModelsExhaustedError(f"All models failed. Errors: {errors}")

    def _get_context_hash(self, messages: list[JSONDict]) -> str:
        """Calculate hash of the conversation context"""
        context_str = json.dumps(list(messages[:-1]), sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()

    async def _yield_cached_response(
        self, cached_memory: list[JSONDict], prompt: str
    ) -> AsyncGenerator[JSONDict, None]:
        """Yield cached response chunks"""
        logger.info(f"⚡️ Cognitive Recall: Serving cached response for '{prompt[:20]}...'")
        for chunk in cached_memory:
            yield chunk

    async def _attempt_node_stream(
        self, node: NeuralNode, messages: list[JSONDict], prompt: str, context_hash: str
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Attempt to stream from a specific node.
        Handles success recording and error recording/raising.
        """
        start_time = time.time()
        full_response_chunks = []
        chunks_yielded = 0

        try:
            async for chunk in self._stream_from_node_with_retry(node, messages):
                yield chunk
                full_response_chunks.append(chunk)
                chunks_yielded += 1

            duration = (time.time() - start_time) * 1000
            node.circuit_breaker.record_success()
            self._record_metrics(node, prompt, duration, True)

            if node.model_id != SAFETY_NET_MODEL_ID:
                await get_semantic_cache().memorize(prompt, context_hash, full_response_chunks)  # type: ignore

        except AIRateLimitError as e:
            duration = (time.time() - start_time) * 1000
            node.circuit_breaker.record_saturation()
            self._record_metrics(node, prompt, duration, False)
            raise e

        except (AIConnectionError, ValueError, Exception) as e:
            duration = (time.time() - start_time) * 1000

            # CRITICAL: Check if we have already yielded data
            if chunks_yielded > 0:
                logger.critical(
                    f"Stream severed mid-transmission from {node.model_id}. Cannot failover safely."
                )
                node.circuit_breaker.record_failure()
                self._record_metrics(node, prompt, duration, False)
                # Raise specific error to stop the mesh from retrying
                raise StreamInterruptedError(f"Stream severed from {node.model_id}") from e

            node.circuit_breaker.record_failure()
            self._record_metrics(node, prompt, duration, False)
            logger.warning(f"Node {node.model_id} failed: {e}")
            raise e

    async def _stream_from_node_with_retry(
        self, node: NeuralNode, messages: list[JSONDict]
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Streams from a node with retry logic.
        """
        if node.model_id == SAFETY_NET_MODEL_ID:
            async for chunk in self._stream_safety_net():
                yield chunk
            return

        client = ConnectionManager.get_client()
        attempt = 0

        while attempt <= MAX_RETRIES:
            attempt += 1
            try:
                async for chunk in self._execute_stream_request(client, node, messages):
                    yield chunk
                return

            except AIRateLimitError:
                raise  # Propagate rate limit immediately (handled in outer loop)

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError, ValueError) as e:
                # _execute_stream_request raises AIConnectionError if stream started then failed
                # Here we catch initial connection errors
                if attempt > MAX_RETRIES:
                    raise AIConnectionError("Max retries exceeded") from e

                await asyncio.sleep(0.5 * attempt)

    async def _stream_safety_net(self) -> AsyncGenerator[JSONDict, None]:
        """Stream safety net response"""
        logger.warning("⚠️ Engaging Safety Net Protocol.")
        safety_msg = "⚠️ System Alert: Unable to reach external intelligence providers."
        for word in safety_msg.split(" "):
            yield {"choices": [{"delta": {"content": word + " "}}]}  # type: ignore
            await asyncio.sleep(0.05)

    async def _execute_stream_request(
        self, client: httpx.AsyncClient, node: NeuralNode, messages: list[JSONDict]
    ) -> AsyncGenerator[JSONDict, None]:
        """Execute the HTTP request and yield chunks"""
        stream_started = False
        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={"model": node.model_id, "messages": messages, "stream": True},
                timeout=httpx.Timeout(BASE_TIMEOUT, connect=10.0),
            ) as response:
                if response.status_code == 429:
                    self._handle_rate_limit(node)
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

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError, ValueError) as e:
            if stream_started:
                raise AIConnectionError("Stream severed") from e
            raise e

    def _handle_rate_limit(self, node: NeuralNode):
        """Handle rate limit backoff calculation"""
        node.consecutive_rate_limits += 1
        backoff = min(6, node.consecutive_rate_limits)
        cooldown = 60.0 * (2 ** (backoff - 1))
        node.rate_limit_cooldown_until = time.time() + cooldown

    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
    ) -> str:
        """
        دالة مساعدة لإرسال رسالة وتلقي رد كامل (غير متدفق).
        """
        messages: list[JSONDict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        full_response = []
        try:
            async for chunk in self.stream_chat(messages):
                content = str(
                    chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")  # type: ignore
                )
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
