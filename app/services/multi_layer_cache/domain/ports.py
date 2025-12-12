"""
Multi-Layer Cache Domain Ports
===============================

Interfaces (Protocols) defining contracts for cache operations.
No implementations - only abstract definitions.
"""
from __future__ import annotations

from typing import Any, Protocol

from .models import CacheLayer


class CachePort(Protocol):
    """Protocol for cache layer operations"""

    def get(self, key: str) -> Any | None:
        """Retrieve value from cache"""
        ...

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store value in cache"""
        ...

    def delete(self, key: str) -> bool:
        """Remove value from cache"""
        ...

    def clear(self) -> None:
        """Clear all cache entries"""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        ...


class EdgeCachePort(Protocol):
    """Protocol for CDN edge cache operations"""

    def get(self, key: str, location: str = "new-york") -> Any | None:
        """Get from nearest edge location"""
        ...

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Distribute to all edge locations"""
        ...

    def invalidate(self, key: str) -> None:
        """Invalidate across all edge locations"""
        ...

    def get_edge_stats(self) -> dict[str, Any]:
        """Get edge cache statistics"""
        ...


class ClusterCachePort(Protocol):
    """Protocol for distributed cluster cache operations"""

    def get(self, key: str) -> Any | None:
        """Get from appropriate cluster node"""
        ...

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store in appropriate cluster node"""
        ...

    def add_node(self, node_id: str, host: str, port: int) -> Any:
        """Add new node to cluster"""
        ...

    def get_cluster_stats(self) -> dict[str, Any]:
        """Get cluster-wide statistics"""
        ...


__all__ = [
    "CachePort",
    "EdgeCachePort",
    "ClusterCachePort",
]
