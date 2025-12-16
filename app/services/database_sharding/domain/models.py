"""Domain models for Database Sharding service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ShardingStrategy(Enum):
    """Sharding strategies."""

    RANGE_BASED = "range_based"
    HASH_BASED = "hash_based"
    GEOGRAPHIC = "geographic"
    LIST_BASED = "list_based"
    COMPOSITE = "composite"


class ShardState(Enum):
    """Shard state."""

    ACTIVE = "active"
    READONLY = "readonly"
    MIGRATING = "migrating"
    OFFLINE = "offline"


class ReplicationRole(Enum):
    """Replication role."""

    MASTER = "master"
    REPLICA = "replica"
    MULTI_MASTER = "multi_master"


@dataclass
class DatabaseShard:
    """Database shard definition."""

    shard_id: str
    name: str
    connection_string: str
    state: ShardState
    role: ReplicationRole
    range_start: int | None = None
    range_end: int | None = None
    region: str | None = None
    partition_keys: list[str] = field(default_factory=list)
    weight: float = 1.0
    current_load: float = 0.0
    max_connections: int = 100
    created_at: datetime | None = None


@dataclass
class ShardingConfig:
    """Sharding configuration."""

    strategy: ShardingStrategy
    shard_key: str
    num_shards: int = 4
    replication_factor: int = 2
    auto_rebalance: bool = True


@dataclass
class QueryRoute:
    """Query routing information."""

    shard_ids: list[str]
    is_cross_shard: bool
    estimated_cost: float = 0.0
