"""Shard management application service."""

import logging
from datetime import UTC, datetime

from ..domain.models import DatabaseShard, ShardState
from ..domain.ports import LoadBalancer, ShardRepository

logger = logging.getLogger(__name__)


class ShardManager:
    """Manages database shards."""

    def __init__(self, repository: ShardRepository, load_balancer: LoadBalancer):
        self.repository = repository
        self.load_balancer = load_balancer

    def register_shard(self, shard: DatabaseShard) -> None:
        """Register a new shard."""
        shard.created_at = datetime.now(UTC)
        self.repository.add_shard(shard)
        logger.info(f"Registered shard: {shard.shard_id}")

    def get_active_shards(self) -> list[DatabaseShard]:
        """Get all active shards."""
        all_shards = self.repository.list_shards()
        return [s for s in all_shards if s.state == ShardState.ACTIVE]

    def update_shard_load(self, shard_id: str, load: float) -> None:
        """Update shard load metrics."""
        shard = self.repository.get_shard(shard_id)
        if shard:
            shard.current_load = load
            self.repository.update_shard(shard)

    def select_best_shard(self) -> DatabaseShard | None:
        """Select best shard for new data."""
        active_shards = self.get_active_shards()
        if not active_shards:
            return None
        return self.load_balancer.select_shard(active_shards)

    def trigger_rebalance(self) -> list[tuple[str, str]]:
        """Trigger shard rebalancing."""
        all_shards = self.repository.list_shards()
        migrations = self.load_balancer.rebalance_shards(all_shards)
        logger.info(f"Rebalancing: {len(migrations)} migrations planned")
        return migrations
