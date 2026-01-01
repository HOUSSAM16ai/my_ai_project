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
from datetime import datetime

security_logger = logging.getLogger('security')

class SecurityEventLogger:
    """
    Centralized security event logging.

    All security-related events should be logged through this class
    to maintain consistent audit trail.
    """

    @staticmethod
    # TODO: Reduce parameters (6 params) - Use config object
    def log_auth_attempt(user_id: (str | None), username: (str | None),
        success: bool, ip_address: str, user_agent: (str | None)=None,
        reason: (str | None)=None):
        """
        Log authentication attempt.

        Args:
            user_id: User ID if available
            username: Username attempted
            success: Whether authentication succeeded
            ip_address: Client IP address
            user_agent: Browser/client user agent
            reason: Failure reason if applicable
        """
        event = {'event_type': 'auth_attempt', 'user_id': user_id,
            'username': username, 'success': success, 'ip_address':
            ip_address, 'user_agent': user_agent, 'reason': reason,
            'timestamp': datetime.utcnow().isoformat()}
        if success:
            security_logger.info(
                f'Authentication successful: user={username}, ip={ip_address}',
                extra=event)
        else:
            security_logger.warning(
                f'Authentication failed: user={username}, ip={ip_address}, reason={reason}'
                , extra=event)

    # TODO: Reduce parameters (6 params) - Use config object
    @staticmethod
    def log_access_denied(user_id: str, username: str, resource: str,
        action: str, ip_address: str, reason: (str | None)=None):
        """
        Log access denial (authorization failure).

        Args:
            user_id: User ID attempting access
            username: Username
            resource: Resource being accessed
            action: Action being attempted
            ip_address: Client IP address
            reason: Denial reason
        """
        event = {'event_type': 'access_denied', 'user_id': user_id,
            'username': username, 'resource': resource, 'action': action,
            'ip_address': ip_address, 'reason': reason, 'timestamp':
            datetime.utcnow().isoformat()}
        security_logger.warning(
            f'Access denied: user={username}, resource={resource}, action={action}'
            , extra=event)

def log_login_success(username: str, ip: str, user_id: (str | None)=None):
    """Log successful login."""
    SecurityEventLogger.log_auth_attempt(user_id=user_id, username=username,
        success=True, ip_address=ip)

def log_login_failure(username: str, ip: str, reason: str='invalid_credentials'
    ) -> None:
    """Log failed login attempt."""
    SecurityEventLogger.log_auth_attempt(user_id=None, username=username,
        success=False, ip_address=ip, reason=reason)

def log_unauthorized_access(user_id: str, resource: str, action: str, ip: str) -> None:
    """Log unauthorized access attempt."""
    SecurityEventLogger.log_access_denied(user_id=user_id, username=
        f'user_{user_id}', resource=resource, action=action, ip_address=ip,
        reason='insufficient_permissions')

__all__ = ['SecurityEventLogger', 'log_login_failure', 'log_login_success',
    'log_unauthorized_access']
