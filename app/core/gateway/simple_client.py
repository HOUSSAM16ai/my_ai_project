"""
Simple AI Client.
Replaces the complex NeuralRoutingMesh with a straightforward, robust implementation.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import httpx

from app.core.ai_config import get_ai_config
from app.core.cognitive_cache import get_cognitive_engine
from app.core.gateway.connection import BASE_TIMEOUT, ConnectionManager
from app.core.types import JSONDict

logger = logging.getLogger(__name__)


@dataclass
class SimpleResponse:
    content: str


class SimpleAIClient:
    """
    A robust, simplified AI client that handles:
    1. Authentication with OpenRouter.
    2. Model Fallback (Primary -> Fallbacks).
    3. Caching (Cognitive Engine).
    4. Safety Net (Offline Fallback).
    """

    def __init__(self, api_key: str | None = None):
        self.config = get_ai_config()
        # Prefer provided key, fallback to config, then dummy
        self.api_key = api_key or self.config.openrouter_api_key or "dummy_key"
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cogniforge.local",
            "X-Title": "CogniForge Simple Gateway",
        }
        self.cognitive_engine = get_cognitive_engine()

    async def __aiter__(self) -> "SimpleAIClient":
        """Support for 'async for' iteration on the client itself (legacy compatibility)."""
        return self

    def _get_context_hash(self, messages: list[JSONDict]) -> str:
        """Generates a stable hash for the conversation context (excluding the last user message)."""
        # If there's only one message, context is empty or just system
        if not messages:
            return "empty"

        # We hash everything *except* the last message (which is the new prompt)
        # unless it's a single message turn.
        context_msgs = messages[:-1] if len(messages) > 1 else []
        context_str = json.dumps(context_msgs, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()

    async def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]:
        """
        Streams a chat completion, trying models in priority order.
        """
        if not messages:
            yield self._create_error_chunk("No messages provided.")
            return

        last_message = messages[-1]
        prompt = str(last_message.get("content", ""))
        context_hash = self._get_context_hash(messages)

        # 1. Check Cognitive Cache (if user message)
        # DISABLED FOR AUTONOMY: The "Static Answer" bug was caused by aggressive fuzzy matching
        # returning cached hallucinations. We force the agent to "Sense" every time.
        # if last_message.get("role") == "user":
        #     cached = self.cognitive_engine.recall(prompt, context_hash)
        #     if cached:
        #         logger.info(f"⚡️ Cache Hit: Serving response for '{prompt[:20]}...'")
        #         for chunk in cached:
        #             yield chunk  # type: ignore
        #         return

        # 2. Prepare Model List (Primary + Fallbacks)
        models_to_try = [
            self.config.primary_model,
            *self.config.get_fallback_models(),
        ]

        # 3. Try each model
        client = ConnectionManager.get_client()
        full_response_chunks: list[JSONDict] = []

        for model_id in models_to_try:
            try:
                # Attempt to stream from this model
                logger.info(f"Attempting model: {model_id}")
                async for chunk in self._stream_model(client, model_id, messages):
                    full_response_chunks.append(chunk)
                    yield chunk

                # Success! Memorize and exit.
                if last_message.get("role") == "user":
                    self.cognitive_engine.memorize(prompt, context_hash, full_response_chunks)
                return

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError, ValueError) as e:
                logger.warning(f"Model {model_id} failed: {e}. Trying next...")
                # Continue to next model
            except Exception as e:
                logger.error(f"Unexpected error with {model_id}: {e}", exc_info=True)
                # Continue to next model

        # 4. Safety Net (All models failed)
        logger.critical("All models exhausted. Engaging Safety Net.")
        async for chunk in self._stream_safety_net():
            yield chunk

    async def _stream_model(
        self, client: httpx.AsyncClient, model_id: str, messages: list[JSONDict]
    ) -> AsyncGenerator[JSONDict, None]:
        """
        Internal generator to stream from a specific model.
        """
        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={"model": model_id, "messages": messages, "stream": True, "temperature": 0.7},
                timeout=httpx.Timeout(BASE_TIMEOUT, connect=10.0),
            ) as response:
                if response.status_code != 200:
                    # Consume body to avoid hanging connection
                    await response.aread()
                    raise httpx.HTTPStatusError(
                        f"Status {response.status_code}",
                        request=response.request,
                        response=response,
                    )

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

        except httpx.StreamError as e:
            raise httpx.ConnectError(f"Stream error: {e}") from e

    async def _stream_safety_net(self) -> AsyncGenerator[JSONDict, None]:
        """Generates the static safety net response."""
        safety_msg = "⚠️ System Alert: Unable to reach external intelligence providers. Please try again later."
        words = safety_msg.split(" ")
        for word in words:
            chunk = {
                "id": "safety-net",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "system/safety-net",
                "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}],
            }
            yield chunk  # type: ignore
            await asyncio.sleep(0.05)  # Simulate typing NON-BLOCKING

        # Final chunk
        yield {
            "id": "safety-net",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "system/safety-net",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }  # type: ignore

    def _create_error_chunk(self, message: str) -> JSONDict:
        return {"error": {"message": message}}  # type: ignore

    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
    ) -> str:
        """
        Simple non-streaming helper.
        """
        messages: list[JSONDict] = [
            {"role": "system", "content": system_prompt},  # type: ignore
            {"role": "user", "content": user_message},  # type: ignore
        ]

        full_content = []
        async for chunk in self.stream_chat(messages):
            choices = chunk.get("choices", [])  # type: ignore
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    full_content.append(content)

        return "".join(full_content)

    async def generate_text(
        self, prompt: str, model: str | None = None, system_prompt: str | None = None, **kwargs
    ) -> SimpleResponse:
        """
        Legacy compatibility method for tool calling.
        """
        sys_p = system_prompt or "You are a helpful assistant."
        content = await self.send_message(sys_p, prompt)
        return SimpleResponse(content=content)

    async def forge_new_code(self, **kwargs) -> SimpleResponse:
        """
        Legacy compatibility method.
        """
        prompt = kwargs.get("prompt", "")
        return await self.generate_text(prompt, **kwargs)
