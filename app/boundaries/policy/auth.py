from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

@dataclass
class Principal:
    """
    الكيان المصادق عليه (Principal)

    يمثل المستخدم أو الخدمة المصادقة
    """

    id: str
    type: str  # user, service, system
    claims: dict[str, Any] = field(default_factory=dict)
    roles: set[str] = field(default_factory=set)
    authenticated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None

    def has_claim(self, claim_name: str, claim_value: Any | None = None) -> bool:
        """التحقق من وجود claim"""
        if claim_name not in self.claims:
            return False
        if claim_value is None:
            return True
        return self.claims[claim_name] == claim_value

    def has_role(self, role: str) -> bool:
        """التحقق من وجود دور"""
        return role in self.roles

    def is_expired(self) -> bool:
        """التحقق مما إذا كانت المصادقة منتهية"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class AuthenticationService(ABC):
    """
    خدمة المصادقة (Authentication Service)

    مسؤولة فقط عن التحقق من هوية المستخدم:
    - إدارة المستخدمين والبيانات الاعتمادية
    - إصدار الرموز (Token Issuance) - JWT/OAuth2
    - تحديث الرموز (Token Refresh)
    - لا علاقة لها بالصلاحيات التفصيلية
    """

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> Principal | None:
        """
        مصادقة مستخدم

        Args:
            credentials: البيانات الاعتمادية (email/password, token, etc.)

        Returns:
            Principal إذا نجحت المصادقة، None إذا فشلت
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> str | None:
        """تحديث رمز الوصول"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """إلغاء رمز"""
        pass
