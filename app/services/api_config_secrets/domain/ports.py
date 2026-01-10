from abc import ABC, abstractmethod

from .models import ConfigEntry, Environment, Secret, SecretAccessLog


class VaultBackend(ABC):
    """
    Abstract base for secret vault backends.
    This acts as a Port for the Infrastructure layer.
    """

    @abstractmethod
    def read_secret(self, secret_id: str) -> str | None:
        """Read secret from vault"""
        ...

    @abstractmethod
    def write_secret(self, secret_id: str, value: str, metadata: dict | None = None) -> bool:
        """Write secret to vault"""
        ...

    @abstractmethod
    def delete_secret(self, secret_id: str) -> bool:
        """Delete secret from vault"""
        ...

    @abstractmethod
    def list_secrets(self, prefix: str | None = None) -> list[str]:
        """List all secrets"""
        ...

    @abstractmethod
    def rotate_secret(self, secret_id: str) -> bool:
        """Rotate secret"""
        ...

class ConfigRepository(ABC):
    """Port for configuration storage"""

    @abstractmethod
    def get_config(self, environment: Environment, key: str) -> ConfigEntry | None:
        """Retrieve a configuration entry"""
        ...

    @abstractmethod
    def set_config(self, entry: ConfigEntry) -> None:
        """Save a configuration entry"""
        ...

    @abstractmethod
    def get_all_config(self, environment: Environment) -> dict[str, ConfigEntry]:
        """Get all configuration entries for an environment"""
        ...

class SecretMetadataRepository(ABC):
    """Port for storing secret metadata (not the values)"""

    @abstractmethod
    def get_secret_metadata(self, secret_id: str) -> Secret | None:
        """Retrieve secret metadata"""
        ...

    @abstractmethod
    def save_secret_metadata(self, secret: Secret) -> None:
        """Save secret metadata"""
        ...

    @abstractmethod
    def get_all_secrets(self) -> list[Secret]:
        """Get all secret metadata"""
        ...

class AuditLogger(ABC):
    """Port for audit logging"""

    @abstractmethod
    def log_access(self, log: SecretAccessLog) -> None:
        """Record an access log"""
        ...

    @abstractmethod
    def get_logs(self, secret_id: str | None = None, accessed_by: str | None = None, limit: int = 1000) -> list[SecretAccessLog]:
        """Retrieve logs"""
        ...
