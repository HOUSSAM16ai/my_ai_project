from dataclasses import dataclass
from enum import Enum, auto


class PoolerType(Enum):
    """Detected pooler type for adaptive configuration."""

    NONE = auto()  # Direct connection
    PGBOUNCER = auto()  # Standard PgBouncer
    SUPABASE_POOLER = auto()  # Supabase's PgBouncer (Transaction mode)
    NEON_POOLER = auto()  # Neon's connection pooler
    UNKNOWN_POOLER = auto()  # Unknown but detected pooler


class DatabaseType(Enum):
    """Supported database types."""

    POSTGRESQL = auto()
    SQLITE = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class PoolerSignature:
    """Signature pattern for pooler detection."""

    pattern: str
    pooler_type: PoolerType
    default_port: int
    requires_prepared_stmt_disable: bool
