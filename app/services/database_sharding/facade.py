"""Facade for Database Sharding service."""

import logging
from typing import Any

from .application.query_router import QueryRoutingService
from .application.shard_manager import ShardManager
from .domain.models import DatabaseShard, QueryRoute, ShardingConfig
from .infrastructure.hash_router import HashBasedRouter
from .infrastructure.in_memory_repository import InMemoryShardRepository
from .infrastructure.load_balancer import WeightedLoadBalancer

logger = logging.getLogger(__name__)


class DatabaseShardingServiceFacade:
    """Unified facade for Database Sharding service."""

    def __init__(self):
        # Infrastructure
        self._repository = InMemoryShardRepository()
        self._router = HashBasedRouter()
        self._load_balancer = WeightedLoadBalancer()

        # Application
        self._shard_manager = ShardManager(self._repository, self._load_balancer)
        self._query_router = QueryRoutingService(self._router)

        logger.info("DatabaseShardingServiceFacade initialized")

    # Shard Management
    def register_shard(self, shard: DatabaseShard) -> None:
        """Register a new shard."""
        self._shard_manager.register_shard(shard)

    def get_active_shards(self) -> list[DatabaseShard]:
        """Get all active shards."""
        return self._shard_manager.get_active_shards()

    def update_shard_load(self, shard_id: str, load: float) -> None:
        """Update shard load."""
        self._shard_manager.update_shard_load(shard_id, load)

    def select_best_shard(self) -> DatabaseShard | None:
        """Select best shard for new data."""
        return self._shard_manager.select_best_shard()

    # Query Routing
    def route_query(
        self, shard_key_value: Any, config: ShardingConfig
    ) -> QueryRoute:
        """Route query to appropriate shard(s)."""
        return self._query_router.route_single_key(shard_key_value, config)

    def route_range_query(
        self, start: Any, end: Any, config: ShardingConfig
    ) -> QueryRoute:
        """Route range query."""
        return self._query_router.route_range(start, end, config)

    # Rebalancing
    def trigger_rebalance(self) -> list[tuple[str, str]]:
        """Trigger shard rebalancing."""
        return self._shard_manager.trigger_rebalance()


# Singleton instance
_facade_instance: DatabaseShardingServiceFacade | None = None


def get_database_sharding_service() -> DatabaseShardingServiceFacade:
    """Get or create singleton facade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = DatabaseShardingServiceFacade()
    return _facade_instance
