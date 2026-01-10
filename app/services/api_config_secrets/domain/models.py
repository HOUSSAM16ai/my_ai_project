from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class Environment(Enum):
    """Deployment environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

class SecretType(Enum):
    """Types of secrets"""

    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    WEBHOOK_SECRET = "webhook_secret"
    CERTIFICATE = "certificate"

class RotationPolicy(Enum):
    """Secret rotation policies"""

    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"

@dataclass
class Secret:
    """Secret metadata and value"""

    secret_id: str
    name: str
    secret_type: SecretType
    environment: Environment
    value: str  # Encrypted value or reference
    created_at: datetime
    updated_at: datetime
    version: int = 1
    rotation_policy: RotationPolicy = RotationPolicy.NEVER
    next_rotation: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)

@dataclass
class ConfigEntry:
    """Configuration entry"""

    key: str
    value: object
    environment: Environment
    description: str
    is_sensitive: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_by: str | None = None

@dataclass
class SecretAccessLog:
    """Secret access audit log"""

    log_id: str
    secret_id: str
    accessed_at: datetime
    accessed_by: str
    action: str  # 'read', 'write', 'rotate', 'delete'
    ip_address: str | None = None
    success: bool = True
    reason: str | None = None

@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""

    environment: Environment
    config: dict[str, object]
    secrets: dict[str, str]  # Secret references, not values
    feature_flags: dict[str, bool]
    resource_limits: dict[str, object]
    deployment_metadata: dict[str, object]
