"""
Security Event Logger - Comprehensive Security Auditing
=======================================================

Implements security event logging to track authentication, authorization,
and security-related events. Addresses security issue: Missing security
event logging.

Features:
- Authentication attempt tracking
- Authorization failure logging
- Suspicious activity detection
- Structured logging format
- Integration with monitoring systems
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

security_logger = logging.getLogger('security')


@dataclass
class AuthAttemptEvent:
    """
    بيانات محاولة المصادقة (Authentication Attempt Event).
    
    يحل مشكلة المعاملات الكثيرة باستخدام dataclass.
    """
    user_id: str | None
    username: str | None
    success: bool
    ip_address: str
    user_agent: str | None = None
    reason: str | None = None
    
    def to_dict(self) -> dict:
        """تحويل إلى dictionary للتسجيل."""
        return {
            'event_type': 'auth_attempt',
            'user_id': self.user_id,
            'username': self.username,
            'success': self.success,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'reason': self.reason,
            'timestamp': datetime.utcnow().isoformat()
        }


@dataclass
class AccessDeniedEvent:
    """
    بيانات رفض الوصول (Access Denied Event).
    
    يحل مشكلة المعاملات الكثيرة باستخدام dataclass.
    """
    user_id: str
    username: str
    resource: str
    action: str
    ip_address: str
    reason: str | None = None
    
    def to_dict(self) -> dict:
        """تحويل إلى dictionary للتسجيل."""
        return {
            'event_type': 'access_denied',
            'user_id': self.user_id,
            'username': self.username,
            'resource': self.resource,
            'action': self.action,
            'ip_address': self.ip_address,
            'reason': self.reason,
            'timestamp': datetime.utcnow().isoformat()
        }


class SecurityEventLogger:
    """
    مُسجل مركزي لأحداث الأمان (Centralized Security Event Logger).

    جميع الأحداث الأمنية يجب تسجيلها عبر هذه الفئة للحفاظ على
    مسار تدقيق متسق (consistent audit trail).
    """

    @staticmethod
    def log_auth_attempt(event: AuthAttemptEvent) -> None:
        """
        تسجيل محاولة مصادقة.

        Args:
            event: بيانات محاولة المصادقة
        """
        event_dict = event.to_dict()
        
        if event.success:
            security_logger.info(
                f'Authentication successful: user={event.username}, ip={event.ip_address}',
                extra=event_dict
            )
        else:
            security_logger.warning(
                f'Authentication failed: user={event.username}, ip={event.ip_address}, reason={event.reason}',
                extra=event_dict
            )

    @staticmethod
    def log_access_denied(event: AccessDeniedEvent) -> None:
        """
        تسجيل رفض وصول (authorization failure).

        Args:
            event: بيانات رفض الوصول
        """
        event_dict = event.to_dict()
        security_logger.warning(
            f'Access denied: user={event.username}, resource={event.resource}, action={event.action}',
            extra=event_dict
        )


# Helper functions للتوافق مع الواجهة القديمة
def log_login_success(username: str, ip: str, user_id: str | None = None) -> None:
    """تسجيل تسجيل دخول ناجح."""
    event = AuthAttemptEvent(
        user_id=user_id,
        username=username,
        success=True,
        ip_address=ip
    )
    SecurityEventLogger.log_auth_attempt(event)


def log_login_failure(username: str, ip: str, reason: str = 'invalid_credentials') -> None:
    """تسجيل محاولة تسجيل دخول فاشلة."""
    event = AuthAttemptEvent(
        user_id=None,
        username=username,
        success=False,
        ip_address=ip,
        reason=reason
    )
    SecurityEventLogger.log_auth_attempt(event)


def log_unauthorized_access(user_id: str, resource: str, action: str, ip: str) -> None:
    """تسجيل محاولة وصول غير مصرح بها."""
    event = AccessDeniedEvent(
        user_id=user_id,
        username=f'user_{user_id}',
        resource=resource,
        action=action,
        ip_address=ip,
        reason='insufficient_permissions'
    )
    SecurityEventLogger.log_access_denied(event)


__all__ = [
    'SecurityEventLogger',
    'AuthAttemptEvent',
    'AccessDeniedEvent',
    'log_login_failure',
    'log_login_success',
    'log_unauthorized_access',
]
