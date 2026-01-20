"""
Neural Routing Mesh Module.
Simplified for reliability and performance.
"""

import time
import hashlib
import json
import logging
from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

# Config imports
from app.core.ai_config import get_ai_config
from app.core.cognitive_cache import get_cognitive_engine
from app.core.gateway.connection import ConnectionManager

# Import new atomic modules
from app.core.gateway.exceptions import (
    AIAllModelsExhaustedError,
    AIConnectionError,
    AIRateLimitError,
    StreamInterruptedError,
)
from app.core.gateway.node import NeuralNode
from app.core.gateway.processor import StreamProcessor
from app.core.gateway.manager import NodeManager
from app.core.types import JSONDict

logger = logging.getLogger(__name__)

# Constants
_ai_config = get_ai_config()
PRIMARY_MODEL = _ai_config.gateway_primary
FALLBACK_MODELS = _ai_config.get_fallback_models()
SAFETY_NET_MODEL_ID = "system/safety-net"
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 30.0


@runtime_checkable
class AIClient(Protocol):
    def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]: ...
    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
    ) -> str: ...
    async def __aiter__(self): ...


class NeuralRoutingMesh:
    """
    The 'Overmind' Router.
    Refactored for Simplicity and Reliability (Phase 28 Cleanup).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Configuration
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cogniforge.local",
            "X-Title": "CogniForge Reality Kernel",
        }

        # Dependencies
        self.manager = NodeManager(
            primary_model=PRIMARY_MODEL,
            fallback_models=FALLBACK_MODELS,
            safety_net_model=SAFETY_NET_MODEL_ID,
            failure_threshold=CIRCUIT_FAILURE_THRESHOLD,
            recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT
        )
        self.processor = StreamProcessor(self.base_url, self.headers)

    @property
    def nodes_map(self) -> dict[str, NeuralNode]:
        """Expose nodes map for backward compatibility/testing."""
        return self.manager.nodes_map

    async def __aiter__(self):
        return self

    async def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]:
        if not messages:
            raise ValueError("Messages list cannot be empty")

        prompt = str(messages[-1].get("content", ""))
        context_hash = self._get_context_hash(messages)

        # 1. Check Cache
        if messages[-1].get("role") == "user":
            cached_memory = get_cognitive_engine().recall(prompt, context_hash)
            if cached_memory:
                async for chunk in self._yield_cached_response(cached_memory, prompt):
                    yield chunk  # type: ignore
                return

        # 2. Get Nodes
        priority_nodes = self.manager.get_prioritized_nodes(prompt)
        if not priority_nodes:
            raise AIAllModelsExhaustedError("All circuits are open, no models available.")

        # 3. Execution Loop
        errors = []
        client = ConnectionManager.get_client()

        for node in priority_nodes:
            # Redundant check? Manager filters, but breaker state might change.
            if not node.circuit_breaker.allow_request():
                continue

            try:
                # Attempt stream
                async for chunk in self._attempt_node_stream(node, messages, prompt, context_hash, client):
                    yield chunk
                return

            except StreamInterruptedError:
                # Critical failure during stream - abort immediately
                logger.critical(f"Stream interrupted for {node.model_id}. Aborting.")
                raise
            except (AIConnectionError, ValueError, AIRateLimitError, Exception) as e:
                errors.append(f"{node.model_id}: {e!s}")
                continue

        raise AIAllModelsExhaustedError(f"All models failed. Errors: {errors}")

    async def _attempt_node_stream(
        self,
        node: NeuralNode,
        messages: list[JSONDict],
        prompt: str,
        context_hash: str,
        client: object,
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Orchestrates a single node attempt: Execution + Monitoring + Metrics.
        """
        start_time = time.time() # This module still needs time for metrics
        full_response_chunks = []
        chunks_yielded = 0

        try:
            # Delegate raw streaming to Processor
            async for chunk in self.processor.stream(node, messages, client): # type: ignore
                yield chunk
                full_response_chunks.append(chunk)
                chunks_yielded += 1

            # Success Recording
            duration = (time.time() - start_time) * 1000
            node.circuit_breaker.record_success()
            self._record_metrics(node, duration, True)

            if node.model_id != SAFETY_NET_MODEL_ID:
                get_cognitive_engine().memorize(prompt, context_hash, full_response_chunks) # type: ignore

        except AIRateLimitError as e:
            duration = (time.time() - start_time) * 1000
            node.circuit_breaker.record_saturation()
            self._record_metrics(node, duration, False)
            raise e

        except Exception as e:
            duration = (time.time() - start_time) * 1000

            # Check for partial stream failure
            if chunks_yielded > 0:
                node.circuit_breaker.record_failure()
                self._record_metrics(node, duration, False)
                raise StreamInterruptedError(f"Stream severed from {node.model_id}") from e

            node.circuit_breaker.record_failure()
            self._record_metrics(node, duration, False)
            logger.warning(f"Node {node.model_id} failed: {e}")
            raise e

    def _record_metrics(self, node: NeuralNode, duration_ms: float, success: bool):
        if node.model_id == SAFETY_NET_MODEL_ID:
            return
        log_method = logger.info if success else logger.warning
        log_method(f"AI Request: {node.model_id} | Success: {success} | Latency: {duration_ms:.2f}ms")

    def _get_context_hash(self, messages: list[JSONDict]) -> str:
        context_str = json.dumps(list(messages[:-1]), sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()

    async def _yield_cached_response(
        self, cached_memory: list[JSONDict], prompt: str
    ) -> AsyncGenerator[JSONDict, None]:
        logger.info(f"⚡️ Cognitive Recall: Serving cached response for '{prompt[:20]}...'")
        for chunk in cached_memory:
            yield chunk

    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
    ) -> str:
        messages: list[JSONDict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        full_response = []
        async for chunk in self.stream_chat(messages):
            content = str(chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")) # type: ignore
            if content:
                full_response.append(content)
        return "".join(full_response)


def get_ai_client() -> AIClient:
    api_key = _ai_config.openrouter_api_key
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. Neural Mesh initializing in shadow mode.")
    return NeuralRoutingMesh(api_key=api_key or "dummy_key")
