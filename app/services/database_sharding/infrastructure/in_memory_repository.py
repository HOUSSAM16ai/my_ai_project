"""In-memory shard repository."""

from ..domain.models import DatabaseShard
from ..domain.ports import ShardRepository


class InMemoryShardRepository(ShardRepository):
    """In-memory storage for shards."""

    def __init__(self):
        self._shards: dict[str, DatabaseShard] = {}

    def add_shard(self, shard: DatabaseShard) -> None:
        """Add a new shard."""
        self._shards[shard.shard_id] = shard

    def get_shard(self, shard_id: str) -> DatabaseShard | None:
        """Get shard by ID."""
        return self._shards.get(shard_id)

    def list_shards(self) -> list[DatabaseShard]:
        """List all shards."""
        return list(self._shards.values())

    def update_shard(self, shard: DatabaseShard) -> None:
        """Update shard information."""
        self._shards[shard.shard_id] = shard
