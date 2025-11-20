# app/core/ai_gateway.py
"""
The ENERGY-ENGINE.

This engine enforces the Law of Energetic Continuity, unifying AI service
communication into a lossless, monotonic, and self-healing stream. This
gateway abstracts the complexities of communicating with external AI
services.
"""

import json
import os
from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

import httpx

# --- Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


# --- Protocols ---
@runtime_checkable
class AIClient(Protocol):
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]: ...

    # This is added to satisfy the type checker, but it's not used in the streaming implementation.
    # It seems to be a quirk of how @runtime_checkable works with async generators.
    async def __aiter__(self):
        return self


# --- Concrete Implementation ---
class OpenRouterAIClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={"model": self.model, "messages": messages, "stream": True},
                timeout=None,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]
                        if line.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(line)
                            yield chunk
                        except json.JSONDecodeError:
                            continue


# --- Dependency Injectable Gateway ---
def get_ai_client() -> AIClient:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set.")
    return OpenRouterAIClient(api_key=OPENROUTER_API_KEY)
