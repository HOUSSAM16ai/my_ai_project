"""
Mesh Processor Module.
Handles the execution of streaming requests and retry logic.
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

import httpx

from app.core.gateway.circuit_breaker import CircuitBreaker
from app.core.gateway.connection import BASE_TIMEOUT
from app.core.gateway.exceptions import (
    AIConnectionError,
    AIRateLimitError,
    StreamInterruptedError,
)
from app.core.gateway.node import NeuralNode
from app.core.types import JSONDict

logger = logging.getLogger(__name__)


class StreamProcessor:
    """
    Handles the imperative shell of streaming data from Neural Nodes.
    Isolates side-effects (IO) and error handling mechanics.
    """

    def __init__(self, base_url: str, headers: dict[str, str], max_retries: int = 3):
        self.base_url = base_url
        self.headers = headers
        self.max_retries = max_retries
        self.safety_net_model_id = "system/safety-net"

    async def stream(
        self,
        node: NeuralNode,
        messages: list[JSONDict],
        client: httpx.AsyncClient,
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Public facade to stream from a node.
        Delegates to specific implementations (Safety Net vs Standard).
        """
        if node.model_id == self.safety_net_model_id:
            async for chunk in self._stream_safety_net():
                yield chunk
            return

        async for chunk in self._stream_with_retry(node, messages, client):
            yield chunk

    async def _stream_with_retry(
        self,
        node: NeuralNode,
        messages: list[JSONDict],
        client: httpx.AsyncClient,
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Streams with retry logic (Exponential Backoff).
        """
        attempt = 0
        while attempt <= self.max_retries:
            attempt += 1
            try:
                async for chunk in self._execute_request(client, node, messages):
                    yield chunk
                return

            except AIRateLimitError:
                raise  # Propagate immediately (handled by caller's circuit breaker logic usually)

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError, ValueError) as e:
                if attempt > self.max_retries:
                    raise AIConnectionError(f"Max retries ({self.max_retries}) exceeded") from e

                backoff = 0.5 * attempt
                logger.warning(f"Retry {attempt}/{self.max_retries} for {node.model_id} in {backoff}s. Error: {e}")
                await asyncio.sleep(backoff)

    async def _execute_request(
        self,
        client: httpx.AsyncClient,
        node: NeuralNode,
        messages: list[JSONDict],
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Executes the raw HTTP request and yields chunks.
        Raises specific domain exceptions.
        """
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
                # If stream started, we cannot retry safely without potentially duplicating content
                raise AIConnectionError("Stream severed mid-transmission") from e
            raise e

    def _handle_rate_limit(self, node: NeuralNode) -> None:
        """Updates node state for rate limiting."""
        node.consecutive_rate_limits += 1
        backoff = min(6, node.consecutive_rate_limits)
        cooldown = 60.0 * (2 ** (backoff - 1))
        node.rate_limit_cooldown_until = time.time() + cooldown

    async def _stream_safety_net(self) -> AsyncGenerator[JSONDict, None]:
        """Generates the static safety net response."""
        logger.warning("⚠️ Engaging Safety Net Protocol.")
        safety_msg = "⚠️ System Alert: Unable to reach external intelligence providers."
        for word in safety_msg.split(" "):
            yield {"choices": [{"delta": {"content": word + " "}}]}  # type: ignore
            await asyncio.sleep(0.05)
