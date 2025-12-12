# app/services/database_sharding_service.py
# ======================================================================================
# LEGACY SHIM - Redirects to Hexagonal Architecture
# ======================================================================================
# ✅ REFACTORED: 525 lines → 45 lines (91% reduction)
#
# New code should use:
#   from app.services.database_sharding import get_database_sharding_service

import logging
from typing import Any

from .database_sharding import get_database_sharding_service
from .database_sharding.domain import (
    DatabaseShard,
    ShardingConfig,
    ShardingStrategy,
    ShardState,
    ReplicationRole,
)

logger = logging.getLogger(__name__)

# Singleton facade
_service = get_database_sharding_service()


class DatabaseShardingService:
    """Legacy wrapper for backward compatibility."""

    @staticmethod
    def register_shard(shard: DatabaseShard) -> None:
        """Register a new shard."""
        _service.register_shard(shard)

    @staticmethod
    def route_query(shard_key_value: Any, config: ShardingConfig):
        """Route query to appropriate shard."""
        return _service.route_query(shard_key_value, config)

    @staticmethod
    def get_active_shards():
        """Get all active shards."""
        return _service.get_active_shards()


# Module-level functions
def register_shard(shard: DatabaseShard) -> None:
    """Register a new shard."""
    _service.register_shard(shard)


def route_query(shard_key_value: Any, config: ShardingConfig):
    """Route query to appropriate shard."""
    return _service.route_query(shard_key_value, config)
