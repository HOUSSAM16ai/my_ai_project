"""
حزمة خدمة التحكم بالوصول (RBAC Package).

تُصدّر هذه الحزمة الواجهات العامة للخدمة لضمان التوافق مع الكود القائم.
"""

from app.services.rbac.constants import (
    ACCOUNT_SELF,
    ADMIN_ROLE,
    AI_CONFIG_READ,
    AI_CONFIG_WRITE,
    AUDIT_READ,
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_DESCRIPTIONS,
    QA_SUBMIT,
    ROLES_WRITE,
    STANDARD_ROLE,
    USERS_READ,
    USERS_WRITE,
)
from app.services.rbac.service import RBACService

__all__ = [
    "ACCOUNT_SELF",
    "ADMIN_ROLE",
    "AI_CONFIG_READ",
    "AI_CONFIG_WRITE",
    "AUDIT_READ",
    "DEFAULT_ROLE_PERMISSIONS",
    "PERMISSION_DESCRIPTIONS",
    "QA_SUBMIT",
    "RBACService",
    "ROLES_WRITE",
    "STANDARD_ROLE",
    "USERS_READ",
    "USERS_WRITE",
]
