# app/core/ai_client_factory.py
"""
UNIFIED AI CLIENT FACTORY — SINGLE RESPONSIBILITY EDITION
==========================================================

This module provides a single, unified way to create and manage AI clients
across the entire application. It eliminates duplication and centralizes
AI client configuration and lifecycle management.

RESPONSIBILITIES:
✅ Single point of AI client creation
✅ Configuration management
✅ Client lifecycle (singleton pattern)
✅ Provider abstraction

DOES NOT:
❌ Implement routing logic (see ai_gateway.py)
❌ Implement streaming (see services)
❌ Implement circuit breakers (see resilience module)
❌ Implement telemetry (see observability)

ARCHITECTURE:
- Factory Pattern: Creates clients based on configuration
- Singleton Pattern: One client instance per configuration
- Strategy Pattern: Different providers (OpenRouter, OpenAI, etc.)
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Protocol, runtime_checkable

from app.config.ai_models import get_ai_config

logger = logging.getLogger(__name__)

# Thread-safe singleton management
_CLIENT_LOCK = threading.Lock()
_CLIENT_CACHE: dict[str, Any] = {}
_CLIENT_META: dict[str, Any] = {}


@runtime_checkable
class AIClientProtocol(Protocol):
    """Protocol defining the interface for AI clients"""
    
    def chat(self) -> Any:
        """Returns chat interface"""
        ...
    
    def meta(self) -> dict[str, Any]:
        """Returns client metadata"""
        ...


class AIClientFactory:
    """
    Unified factory for creating AI clients.
    Handles all provider-specific logic in one place.
    """
    
    @staticmethod
    def create_client(
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 180.0,
        use_cache: bool = True,
    ) -> Any:
        """
        Create or retrieve an AI client.
        
        Args:
            provider: Provider name ('openrouter', 'openai', etc.)
            api_key: API key for the provider
            base_url: Base URL for API calls
            timeout: Request timeout in seconds
            use_cache: Whether to use cached client
            
        Returns:
            AI client instance
        """
        # Get configuration if not provided
        if not provider or not api_key:
            config = get_ai_config()
            provider = provider or "openrouter"
            api_key = api_key or config.openrouter_api_key
            base_url = base_url or "https://openrouter.ai/api/v1"
        
        # Create cache key (use hash of API key for security)
        import hashlib
        api_key_hash = hashlib.sha256(api_key.encode() if api_key else b'none').hexdigest()[:16]
        cache_key = f"{provider}:{api_key_hash}:{base_url}"
        
        # Check cache
        if use_cache and cache_key in _CLIENT_CACHE:
            logger.debug(f"Returning cached client for {provider}")
            return _CLIENT_CACHE[cache_key]
        
        # Thread-safe client creation
        with _CLIENT_LOCK:
            # Double-check after acquiring lock
            if use_cache and cache_key in _CLIENT_CACHE:
                return _CLIENT_CACHE[cache_key]
            
            # Create new client
            client = AIClientFactory._create_new_client(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )
            
            # Cache the client
            if use_cache:
                _CLIENT_CACHE[cache_key] = client
            
            # Store metadata
            _CLIENT_META[cache_key] = {
                "provider": provider,
                "created_at": time.time(),
                "client_id": str(uuid.uuid4()),
            }
            
            logger.info(f"Created new AI client for provider: {provider}")
            return client
    
    @staticmethod
    def _create_new_client(
        provider: str,
        api_key: str,
        base_url: str,
        timeout: float,
    ) -> Any:
        """Create a new client instance based on provider"""
        
        try:
            # Try to use OpenAI SDK
            import openai
            
            client_kwargs = {
                "api_key": api_key,
                "base_url": base_url,
                "timeout": timeout,
            }
            
            client = openai.OpenAI(**client_kwargs)
            logger.info(f"Created OpenAI SDK client for {provider}")
            return client
            
        except ImportError:
            logger.warning("OpenAI SDK not available, using fallback")
            return AIClientFactory._create_fallback_client(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )
        except Exception as e:
            logger.error(f"Failed to create client: {e}")
            return AIClientFactory._create_fallback_client(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )
    
    @staticmethod
    def _create_fallback_client(
        api_key: str,
        base_url: str,
        timeout: float,
    ) -> Any:
        """Create a simple HTTP-based fallback client"""
        
        try:
            import requests
            
            class SimpleFallbackClient:
                """Minimal HTTP client for AI API calls"""
                
                def __init__(self, api_key: str, base_url: str, timeout: float):
                    self.api_key = api_key
                    self.base_url = base_url
                    self.timeout = timeout
                    self._id = str(uuid.uuid4())
                    self._created_at = time.time()
                
                class _ChatWrapper:
                    def __init__(self, parent):
                        self._parent = parent
                    
                    class _CompletionsWrapper:
                        def __init__(self, parent):
                            self._parent = parent
                        
                        def create(self, model: str, messages: list, **kwargs):
                            """Make API call using requests"""
                            headers = {
                                "Authorization": f"Bearer {self._parent._parent.api_key[:10]}...",  # Masked for logging
                                "Content-Type": "application/json",
                            }
                            
                            payload = {
                                "model": model,
                                "messages": messages,
                                **kwargs,
                            }
                            
                            try:
                                response = requests.post(
                                    f"{self._parent._parent.base_url}/chat/completions",
                                    json=payload,
                                    headers=headers,
                                    timeout=self._parent._parent.timeout,
                                )
                                response.raise_for_status()
                                return response.json()
                            except Exception as e:
                                logger.error(f"API call failed: {e}")
                                raise
                    
                    def completions(self):
                        return self._CompletionsWrapper(self)
                
                def chat(self):
                    return self._ChatWrapper(self)
                
                def meta(self) -> dict[str, Any]:
                    return {
                        "client_id": self._id,
                        "created_at": self._created_at,
                        "type": "fallback",
                    }
            
            return SimpleFallbackClient(api_key, base_url, timeout)
            
        except ImportError:
            logger.error("Neither OpenAI SDK nor requests available")
            return AIClientFactory._create_mock_client("no-dependencies")
    
    @staticmethod
    def _create_mock_client(reason: str) -> Any:
        """Create a mock client for testing/development"""
        
        class MockClient:
            """Mock client that returns synthetic responses"""
            
            def __init__(self, reason: str):
                self.reason = reason
                self._id = str(uuid.uuid4())
                self._created_at = time.time()
                self._is_mock_client = True  # Protocol marker for detection
            
            class _ChatWrapper:
                def __init__(self, parent):
                    self._parent = parent
                
                class _CompletionsWrapper:
                    def __init__(self, parent):
                        self._parent = parent
                    
                    def create(self, model: str, messages: list, **kwargs):
                        """Return mock response"""
                        
                        class _Message:
                            def __init__(self, content: str):
                                self.content = content
                                self.tool_calls = None
                        
                        class _Choice:
                            def __init__(self, message):
                                self.message = message
                                self.finish_reason = "stop"
                        
                        class _Response:
                            def __init__(self, choices):
                                self.choices = choices
                                self.id = str(uuid.uuid4())
                                self.model = model
                                self.usage = {"total_tokens": 100}
                        
                        mock_content = f"[MOCK:{self._parent._parent.reason}] Response for model {model}"
                        message = _Message(mock_content)
                        choice = _Choice(message)
                        return _Response([choice])
                
                def completions(self):
                    return self._CompletionsWrapper(self)
            
            def chat(self):
                return self._ChatWrapper(self)
            
            def meta(self) -> dict[str, Any]:
                return {
                    "client_id": self._id,
                    "created_at": self._created_at,
                    "type": "mock",
                    "reason": self.reason,
                }
        
        return MockClient(reason)
    
    @staticmethod
    def clear_cache():
        """Clear the client cache"""
        with _CLIENT_LOCK:
            _CLIENT_CACHE.clear()
            _CLIENT_META.clear()
            logger.info("Client cache cleared")
    
    @staticmethod
    def get_cached_clients() -> dict[str, Any]:
        """Get information about cached clients"""
        return dict(_CLIENT_META)


# =============================================================================
# PUBLIC API
# =============================================================================

def get_ai_client(
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 180.0,
    use_cache: bool = True,
) -> Any:
    """
    Get an AI client instance.
    
    This is the primary function to use for obtaining AI clients
    throughout the application.
    
    Args:
        provider: Provider name ('openrouter', 'openai', etc.)
        api_key: API key for the provider
        base_url: Base URL for API calls
        timeout: Request timeout in seconds
        use_cache: Whether to use cached client
        
    Returns:
        AI client instance
    """
    return AIClientFactory.create_client(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        use_cache=use_cache,
    )


def clear_ai_client_cache():
    """Clear the AI client cache"""
    AIClientFactory.clear_cache()


def get_client_metadata() -> dict[str, Any]:
    """Get metadata about cached clients"""
    return AIClientFactory.get_cached_clients()


__all__ = [
    "AIClientFactory",
    "AIClientProtocol",
    "get_ai_client",
    "clear_ai_client_cache",
    "get_client_metadata",
]
