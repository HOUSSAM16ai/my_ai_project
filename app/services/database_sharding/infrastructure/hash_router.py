"""Hash-based sharding router."""

import hashlib
from typing import Any

from ..domain.models import QueryRoute, ShardingConfig, ShardingStrategy
from ..domain.ports import ShardingRouter


class HashBasedRouter(ShardingRouter):
    """Routes queries using consistent hashing."""

    def route_query(self, shard_key_value: Any, config: ShardingConfig) -> QueryRoute:
        """Route query using hash function."""
        if config.strategy == ShardingStrategy.HASH_BASED:
            shard_id = self._hash_to_shard(shard_key_value, config.num_shards)
            return QueryRoute(shard_ids=[shard_id], is_cross_shard=False)

        # Fallback to first shard
        return QueryRoute(shard_ids=["shard_0"], is_cross_shard=False)

    def route_range_query(
        self, start: Any, end: Any, config: ShardingConfig
    ) -> QueryRoute:
        """Route range query - may span multiple shards."""
        # For hash-based, range queries typically need all shards
        shard_ids = [f"shard_{i}" for i in range(config.num_shards)]
        return QueryRoute(shard_ids=shard_ids, is_cross_shard=True, estimated_cost=len(shard_ids))

    def _hash_to_shard(self, key: Any, num_shards: int) -> str:
        """Hash key to shard ID."""
        key_str = str(key)
        hash_value = int(hashlib.md5(key_str.encode()).hexdigest(), 16)
        shard_num = hash_value % num_shards
        return f"shard_{shard_num}"
