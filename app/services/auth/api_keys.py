"""
إدارة مفاتيح واجهة برمجة التطبيقات (API Keys).

يوفر هذا المكون آلية لإنشاء وإدارة والتحقق من مفاتيح API
للاستخدام من قبل الخدمات الخارجية أو السكربتات (Service Accounts).

الميزات:
- مفاتيح مشفرة (Hashed) في قاعدة البيانات (لا نخزن المفتاح الخام).
- بادئة للتعرف السريع (e.g., `sk_live_...`).
- تحديد الصلاحيات (Scopes) لكل مفتاح.
- تتبع آخر استخدام (Last Used).
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

# We use a simulated In-Memory store for the Monolith Kernel phase
# untill the Auth Microservice is fully extracted with its own DB.
from app.core.domain.common import utc_now

logger = logging.getLogger(__name__)

@dataclass
class APIKey:
    """تمثيل مفتاح API (DTO)."""
    id: str
    name: str
    prefix: str
    key_hash: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    user_id: int
    expires_at: datetime | None = None
    last_used_at: datetime | None = None

# Simulated DB for Monolith Phase
_API_KEY_STORE: dict[str, APIKey] = {}

class APIKeyManager:
    """
    مدير مفاتيح API.

    ملاحظة: يعتمد حالياً على ذاكرة مؤقتة (In-Memory) كحل انتقالي
    حتى يتم إنشاء جدول `api_keys` في قاعدة البيانات.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session # Reserved for future DB usage

    async def create_key(
        self,
        user_id: int,
        name: str,
        scopes: list[str],
        expires_at: datetime | None = None
    ) -> tuple[APIKey, str]:
        """
        إنشاء مفتاح جديد.

        Returns:
            tuple[APIKey, str]: الكائن المخزن + المفتاح الخام (يظهر مرة واحدة فقط).
        """
        prefix = "sk_live_"
        raw_key = prefix + secrets.token_urlsafe(32)
        key_hash = self._hash_key(raw_key)
        key_id = secrets.token_urlsafe(8)

        api_key = APIKey(
            id=key_id,
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            scopes=scopes,
            is_active=True,
            expires_at=expires_at,
            created_at=utc_now(),
            last_used_at=None,
            user_id=user_id
        )

        # Simulate DB Insert
        _API_KEY_STORE[key_hash] = api_key
        logger.info(f"🔑 Created API Key '{name}' for user {user_id}")

        return api_key, raw_key

    async def verify_key(self, raw_key: str) -> APIKey | None:
        """
        التحقق من المفتاح.
        """
        key_hash = self._hash_key(raw_key)

        # Simulate DB Select
        api_key = _API_KEY_STORE.get(key_hash)

        if not api_key:
            return None

        if not api_key.is_active:
            return None

        if api_key.expires_at and api_key.expires_at < utc_now():
            return None

        # Simulate DB Update (Last Used)
        api_key.last_used_at = utc_now()

        return api_key

    async def revoke_key(self, raw_key: str) -> bool:
        """إبطال مفتاح."""
        key_hash = self._hash_key(raw_key)
        if key_hash in _API_KEY_STORE:
            _API_KEY_STORE[key_hash].is_active = False
            return True
        return False

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
