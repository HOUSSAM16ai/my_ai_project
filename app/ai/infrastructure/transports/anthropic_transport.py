# app/ai/infrastructure/transports/anthropic_transport.py
"""
Anthropic (Claude) Transport Implementation
============================================
Direct Anthropic API transport with native SDK integration.

Features:
- Native Anthropic SDK support
- Claude models support (Opus, Sonnet, Haiku)
- Streaming support
- Tool use support
- Error handling and normalization
"""

from __future__ import annotations

import logging
import os
from typing import Any, Generator

_LOG = logging.getLogger(__name__)


class AnthropicTransport:
    """
    Anthropic API transport implementation.
    
    Implements LLMClientPort for Anthropic Claude models.
    """
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize Anthropic transport.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            )
        
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError("Anthropic API key not provided")
        
        self._client = anthropic.Anthropic(api_key=self._api_key)
        _LOG.info("Anthropic transport initialized")
    
    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute chat completion via Anthropic.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier (e.g., claude-3-opus, claude-3-sonnet)
            **kwargs: Additional parameters
            
        Returns:
            Normalized response dictionary
        """
        try:
            converted_messages = self._convert_messages(messages)
            
            system_message = kwargs.pop("system", None)
            if not system_message and converted_messages:
                if converted_messages[0].get("role") == "system":
                    system_message = converted_messages[0]["content"]
                    converted_messages = converted_messages[1:]
            
            max_tokens = kwargs.pop("max_tokens", 4096)
            
            response = self._client.messages.create(
                model=model,
                messages=converted_messages,
                max_tokens=max_tokens,
                system=system_message,
                **kwargs,
            )
            
            return self._normalize_response(response)
            
        except Exception as e:
            _LOG.error(f"Anthropic transport error: {e}")
            raise
    
    def chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Execute streaming chat completion via Anthropic.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        try:
            converted_messages = self._convert_messages(messages)
            
            system_message = kwargs.pop("system", None)
            if not system_message and converted_messages:
                if converted_messages[0].get("role") == "system":
                    system_message = converted_messages[0]["content"]
                    converted_messages = converted_messages[1:]
            
            max_tokens = kwargs.pop("max_tokens", 4096)
            
            with self._client.messages.stream(
                model=model,
                messages=converted_messages,
                max_tokens=max_tokens,
                system=system_message,
                **kwargs,
            ) as stream:
                for text in stream.text_stream:
                    yield {
                        "content": text,
                        "delta": text,
                        "model": model,
                    }
                    
        except Exception as e:
            _LOG.error(f"Anthropic streaming error: {e}")
            raise
    
    def _convert_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Convert OpenAI-style messages to Anthropic format.
        
        Args:
            messages: OpenAI-style messages
            
        Returns:
            Anthropic-style messages
        """
        converted = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                converted.append({"role": "user", "content": f"[System: {content}]"})
            elif role == "assistant":
                converted.append({"role": "assistant", "content": content})
            else:
                converted.append({"role": "user", "content": content})
        
        return converted
    
    def _normalize_response(self, response: Any) -> dict[str, Any]:
        """
        Normalize Anthropic response to standard format.
        
        Args:
            response: Raw Anthropic response
            
        Returns:
            Normalized response dictionary
        """
        content = ""
        if hasattr(response, "content") and response.content:
            if isinstance(response.content, list):
                content = " ".join(
                    block.text for block in response.content
                    if hasattr(block, "text")
                )
            else:
                content = str(response.content)
        
        result = {
            "content": content,
            "model": response.model,
            "finish_reason": response.stop_reason if hasattr(response, "stop_reason") else None,
        }
        
        if hasattr(response, "usage") and response.usage:
            result["usage"] = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
        
        if hasattr(response, "content") and response.content:
            tool_uses = [
                block for block in response.content
                if hasattr(block, "type") and block.type == "tool_use"
            ]
            
            if tool_uses:
                result["tool_calls"] = [
                    {
                        "id": tool.id,
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "arguments": str(tool.input),
                        }
                    }
                    for tool in tool_uses
                ]
        
        return result
