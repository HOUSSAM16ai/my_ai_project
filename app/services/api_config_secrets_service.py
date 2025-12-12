# app/services/api_config_secrets_service.py
# ======================================================================================
# ==    SUPERHUMAN CONFIG & SECRETS MANAGEMENT SERVICE (v1.0 - VAULT EDITION)      ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام إدارة التهيئة والأسرار المركزي الخارق
#   ✨ المميزات الخارقة:
#   - Centralized configuration management
#   - Secrets encryption and rotation
#   - HashiCorp Vault integration support
#   - AWS Secrets Manager integration support
#   - Environment-based configuration (Dev/Staging/Prod)
#   - Dynamic configuration updates
#   - Audit logging for secrets access
#   - Secret versioning and rollback

import os
import threading
from typing import Any

from app.services.api_config_secrets.domain.models import (
    ConfigEntry,
    Environment,
    EnvironmentConfig,
    RotationPolicy,
    Secret,
    SecretAccessLog,
    SecretType,
)
from app.services.api_config_secrets.domain.ports import VaultBackend
from app.services.api_config_secrets.application.config_secrets_manager import ConfigSecretsManager
from app.services.api_config_secrets.infrastructure.memory_adapters import (
    InMemoryConfigRepository,
    InMemorySecretMetadataRepository,
    InMemoryAuditLogger,
)
from app.services.api_config_secrets.infrastructure.vault_adapters import (
    LocalVaultBackend,
    HashiCorpVaultBackend,
    AWSSecretsManagerBackend,
    SecretEncryption,
)

# Re-export key classes for backward compatibility
__all__ = [
    "Environment",
    "SecretType",
    "RotationPolicy",
    "Secret",
    "ConfigEntry",
    "SecretAccessLog",
    "EnvironmentConfig",
    "SecretEncryption",
    "VaultBackend",
    "LocalVaultBackend",
    "HashiCorpVaultBackend",
    "AWSSecretsManagerBackend",
    "ConfigSecretsService",
    "get_config_secrets_service",
]


class ConfigSecretsService:
    """
    Facade for ConfigSecretsManager to maintain backward compatibility.

    Features:
    - Multi-environment configuration management
    - Secure secrets storage with encryption
    - Integration with HashiCorp Vault / AWS Secrets Manager
    - Automatic secret rotation
    - Audit logging for all secret access
    - Dynamic configuration updates
    - Environment-based separation (Dev/Staging/Prod)
    """

    def __init__(self, vault_backend: VaultBackend | None = None):
        self._vault = vault_backend or LocalVaultBackend()
        self._config_repo = InMemoryConfigRepository()
        self._secret_repo = InMemorySecretMetadataRepository()
        self._audit_logger = InMemoryAuditLogger()

        self._manager = ConfigSecretsManager(
            vault_backend=self._vault,
            config_repo=self._config_repo,
            secret_metadata_repo=self._secret_repo,
            audit_logger=self._audit_logger,
        )

    # ==========================================================================
    # Exposed Properties for Backward Compatibility (if accessed directly)
    # ==========================================================================

    @property
    def vault(self) -> VaultBackend:
        return self._manager.vault

    @property
    def config_store(self):
        # Expose internal store via the repo if strictly necessary,
        # but better to avoid if possible.
        # The original code accessed config_store[environment][key].
        # We can simulate this property or let it break if it was private.
        # It was public: self.config_store: dict[...]
        # To strictly maintain compat, we might need to expose the underlying dict of the repo
        return self._config_repo._store

    @property
    def secrets_registry(self):
        return self._secret_repo._registry

    @property
    def access_logs(self):
        return self._audit_logger._logs

    @property
    def lock(self):
        # The manager handles locking internally, but if external code uses the lock...
        return self._config_repo._lock # Just return one of the locks

    # ==========================================================================
    # Proxy Methods
    # ==========================================================================

    def set_config(
        self,
        environment: Environment,
        key: str,
        value: Any,
        description: str,
        is_sensitive: bool = False,
        updated_by: str | None = None,
    ):
        """Set configuration value for an environment"""
        return self._manager.set_config(
            environment, key, value, description, is_sensitive, updated_by
        )

    def get_config(self, environment: Environment, key: str, default: Any = None) -> Any:
        """Get configuration value for an environment"""
        return self._manager.get_config(environment, key, default)

    def create_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType,
        environment: Environment,
        rotation_policy: RotationPolicy = RotationPolicy.NEVER,
        accessed_by: str = "system",
    ) -> str:
        """Create a new secret"""
        return self._manager.create_secret(
            name, value, secret_type, environment, rotation_policy, accessed_by
        )

    def get_secret(self, secret_id: str, accessed_by: str = "system") -> str | None:
        """Get secret value from vault"""
        return self._manager.get_secret(secret_id, accessed_by)

    def rotate_secret(self, secret_id: str, new_value: str, accessed_by: str = "system") -> bool:
        """Rotate a secret to a new value"""
        return self._manager.rotate_secret(secret_id, new_value, accessed_by)

    def check_rotation_needed(self) -> list[str]:
        """Check which secrets need rotation"""
        return self._manager.check_rotation_needed()

    # _calculate_next_rotation was internal/protected, but if we want to be safe:
    def _calculate_next_rotation(self, from_date, policy):
        return self._manager._calculate_next_rotation(from_date, policy)

    # _log_access was internal
    def _log_access(self, secret_id, accessed_by, action, success, reason=None):
        return self._manager._log_access(secret_id, accessed_by, action, success, reason)

    def get_environment_config(self, environment: Environment) -> EnvironmentConfig:
        """Get complete configuration for an environment"""
        return self._manager.get_environment_config(environment)

    def get_audit_report(
        self, secret_id: str | None = None, accessed_by: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Get audit logs for secret access"""
        return self._manager.get_audit_report(secret_id, accessed_by, limit)

    # Delegate private init method if called (though it was called in __init__)
    def _initialize_environments(self):
        # Already called by manager init
        pass


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_config_secrets_instance: ConfigSecretsService | None = None
_config_lock = threading.Lock()


def get_config_secrets_service() -> ConfigSecretsService:
    """Get singleton config & secrets service instance"""
    global _config_secrets_instance

    if _config_secrets_instance is None:
        with _config_lock:
            if _config_secrets_instance is None:
                # Determine which vault backend to use based on environment
                vault_type = os.environ.get("VAULT_BACKEND", "local")

                if vault_type == "hashicorp":
                    vault_url = os.environ.get("VAULT_URL", "http://localhost:8200")
                    vault_token = os.environ.get("VAULT_TOKEN", "")
                    backend = HashiCorpVaultBackend(vault_url, vault_token)
                elif vault_type == "aws":
                    region = os.environ.get("AWS_REGION", "us-east-1")
                    backend = AWSSecretsManagerBackend(region)
                else:
                    backend = LocalVaultBackend()

                _config_secrets_instance = ConfigSecretsService(vault_backend=backend)

    return _config_secrets_instance
