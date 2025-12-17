# app/services/developer_portal/application/api_key_manager.py
"""API Key Management Service - Single Responsibility"""

import hashlib
import secrets
from datetime import datetime, timedelta, UTC

from app.services.developer_portal.domain.models import APIKey, APIKeyStatus
from app.services.developer_portal.domain.ports import APIKeyRepository


class APIKeyManager:
    """
    Manages API key lifecycle.

    Single Responsibility: API key creation, validation, rotation, revocation.
    """

    def __init__(self, repository: APIKeyRepository):
        self._repo = repository

    def generate_key(
        self,
        developer_id: str,
        name: str,
        scopes: list[str],
        expires_in_days: int | None = None,
    ) -> APIKey:
        """Generate new API key"""
        key_value = self._generate_secure_key()
        key_id = hashlib.sha256(key_value.encode()).hexdigest()[:16]

        api_key = APIKey(
            key_id=key_id,
            key_value=key_value,
            name=name,
            developer_id=developer_id,
            status=APIKeyStatus.ACTIVE,
            created_at=datetime.now(UTC),
            scopes=scopes,
            expires_at=(
                datetime.now(UTC) + timedelta(days=expires_in_days)
                if expires_in_days
                else None
            ),
        )

        self._repo.create(api_key)
        return api_key

    def revoke_key(self, key_id: str, reason: str) -> bool:
        """Revoke an API key"""
        api_key = self._repo.get(key_id)
        if not api_key:
            return False

        api_key.status = APIKeyStatus.REVOKED
        api_key.revoked_at = datetime.now(UTC)
        api_key.revocation_reason = reason
        self._repo.update(api_key)
        return True

    def validate_key(self, key_value: str) -> APIKey | None:
        """Validate API key"""
        key_id = hashlib.sha256(key_value.encode()).hexdigest()[:16]
        api_key = self._repo.get(key_id)

        if not api_key or api_key.status != APIKeyStatus.ACTIVE:
            return None

        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            return None

        # Update last used
        api_key.last_used_at = datetime.now(UTC)
        api_key.total_requests += 1
        self._repo.update(api_key)

        return api_key

    def rotate_key(self, key_id: str) -> APIKey | None:
        """Rotate an existing key"""
        old_key = self._repo.get(key_id)
        if not old_key:
            return None

        # Revoke old key
        self.revoke_key(key_id, "Key rotated")

        # Generate new key
        return self.generate_key(
            developer_id=old_key.developer_id,
            name=old_key.name,
            scopes=old_key.scopes,
        )

    def _generate_secure_key(self) -> str:
        """Generate cryptographically secure API key"""
        return f"sk_{secrets.token_urlsafe(32)}"
