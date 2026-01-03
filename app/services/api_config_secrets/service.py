from typing import Any

import os
import threading

from app.services.api_config_secrets.application.config_secrets_manager import ConfigSecretsManager
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
from app.services.api_config_secrets.infrastructure.memory_adapters import (
    InMemoryAuditLogger,
    InMemoryConfigRepository,
    InMemorySecretMetadataRepository,
)
from app.services.api_config_secrets.infrastructure.vault_adapters import (
    AWSSecretsManagerBackend,
    HashiCorpVaultBackend,
    LocalVaultBackend,
    SecretEncryption,
)

__all__ = [
    'AWSSecretsManagerBackend',
    'ConfigEntry',
    'ConfigSecretsService',
    'Environment',
    'EnvironmentConfig',
    'HashiCorpVaultBackend',
    'LocalVaultBackend',
    'RotationPolicy',
    'Secret',
    'SecretAccessLog',
    'SecretEncryption',
    'SecretType',
    'VaultBackend',
    'get_config_secrets_service',
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

    def __init__(self, vault_backend: (VaultBackend | None)=None):
        self._vault = vault_backend or LocalVaultBackend()
        self._config_repo = InMemoryConfigRepository()
        self._secret_repo = InMemorySecretMetadataRepository()
        self._audit_logger = InMemoryAuditLogger()
        self._manager = ConfigSecretsManager(vault_backend=self._vault,
            config_repo=self._config_repo, secret_metadata_repo=self.
            _secret_repo, audit_logger=self._audit_logger)

    @property
    def vault(self) ->VaultBackend:
        return self._manager.vault

    @property
    def lock(self) -> None:
        return self._config_repo._lock

    # TODO: Reduce parameters (7 params) - Use config object
    def set_config(self, environment: Environment, key: str, value: dict[str, str | int | bool],
        description: str, is_sensitive: bool=False, updated_by: (str | None
        )=None):
        """Set configuration value for an environment"""
        return self._manager.set_config(environment, key, value,
            description, is_sensitive, updated_by)

    def get_config(self, environment: Environment, key: str, default: dict[str, str | int | bool]=None
        ) ->dict[str, str | int | bool]:
        """Get configuration value for an environment"""
        return self._manager.get_config(environment, key, default)
# TODO: Reduce parameters (7 params) - Use config object

    def create_secret(self, name: str, value: str, secret_type: SecretType,
        environment: Environment, rotation_policy: RotationPolicy=
        RotationPolicy.NEVER, accessed_by: str='system') ->str:
        """Create a new secret"""
        return self._manager.create_secret(name, value, secret_type,
            environment, rotation_policy, accessed_by)

    def get_secret(self, secret_id: str, accessed_by: str='system') ->(str |
        None):
        """Get secret value from vault"""
        return self._manager.get_secret(secret_id, accessed_by)

    def rotate_secret(self, secret_id: str, new_value: str, accessed_by:
        str='system') ->bool:
        """Rotate a secret to a new value"""
        return self._manager.rotate_secret(secret_id, new_value, accessed_by)

    def check_rotation_needed(self) ->list[str]:
        """Check which secrets need rotation"""
        return self._manager.check_rotation_needed()

    def _calculate_next_rotation(self, from_date, policy):
        # TODO: Reduce parameters (6 params) - Use config object
        return self._manager._calculate_next_rotation(from_date, policy)

    def _log_access(self, secret_id, accessed_by, action, success, reason=None
        ):
        return self._manager._log_access(secret_id, accessed_by, action,
            success, reason)

    def get_environment_config(self, environment: Environment
        ) ->EnvironmentConfig:
        """Get complete configuration for an environment"""
        return self._manager.get_environment_config(environment)

    def get_audit_report(self, secret_id: (str | None)=None, accessed_by: (
        str | None)=None, limit: int=1000) ->list[dict[str, Any]]:
        """Get audit logs for secret access"""
        return self._manager.get_audit_report(secret_id, accessed_by, limit)

    def _initialize_environments(self):
        pass

_config_secrets_instance: ConfigSecretsService | None = None
_config_lock = threading.Lock()

def get_config_secrets_service() ->ConfigSecretsService:
    """Get singleton config & secrets service instance"""
    global _config_secrets_instance
    if _config_secrets_instance is None:
        with _config_lock:
            if _config_secrets_instance is None:
                vault_type = os.environ.get('VAULT_BACKEND', 'local')
                if vault_type == 'hashicorp':
                    vault_url = os.environ.get('VAULT_URL',
                        'http://localhost:8200')
                    vault_token = os.environ.get('VAULT_TOKEN', '')
                    backend = HashiCorpVaultBackend(vault_url, vault_token)
                elif vault_type == 'aws':
                    region = os.environ.get('AWS_REGION', 'us-east-1')
                    backend = AWSSecretsManagerBackend(region)
                else:
                    backend = LocalVaultBackend()
                _config_secrets_instance = ConfigSecretsService(vault_backend
                    =backend)
    return _config_secrets_instance
