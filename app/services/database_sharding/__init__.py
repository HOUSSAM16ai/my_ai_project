"""Database Sharding Service - Hexagonal Architecture.

Provides database sharding with:
- Hash-based and range-based sharding
- Multi-master replication
- Automatic load balancing
- Cross-shard query routing
"""

from .facade import DatabaseShardingServiceFacade, get_database_sharding_service

__all__ = ["DatabaseShardingServiceFacade", "get_database_sharding_service"]
