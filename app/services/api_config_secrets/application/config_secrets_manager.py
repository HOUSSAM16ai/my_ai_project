import hashlib
from dataclasses import dataclass
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


@dataclass(slots=True)
class ConfigSetting:
    """تعريف إعداد تكوين مبسط يساعد المبتدئين على رؤية الحقول المطلوبة بوضوح."""

    environment: Environment
    key: str
    value: object
    description: str
    is_sensitive: bool = False
    updated_by: str | None = None

    def to_entry(self) -> ConfigEntry:
        """إنشاء كائن تخزين معياري يمر بسلاسة عبر منافذ التخزين."""

        return ConfigEntry(
            key=self.key,
            value=self.value,
            environment=self.environment,
            description=self.description,
            is_sensitive=self.is_sensitive,
            updated_by=self.updated_by,
        )


@dataclass(slots=True)
class SecretRequest:
    """طلب إنشاء سر جديد بحقول موحّدة تسهّل التدقيق والتوثيق."""

    name: str
    value: str
    secret_type: SecretType
    environment: Environment
    rotation_policy: RotationPolicy = RotationPolicy.NEVER
    accessed_by: str = "system"

class ConfigSecretsManager:
    """خدمة تطبيقية تنظّم ضبط الإعدادات وإدارة الأسرار بواجهات واضحة."""

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

    def _initialize_environments(self) -> None:
        """تهيئة إعدادات افتراضية للبيئات لضمان تشغيل فوري قابل للفهم."""
        self._initialize_development_config()
        self._initialize_staging_config()
        self._initialize_production_config()

    def _initialize_development_config(self) -> None:
        """تهيئة إعدادات التطوير بوضوح لتسريع عمل المبتدئين."""

        self.set_config(
            ConfigSetting(
                environment=Environment.DEVELOPMENT,
                key="debug_mode",
                value=True,
                description="تمكين نمط التصحيح والسجلات التفصيلية",
            )
        )
        self.set_config(
            ConfigSetting(
                environment=Environment.DEVELOPMENT,
                key="rate_limit_enabled",
                value=False,
                description="تعطيل ضبط المعدل لتجارب تطوير أسرع",
            )
        )

    def _initialize_staging_config(self) -> None:
        """تهيئة بيئة الاختبار بإعدادات قريبة من الإنتاج للموثوقية."""

        self.set_config(
            ConfigSetting(
                environment=Environment.STAGING,
                key="debug_mode",
                value=False,
                description="إيقاف نمط التصحيح في بيئة الاختبار",
            )
        )
        self.set_config(
            ConfigSetting(
                environment=Environment.STAGING,
                key="rate_limit_enabled",
                value=True,
                description="تفعيل ضبط المعدل لمضاهاة بيئة الإنتاج",
            )
        )

    def _initialize_production_config(self) -> None:
        """تهيئة الإنتاج بأعلى معايير الأمان والتقييد."""

        self.set_config(
            ConfigSetting(
                environment=Environment.PRODUCTION,
                key="debug_mode",
                value=False,
                description="حظر نمط التصحيح تماماً في الإنتاج",
            )
        )
        self.set_config(
            ConfigSetting(
                environment=Environment.PRODUCTION,
                key="rate_limit_enabled",
                value=True,
                description="فرض ضبط المعدل في الإنتاج",
            )
        )
        self.set_config(
            ConfigSetting(
                environment=Environment.PRODUCTION,
                key="strict_ssl",
                value=True,
                description="فرض تشفير SSL/TLS في جميع الاتصالات",
            )
        )

    def set_config(self, setting: ConfigSetting) -> None:
        """تطبيق إعداد تكوين موحّد على بيئة محددة بطريقة قابلة للتدقيق."""

        self.config_repo.set_config(setting.to_entry())

    def get_config(
        self, environment: Environment, key: str, default: object | None = None
    ) -> object | None:
        """الحصول على قيمة إعداد مع دعم قيمة افتراضية واضحة."""
        entry = self.config_repo.get_config(environment, key)
        if entry:
            return entry.value
        return default

    def create_secret(self, request: SecretRequest) -> str:
        """إنشاء سر جديد من طلب موحّد وتخزينه مع تسجيل كامل."""

        secret_id = self._generate_secret_id(request.name, request.environment)
        self._store_in_vault(secret_id, request.value)
        secret = self._create_secret_metadata(
            secret_id,
            request.name,
            request.secret_type,
            request.environment,
            request.rotation_policy,
        )
        self.secret_repo.save_secret_metadata(secret)
        self._log_access(secret_id, request.accessed_by, "write", True)

        return secret_id

    def _generate_secret_id(self, name: str, environment: Environment) -> str:
        """توليد معرف سر قصير ثابت الطول اعتماداً على الاسم والبيئة والزمن."""
        return hashlib.sha256(
            f"{name}{environment.value}{datetime.now(UTC)}".encode()
        ).hexdigest()[:16]

    def _store_in_vault(self, secret_id: str, value: str) -> None:
        """حفظ السر في الخزينة مع رفع خطأ واضح عند الفشل."""
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
        """بناء وصف السر المخزن دون الاحتفاظ بالقيمة النصية في الذاكرة."""
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
        """استرجاع السر من الخزينة مع تسجيل الوصول."""
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
        """تدوير السر إلى قيمة جديدة مع تحديث بيانات التدوير."""
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
        """تحديد الأسرار التي حان موعد تدويرها بناءً على السياسة المعلنة."""
        now = datetime.now(UTC)
        all_secrets = self.secret_repo.get_all_secrets()
        return [
            secret.secret_id
            for secret in all_secrets
            if secret.next_rotation and secret.next_rotation <= now
        ]

    def _calculate_next_rotation(self, from_date: datetime, policy: RotationPolicy) -> datetime:
        """حساب تاريخ التدوير القادم بالاعتماد على سياسة معرّفة بوضوح."""
        if policy == RotationPolicy.DAILY:
            return from_date + timedelta(days=1)
        if policy == RotationPolicy.WEEKLY:
            return from_date + timedelta(weeks=1)
        if policy == RotationPolicy.MONTHLY:
            return from_date + timedelta(days=30)
        if policy == RotationPolicy.QUARTERLY:
            return from_date + timedelta(days=90)
        return from_date + timedelta(days=365)  # Default to yearly

    def _log_access(
        self,
        secret_id: str,
        accessed_by: str,
        action: str,
        success: bool,
        reason: str | None = None,
    ):
        """تسجيل الوصول للأسرار لأغراض التتبع والتدقيق الأمني."""
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
        """تجميع التكوين الكامل والربط بالأسرار لبيئة محددة."""
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
        """استخراج تقرير تدقيق للوصول إلى الأسرار مع إمكانية التصفية."""
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
