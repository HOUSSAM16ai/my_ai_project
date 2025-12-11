# app/ai/infrastructure/transports/openai_transport.py
"""
OpenAI Transport Implementation
================================
Direct OpenAI API transport with native SDK integration.

Features:
- Native OpenAI SDK support
- Function calling support
- Streaming support
- Error handling and normalization
"""

from __future__ import annotations

import logging
import os
from typing import Any, Generator

_LOG = logging.getLogger(__name__)


class OpenAITransport:
    """
    OpenAI API transport implementation.
    
    Implements LLMClientPort for OpenAI service using official SDK.
    """
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize OpenAI transport.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install openai"
            )
        
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OpenAI API key not provided")
        
        self._client = openai.OpenAI(api_key=self._api_key)
        _LOG.info("OpenAI transport initialized")
    
    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute chat completion via OpenAI.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier (e.g., gpt-4, gpt-3.5-turbo)
            **kwargs: Additional parameters
            
        Returns:
            Normalized response dictionary
        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            
            return self._normalize_response(response)
            
        except Exception as e:
            _LOG.error(f"OpenAI transport error: {e}")
            raise
    
    def chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Execute streaming chat completion via OpenAI.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
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
                        "content": chunk.choices[0].delta.content,
                        "delta": chunk.choices[0].delta.content,
                        "finish_reason": chunk.choices[0].finish_reason,
                        "model": chunk.model,
                    }
                    
        except Exception as e:
            _LOG.error(f"OpenAI streaming error: {e}")
            raise
    
    def _normalize_response(self, response: Any) -> dict[str, Any]:
        """
        Normalize OpenAI response to standard format.
        
        Args:
            response: Raw OpenAI response
            
        Returns:
            Normalized response dictionary
        """
        choice = response.choices[0] if response.choices else None
        
        result = {
            "content": choice.message.content if choice else "",
            "model": response.model,
            "finish_reason": choice.finish_reason if choice else None,
        }
        
        if hasattr(response, "usage") and response.usage:
            result["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        if choice and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in choice.message.tool_calls
            ]
        
        return result
