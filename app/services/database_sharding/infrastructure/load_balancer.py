"""Load balancer implementation."""

import logging

from ..domain.models import DatabaseShard
from ..domain.ports import LoadBalancer

logger = logging.getLogger(__name__)


class WeightedLoadBalancer(LoadBalancer):
    """Load balancer using weighted round-robin."""

    def select_shard(self, shards: list[DatabaseShard]) -> DatabaseShard:
        """Select shard with lowest load."""
        if not shards:
            raise ValueError("No shards available")

        # Select shard with lowest load relative to weight
        best_shard = min(shards, key=lambda s: s.current_load / s.weight)
        return best_shard

    def rebalance_shards(self, shards: list[DatabaseShard]) -> list[tuple[str, str]]:
        """Determine rebalancing migrations."""
        if len(shards) < 2:
            return []

        migrations = []
        avg_load = sum(s.current_load for s in shards) / len(shards)
        threshold = avg_load * 0.2  # 20% threshold

        overloaded = [s for s in shards if s.current_load > avg_load + threshold]
        underloaded = [s for s in shards if s.current_load < avg_load - threshold]

        for over_shard in overloaded:
            for under_shard in underloaded:
                migrations.append((over_shard.shard_id, under_shard.shard_id))
                break

        return migrations
