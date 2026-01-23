"""
شبكة التوجيه العصبي.

تم تبسيطها لتحسين الاعتمادية والأداء مع الحفاظ على التوافق الخلفي.
"""

import time
import hashlib
import json
import logging
from collections.abc import AsyncGenerator
from typing import Literal, Protocol, runtime_checkable

# Config imports
from app.core.ai_config import get_ai_config
from app.core.cognitive_cache import get_cognitive_engine
from app.core.gateway.connection import ConnectionManager

# Import new atomic modules
from app.core.gateway.exceptions import (
    AIAllModelsExhaustedError,
    AIRateLimitError,
    StreamInterruptedError,
)
from app.core.gateway.node import NeuralNode
from app.core.gateway.processor import StreamProcessor
from app.core.gateway.manager import DefaultRanker, NodeManager, NodeRanker
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
    موجّه "العقل الفائق" لإدارة توجيه الطلبات بشكل مبسط وموثوق.
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
        self.omni_router = get_omni_router(self.manager.nodes_map)
        self.manager.ranker = self.omni_router

    @property
    def nodes_map(self) -> dict[str, NeuralNode]:
        """يوفر خريطة العقد للتوافق الخلفي والاختبارات."""
        return self.manager.nodes_map

    @nodes_map.setter
    def nodes_map(self, value: dict[str, NeuralNode]) -> None:
        """يدعم ضبط الخريطة لأغراض الاختبارات الرجعية."""
        self.manager.nodes_map = value
        self.omni_router = get_omni_router(value)
        self.manager.ranker = self.omni_router

    async def __aiter__(self) -> "NeuralRoutingMesh":
        """يدعم التكرار غير المتزامن على كائن الشبكة نفسه."""
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
        priority_nodes = self._get_prioritized_nodes(prompt)
        if not priority_nodes:
            raise AIAllModelsExhaustedError("All circuits are open, no models available.")

        # 3. Execution Loop
        error_messages: list[str] = []
        for node in priority_nodes:
            # Redundant check? Manager filters, but breaker state might change.
            if not node.circuit_breaker.allow_request():
                continue

            try:
                # Attempt stream
                async for chunk in self._stream_from_node_with_retry(node, messages):
                    yield chunk
                return

            except StreamInterruptedError:
                # Critical failure during stream - abort immediately
                logger.critical(f"Stream interrupted for {node.model_id}. Aborting.")
                raise
            except Exception as e:
                error_messages.append(f"{node.model_id}: {e!s}")

        raise AIAllModelsExhaustedError(f"All models failed. Errors: {error_messages}")

    def _get_prioritized_nodes(self, prompt: str) -> list[NeuralNode]:
        """واجهة توافقية لاختيار العقد ذات الأولوية."""
        return self.manager.get_prioritized_nodes(prompt)

    async def _stream_from_node_with_retry(
        self,
        node: NeuralNode,
        messages: list[JSONDict],
    ) -> AsyncGenerator[JSONDict, None]:
        """غلاف متوافق للاختبارات يستدعي تنفيذ البث الداخلي."""
        prompt = str(messages[-1].get("content", ""))
        context_hash = self._get_context_hash(messages)
        client = ConnectionManager.get_client()
        async for chunk in self._attempt_node_stream(node, messages, prompt, context_hash, client):
            yield chunk

    async def _attempt_node_stream(
        self,
        node: NeuralNode,
        messages: list[JSONDict],
        prompt: str,
        context_hash: str,
        client: object,
    ) -> AsyncGenerator[JSONDict, None]:
        """
        يدير محاولة عقدة واحدة عبر التنفيذ والمراقبة وقياس الأداء.
        """
        start_time = time.time()
        full_response_chunks: list[JSONDict] = []
        chunks_yielded = 0

        try:
            async for chunk in self._stream_and_collect(node, messages, client, full_response_chunks):
                yield chunk
                chunks_yielded += 1

            self._record_outcome(node, start_time, outcome="success")
            self._memorize_response(node, prompt, context_hash, full_response_chunks)

        except AIRateLimitError as e:
            self._record_outcome(node, start_time, outcome="rate_limit")
            raise e

        except Exception as e:
            self._handle_stream_failure(node, start_time, chunks_yielded, e)

    async def _stream_and_collect(
        self,
        node: NeuralNode,
        messages: list[JSONDict],
        client: object,
        chunks: list[JSONDict],
    ) -> AsyncGenerator[JSONDict, None]:
        """يبث الردود ويجمعها في قائمة مشتركة لغايات التسجيل لاحقاً."""
        async for chunk in self.processor.stream(node, messages, client):  # type: ignore
            chunks.append(chunk)
            yield chunk

    def _record_outcome(
        self,
        node: NeuralNode,
        start_time: float,
        outcome: Literal["success", "rate_limit", "failure"],
    ) -> None:
        """يوحد تسجيل نتائج التنفيذ لنجاح العقدة أو حد السرعة أو الفشل."""
        duration_ms = self._elapsed_ms(start_time)
        if outcome == "success":
            node.circuit_breaker.record_success()
            self._record_metrics(node, duration_ms, True)
            return
        if outcome == "rate_limit":
            node.circuit_breaker.record_saturation()
            self._record_metrics(node, duration_ms, False)
            return
        node.circuit_breaker.record_failure()
        self._record_metrics(node, duration_ms, False)

    def _handle_stream_failure(
        self,
        node: NeuralNode,
        start_time: float,
        chunks_yielded: int,
        error: Exception,
    ) -> None:
        """يوحد معالجة فشل البث مع التفريق بين الفشل الجزئي والكامل."""
        self._record_outcome(node, start_time, outcome="failure")

        if chunks_yielded > 0:
            raise StreamInterruptedError(f"Stream severed from {node.model_id}") from error

        logger.warning(f"Node {node.model_id} failed: {error}")
        raise error

    def _memorize_response(
        self,
        node: NeuralNode,
        prompt: str,
        context_hash: str,
        chunks: list[JSONDict],
    ) -> None:
        """يحفظ الاستجابة في الذاكرة المعرفية عند توفر الشروط."""
        if node.model_id == SAFETY_NET_MODEL_ID:
            return
        get_cognitive_engine().memorize(prompt, context_hash, chunks)  # type: ignore

    def _elapsed_ms(self, start_time: float) -> float:
        """يحصل على الزمن المنقضي بالمللي ثانية."""
        return (time.time() - start_time) * 1000

    def _record_metrics(self, node: NeuralNode, duration_ms: float, success: bool) -> None:
        """يسجل مقاييس الأداء للعقدة مع احترام نموذج شبكة الأمان."""
        if node.model_id == SAFETY_NET_MODEL_ID:
            return
        log_method = logger.info if success else logger.warning
        log_method(f"AI Request: {node.model_id} | Success: {success} | Latency: {duration_ms:.2f}ms")

    def _get_context_hash(self, messages: list[JSONDict]) -> str:
        """ينشئ بصمة سياق مستقرة لمحتوى الرسائل السابقة."""
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


def get_omni_router(nodes_map: dict[str, NeuralNode] | None = None) -> NodeRanker:
    """يبني موجه ترتيب بسيط للحفاظ على التوافق الخلفي."""
    if nodes_map is None:
        return DefaultRanker({})
    return DefaultRanker(nodes_map)
