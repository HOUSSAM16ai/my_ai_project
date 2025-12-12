"""Domain ports for Database Sharding service."""

from abc import ABC, abstractmethod
from typing import Any

from .models import DatabaseShard, QueryRoute, ShardingConfig


class ShardRepository(ABC):
    """Repository for shard management."""

    @abstractmethod
    def add_shard(self, shard: DatabaseShard) -> None:
        """Add a new shard."""
        pass

    @abstractmethod
    def get_shard(self, shard_id: str) -> DatabaseShard | None:
        """Get shard by ID."""
        pass

    @abstractmethod
    def list_shards(self) -> list[DatabaseShard]:
        """List all shards."""
        pass

    @abstractmethod
    def update_shard(self, shard: DatabaseShard) -> None:
        """Update shard information."""
        pass


class ShardingRouter(ABC):
    """Routing interface for sharding."""

    @abstractmethod
    def route_query(self, shard_key_value: Any, config: ShardingConfig) -> QueryRoute:
        """Route query to appropriate shard(s)."""
        pass

    @abstractmethod
    def route_range_query(
        self, start: Any, end: Any, config: ShardingConfig
    ) -> QueryRoute:
        """Route range query across shards."""
        pass


class LoadBalancer(ABC):
    """Load balancing interface."""

    @abstractmethod
    def select_shard(self, shards: list[DatabaseShard]) -> DatabaseShard:
        """Select best shard based on load."""
        pass

    @abstractmethod
    def rebalance_shards(self, shards: list[DatabaseShard]) -> list[tuple[str, str]]:
        """Rebalance data across shards. Returns list of (from_shard, to_shard)."""
        pass
