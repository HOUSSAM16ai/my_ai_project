# app/core/http_client_factory.py
"""
HTTP CLIENT FACTORY — CENTRALIZED HTTP CLIENT MANAGEMENT
=========================================================

Single source of truth for HTTP client creation and management.
Eliminates the 8 duplicate HTTP client implementations found in:
- app/core/ai_gateway.py
- app/core/rate_limiter.py
- app/core/superhuman_performance_optimizer.py
- app/services/ai_model_metrics_service.py
- app/services/api_config_secrets_service.py
- app/services/api_developer_portal_service.py
- app/services/distributed_resilience_service.py
- app/services/llm_client_service.py

RESPONSIBILITIES:
✅ HTTP client creation and pooling
✅ Connection management and reuse
✅ Timeout configuration
✅ Header management

DOES NOT:
❌ Implement retry logic (see resilience module)
❌ Implement circuit breakers (see resilience module)
❌ Implement telemetry (see observability)
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

# Thread-safe singleton management
_CLIENT_LOCK = threading.Lock()
_HTTP_CLIENTS: dict[str, Any] = {}


class HTTPClientFactory:
    """
    Factory for creating and managing HTTP clients.
    
    Provides connection pooling and reuse for better performance.
    """
    
    @staticmethod
    def create_client(
        name: str = "default",
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 30.0,
        use_cache: bool = True,
    ) -> Any:
        """
        Create or retrieve an HTTP client.
        
        Args:
            name: Unique name for the client (for caching)
            timeout: Request timeout in seconds
            max_connections: Maximum number of connections
            max_keepalive_connections: Maximum keepalive connections
            keepalive_expiry: Keepalive expiry time in seconds
            use_cache: Whether to use cached client
            
        Returns:
            HTTP client instance (httpx.AsyncClient)
        """
        cache_key = f"{name}:{timeout}:{max_connections}"
        
        # Check cache
        if use_cache and cache_key in _HTTP_CLIENTS:
            logger.debug(f"Returning cached HTTP client '{name}'")
            return _HTTP_CLIENTS[cache_key]
        
        # Thread-safe client creation
        with _CLIENT_LOCK:
            # Double-check after acquiring lock
            if use_cache and cache_key in _HTTP_CLIENTS:
                return _HTTP_CLIENTS[cache_key]
            
            # Create new client
            try:
                import httpx
                
                limits = httpx.Limits(
                    max_connections=max_connections,
                    max_keepalive_connections=max_keepalive_connections,
                    keepalive_expiry=keepalive_expiry,
                )
                
                client = httpx.AsyncClient(
                    timeout=httpx.Timeout(timeout),
                    limits=limits,
                    follow_redirects=True,
                )
                
                # Cache the client
                if use_cache:
                    _HTTP_CLIENTS[cache_key] = client
                
                logger.info(
                    f"Created HTTP client '{name}' with timeout={timeout}s, "
                    f"max_connections={max_connections}"
                )
                return client
                
            except ImportError:
                logger.error("httpx not available, cannot create HTTP client")
                # Return a mock client for development/testing
                return HTTPClientFactory._create_mock_http_client(name)
    
    @staticmethod
    async def close_client(name: str = "default"):
        """Close a specific HTTP client"""
        # More efficient: find keys directly without creating list
        with _CLIENT_LOCK:
            keys_to_remove = [k for k in _HTTP_CLIENTS if k.startswith(f"{name}:")]
            
            for key in keys_to_remove:
                client = _HTTP_CLIENTS.pop(key, None)
                if client:
                    try:
                        await client.aclose()
                        logger.info(f"Closed HTTP client '{key}'")
                    except Exception as e:
                        logger.error(f"Error closing HTTP client '{key}': {e}")
    
    @staticmethod
    async def close_all():
        """Close all HTTP clients"""
        with _CLIENT_LOCK:
            for key, client in list(_HTTP_CLIENTS.items()):
                try:
                    await client.aclose()
                    logger.debug(f"Closed HTTP client '{key}'")
                except Exception as e:
                    logger.error(f"Error closing HTTP client '{key}': {e}")
            
            _HTTP_CLIENTS.clear()
            logger.info("All HTTP clients closed")
    
    @staticmethod
    def get_cached_clients() -> dict[str, Any]:
        """Get information about cached clients"""
        return {
            key: {"created": True}
            for key in _HTTP_CLIENTS.keys()
        }
    
    @staticmethod
    def _create_mock_http_client(name: str) -> Any:
        """Create a mock HTTP client for testing/development when httpx unavailable"""
        
        class MockHTTPClient:
            """Mock HTTP client for development"""
            
            def __init__(self, name: str):
                self.name = name
                self._closed = False
                self._is_mock_client = True  # Protocol marker for detection
            
            async def get(self, url: str, **kwargs):
                """Mock GET request"""
                raise RuntimeError("httpx not available - mock client only")
            
            async def post(self, url: str, **kwargs):
                """Mock POST request"""
                raise RuntimeError("httpx not available - mock client only")
            
            async def aclose(self):
                """Mock close"""
                self._closed = True
            
            def __repr__(self):
                return f"MockHTTPClient(name={self.name})"
        
        return MockHTTPClient(name)


# =============================================================================
# PUBLIC API
# =============================================================================

def get_http_client(
    name: str = "default",
    timeout: float = 30.0,
    max_connections: int = 100,
    max_keepalive_connections: int = 20,
    keepalive_expiry: float = 30.0,
    use_cache: bool = True,
) -> Any:
    """
    Get an HTTP client instance.
    
    This is the primary function to use for obtaining HTTP clients
    throughout the application.
    
    Args:
        name: Unique name for the client
        timeout: Request timeout in seconds
        max_connections: Maximum number of connections
        max_keepalive_connections: Maximum keepalive connections
        keepalive_expiry: Keepalive expiry time in seconds
        use_cache: Whether to use cached client
        
    Returns:
        HTTP client instance
    """
    return HTTPClientFactory.create_client(
        name=name,
        timeout=timeout,
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
        keepalive_expiry=keepalive_expiry,
        use_cache=use_cache,
    )


async def close_http_client(name: str = "default"):
    """Close a specific HTTP client"""
    await HTTPClientFactory.close_client(name)


async def close_all_http_clients():
    """Close all HTTP clients"""
    await HTTPClientFactory.close_all()


def get_http_client_stats() -> dict[str, Any]:
    """Get statistics about cached HTTP clients"""
    return HTTPClientFactory.get_cached_clients()


__all__ = [
    "HTTPClientFactory",
    "get_http_client",
    "close_http_client",
    "close_all_http_clients",
    "get_http_client_stats",
]
