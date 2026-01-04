import hashlib
from datetime import UTC, datetime, timedelta

from app.services.api_config_secrets.domain.models import (
    ConfigEntry,
    Environment,
    EnvironmentConfig,
    RotationPolicy,
    Secret,
    SecretAccessLog,
    SecretType,
)
from app.services.api_config_secrets.domain.ports import (
    AuditLogger,
    ConfigRepository,
    SecretMetadataRepository,
    VaultBackend,
)

class ConfigSecretsManager:
    """
    Application service that orchestrates configuration and secrets management.
    """

    def __init__(
        self,
        vault_backend: VaultBackend,
        config_repo: ConfigRepository,
        secret_metadata_repo: SecretMetadataRepository,
        audit_logger: AuditLogger,
    ):
        self.vault = vault_backend
        self.config_repo = config_repo
        self.secret_repo = secret_metadata_repo
        self.audit_logger = audit_logger

        self._initialize_environments()

    def _initialize_environments(self):
        """
        تهيئة البيئات الافتراضية | Initialize default configurations for each environment
        
        يقوم بتهيئة إعدادات البيئات الثلاث (تطوير، اختبار، إنتاج)
        Initializes settings for three environments (development, staging, production)
        """
        self._initialize_development_config()
        self._initialize_staging_config()
        self._initialize_production_config()

    def _initialize_development_config(self) -> None:
        """
        تهيئة بيئة التطوير | Initialize development environment
        
        تفعيل وضع التطوير وتعطيل القيود للتطوير السريع
        Enable development mode and disable restrictions for rapid development
        """
        self.set_config(
            Environment.DEVELOPMENT, "debug_mode", True, "Enable debug mode and verbose logging"
        )
        self.set_config(
            Environment.DEVELOPMENT,
            "rate_limit_enabled",
            False,
            "Disable rate limiting for easier development",
        )

    def _initialize_staging_config(self) -> None:
        """
        تهيئة بيئة الاختبار | Initialize staging environment
        
        إعدادات مشابهة للإنتاج للاختبار الواقعي
        Production-like settings for realistic testing
        """
        self.set_config(Environment.STAGING, "debug_mode", False, "Disable debug mode in staging")
        self.set_config(
            Environment.STAGING,
            "rate_limit_enabled",
            True,
            "Enable rate limiting to match production",
        )

    def _initialize_production_config(self) -> None:
        """
        تهيئة بيئة الإنتاج | Initialize production environment
        
        أعلى مستوى من الأمان والموثوقية
        Highest level of security and reliability
        """
        self.set_config(
            Environment.PRODUCTION, "debug_mode", False, "Debug mode always off in production"
        )
        self.set_config(
            Environment.PRODUCTION,
            "rate_limit_enabled",
            True,
            "Rate limiting mandatory in production",
        )
        self.set_config(Environment.PRODUCTION, "strict_ssl", True, "Enforce SSL/TLS in production")

    # TODO: Reduce parameters (7 params) - Use config object
    def set_config(
        self,
        environment: Environment,
        key: str,
        value: dict[str, str | int | bool],
        description: str,
        is_sensitive: bool = False,
        updated_by: str | None = None,
    ) -> None:
        """Set configuration value for an environment"""
        entry = ConfigEntry(
            key=key,
            value=value,
            environment=environment,
            description=description,
            is_sensitive=is_sensitive,
            updated_by=updated_by,
        )
        self.config_repo.set_config(entry)

    def get_config(self, environment: Environment, key: str, default: dict[str, str | int | bool] = None) -> dict[str, str | int | bool]:
        """Get configuration value for an environment"""
        entry = self.config_repo.get_config(environment, key)
        if entry:
            return entry.value
        return default

    def create_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType,
        environment: Environment,
        rotation_policy: RotationPolicy = RotationPolicy.NEVER,
        accessed_by: str = "system",
    ) -> str:
        """
        إنشاء سر جديد | Create a new secret
        
        يقوم بإنشاء سر جديد وتخزينه في الخزينة
        Creates a new secret and stores it in the vault
        
        Args:
            name: اسم السر | Secret name
            value: قيمة السر | Secret value
            secret_type: نوع السر | Secret type
            environment: البيئة | Environment
            rotation_policy: سياسة التدوير | Rotation policy
            accessed_by: المستخدم | User accessing
            
        Returns:
            معرف السر | Secret ID
        """
        secret_id = self._generate_secret_id(name, environment)
        self._store_in_vault(secret_id, value)
        secret = self._create_secret_metadata(
            secret_id, name, secret_type, environment, rotation_policy
        )
        self.secret_repo.save_secret_metadata(secret)
        self._log_access(secret_id, accessed_by, "write", True)
        
        return secret_id

    def _generate_secret_id(self, name: str, environment: Environment) -> str:
        """
        توليد معرف السر | Generate secret ID
        
        Args:
            name: اسم السر | Secret name
            environment: البيئة | Environment
            
        Returns:
            معرف السر | Secret ID
        """
        return hashlib.sha256(
            f"{name}{environment.value}{datetime.now(UTC)}".encode()
        ).hexdigest()[:16]

    def _store_in_vault(self, secret_id: str, value: str) -> None:
        """
        التخزين في الخزينة | Store in vault
        
        Args:
            secret_id: معرف السر | Secret ID
            value: قيمة السر | Secret value
            
        Raises:
            RuntimeError: إذا فشل التخزين | If storage fails
        """
        success = self.vault.write_secret(secret_id, value)
        if not success:
            raise RuntimeError(f"Failed to write secret to vault: {secret_id}")

    def _create_secret_metadata(
        self,
        secret_id: str,
        name: str,
        secret_type: SecretType,
        environment: Environment,
        rotation_policy: RotationPolicy
    ) -> Secret:
        """
        إنشاء بيانات وصفية للسر | Create secret metadata
        
        Args:
            secret_id: معرف السر | Secret ID
            name: اسم السر | Secret name
            secret_type: نوع السر | Secret type
            environment: البيئة | Environment
            rotation_policy: سياسة التدوير | Rotation policy
            
        Returns:
            كائن السر | Secret object
        """
        now = datetime.now(UTC)
        secret = Secret(
            secret_id=secret_id,
            name=name,
            secret_type=secret_type,
            environment=environment,
            value="[ENCRYPTED]",  # Don't store actual value in memory/metadata
            created_at=now,
            updated_at=now,
            rotation_policy=rotation_policy,
        )

        # Calculate next rotation if needed
        if rotation_policy != RotationPolicy.NEVER:
            secret.next_rotation = self._calculate_next_rotation(now, rotation_policy)

        return secret

    def get_secret(self, secret_id: str, accessed_by: str = "system") -> str | None:
        """Get secret value from vault"""
        secret_meta = self.secret_repo.get_secret_metadata(secret_id)
        if not secret_meta:
            self._log_access(secret_id, accessed_by, "read", False, "Secret not found")
            return None

        # Read from vault
        value = self.vault.read_secret(secret_id)

        # Log access
        self._log_access(secret_id, accessed_by, "read", value is not None)

        return value

    def rotate_secret(self, secret_id: str, new_value: str, accessed_by: str = "system") -> bool:
        """Rotate a secret to a new value"""
        secret_meta = self.secret_repo.get_secret_metadata(secret_id)
        if not secret_meta:
            return False

        # Write new value
        success = self.vault.write_secret(secret_id, new_value)

        if success:
            secret_meta.version += 1
            secret_meta.updated_at = datetime.now(UTC)

            # Calculate next rotation
            if secret_meta.rotation_policy != RotationPolicy.NEVER:
                secret_meta.next_rotation = self._calculate_next_rotation(
                    secret_meta.updated_at, secret_meta.rotation_policy
                )

            self.secret_repo.save_secret_metadata(secret_meta)

        # Log rotation
        self._log_access(secret_id, accessed_by, "rotate", success)

        return success

    def check_rotation_needed(self) -> list[str]:
        """Check which secrets need rotation"""
        now = datetime.now(UTC)
        all_secrets = self.secret_repo.get_all_secrets()
        return [
            secret.secret_id
            for secret in all_secrets
            if secret.next_rotation and secret.next_rotation <= now
        ]

    def _calculate_next_rotation(self, from_date: datetime, policy: RotationPolicy) -> datetime:
        """Calculate next rotation date based on policy"""
        if policy == RotationPolicy.DAILY:
            return from_date + timedelta(days=1)
        if policy == RotationPolicy.WEEKLY:
            return from_date + timedelta(weeks=1)
        if policy == RotationPolicy.MONTHLY:
            return from_date + timedelta(days=30)
        if policy == RotationPolicy.QUARTERLY:
            return from_date + timedelta(days=90)
        # TODO: Reduce parameters (6 params) - Use config object
        return from_date + timedelta(days=365)  # Default to yearly

    def _log_access(
        self,
        secret_id: str,
        accessed_by: str,
        action: str,
        success: bool,
        reason: str | None = None,
    ):
        """Log secret access for audit trail"""
        log = SecretAccessLog(
            log_id=hashlib.sha256(
                f"{secret_id}{accessed_by}{datetime.now(UTC)}".encode()
            ).hexdigest()[:16],
            secret_id=secret_id,
            accessed_at=datetime.now(UTC),
            accessed_by=accessed_by,
            action=action,
            success=success,
            reason=reason,
        )

        self.audit_logger.log_access(log)

    def get_environment_config(self, environment: Environment) -> EnvironmentConfig:
        """Get complete configuration for an environment"""
        config_entries = self.config_repo.get_all_config(environment)

        config = {
            key: entry.value
            for key, entry in config_entries.items()
            if not entry.is_sensitive
        }

        all_secrets = self.secret_repo.get_all_secrets()
        secrets = {
            secret.name: secret.secret_id
            for secret in all_secrets
            if secret.environment == environment
        }

        return EnvironmentConfig(
            environment=environment,
            config=config,
            secrets=secrets,
            feature_flags={},
            resource_limits={},
            deployment_metadata={},
        )

    def get_audit_report(
        self, secret_id: str | None = None, accessed_by: str | None = None, limit: int = 1000
    ) -> list[dict[str, object]]:
        """Get audit logs for secret access"""
        logs = self.audit_logger.get_logs(secret_id, accessed_by, limit)

        return [
            {
                "log_id": log.log_id,
                "secret_id": log.secret_id,
                "accessed_at": log.accessed_at.isoformat(),
                "accessed_by": log.accessed_by,
                "action": log.action,
                "success": log.success,
                "reason": log.reason,
            }
            for log in logs
        ]
