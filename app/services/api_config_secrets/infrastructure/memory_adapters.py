from collections import defaultdict, deque
import threading

from app.services.api_config_secrets.domain.models import ConfigEntry, Secret, SecretAccessLog, Environment
from app.services.api_config_secrets.domain.ports import ConfigRepository, SecretMetadataRepository, AuditLogger


class InMemoryConfigRepository(ConfigRepository):
    def __init__(self):
        self._store: dict[Environment, dict[str, ConfigEntry]] = defaultdict(dict)
        self._lock = threading.RLock()

    def get_config(self, environment: Environment, key: str) -> ConfigEntry | None:
        with self._lock:
            return self._store.get(environment, {}).get(key)

    def set_config(self, entry: ConfigEntry) -> None:
        with self._lock:
            self._store[entry.environment][entry.key] = entry

    def get_all_config(self, environment: Environment) -> dict[str, ConfigEntry]:
        with self._lock:
            return self._store.get(environment, {}).copy()


class InMemorySecretMetadataRepository(SecretMetadataRepository):
    def __init__(self):
        self._registry: dict[str, Secret] = {}
        self._lock = threading.RLock()

    def get_secret_metadata(self, secret_id: str) -> Secret | None:
        with self._lock:
            return self._registry.get(secret_id)

    def save_secret_metadata(self, secret: Secret) -> None:
        with self._lock:
            self._registry[secret.secret_id] = secret

    def get_all_secrets(self) -> list[Secret]:
        with self._lock:
            return list(self._registry.values())


class InMemoryAuditLogger(AuditLogger):
    def __init__(self, maxlen: int = 10000):
        self._logs: deque = deque(maxlen=maxlen)
        self._lock = threading.RLock()

    def log_access(self, log: SecretAccessLog) -> None:
        with self._lock:
            self._logs.append(log)

    def get_logs(self, secret_id: str | None = None, accessed_by: str | None = None, limit: int = 1000) -> list[SecretAccessLog]:
        with self._lock:
            logs = list(self._logs)

            if secret_id:
                logs = [log for log in logs if log.secret_id == secret_id]

            if accessed_by:
                logs = [log for log in logs if log.accessed_by == accessed_by]

            return logs[-limit:]
