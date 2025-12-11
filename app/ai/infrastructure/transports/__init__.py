# app/ai/infrastructure/transports/__init__.py
"""
Infrastructure Transports for LLM Client
========================================
Concrete implementations of domain ports.

These adapters connect the domain layer to external LLM services.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Generator

from app.ai.domain.ports import LLMClientPort

_LOG = logging.getLogger(__name__)


# ======================================================================================
# OPENROUTER TRANSPORT
# ======================================================================================


class OpenRouterTransport:
    """
    OpenRouter API transport implementation.
    
    Implements LLMClientPort for OpenRouter service.
    Uses centralized AI client factory for actual HTTP communication.
    """

    def __init__(self, client: Any):
        """
        Initialize OpenRouter transport.
        
        Args:
            client: OpenRouter client instance (from ai_client_factory)
        """
        self._client = client

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute chat completion via OpenRouter.
        
        Delegates to the underlying OpenRouter client.
        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            
            # Normalize response format
            return {
                "content": response.choices[0].message.content if response.choices else "",
                "usage": {
                    "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(response.usage, "completion_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason if response.choices else None,
            }
        except Exception as e:
            _LOG.error(f"OpenRouter transport error: {e}")
            raise

    def chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Execute streaming chat completion via OpenRouter.
        """
        try:
            stream = self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs,
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "delta": chunk.choices[0].delta.content,
                        "finish_reason": chunk.choices[0].finish_reason,
                    }
        except Exception as e:
            _LOG.error(f"OpenRouter streaming error: {e}")
            raise


# ======================================================================================
# MOCK TRANSPORT
# ======================================================================================


class MockLLMTransport:
    """
    Mock LLM transport for testing.
    
    Returns predefined responses without calling external APIs.
    Useful for testing and development.
    """

    def __init__(self, default_response: str = "Mock LLM response"):
        """
        Initialize mock transport.
        
        Args:
            default_response: Default text to return
        """
        self._default_response = default_response
        self._call_count = 0

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Return mock chat completion response.
        """
        self._call_count += 1
        
        return {
            "content": self._default_response,
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
            },
            "model": model,
            "finish_reason": "stop",
            "mock": True,
            "call_count": self._call_count,
        }

    def chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Return mock streaming response.
        """
        self._call_count += 1
        
        # Split response into chunks
        words = self._default_response.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield {
                "delta": chunk,
                "finish_reason": "stop" if i == len(words) - 1 else None,
                "mock": True,
            }

    def get_call_count(self) -> int:
        """Get number of times transport was called"""
        return self._call_count

    def reset_call_count(self) -> None:
        """Reset call counter"""
        self._call_count = 0


# ======================================================================================
# TRANSPORT FACTORY
# ======================================================================================


def create_llm_transport(
    client: Any | None = None,
    force_mock: bool = False,
) -> LLMClientPort:
    """
    Factory function to create appropriate LLM transport.
    
    Args:
        client: Optional client instance (if None, will be created)
        force_mock: Force mock transport regardless of environment
        
    Returns:
        Transport implementing LLMClientPort
    """
    # Check environment flags
    if force_mock or os.getenv("LLM_FORCE_MOCK", "0") == "1":
        return MockLLMTransport()
    
    # For now, default to OpenRouter
    # In the future, this could route to different transports based on model/config
    if client is None:
        from app.core.ai_client_factory import get_ai_client
        client = get_ai_client()
    
    # Check if it's a mock client
    if hasattr(client, "__class__") and "Mock" in client.__class__.__name__:
        return MockLLMTransport()
    
    return OpenRouterTransport(client)


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "OpenRouterTransport",
    "MockLLMTransport",
    "create_llm_transport",
]
