# app/middleware/security_logger.py
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
from typing import Any

# Dedicated security logger (separate from application logs)
security_logger = logging.getLogger("security")


class SecurityEventLogger:
    """
    Centralized security event logging.

    All security-related events should be logged through this class
    to maintain consistent audit trail.
    """

    @staticmethod
    def log_auth_attempt(
        user_id: str | None,
        username: str | None,
        success: bool,
        ip_address: str,
        user_agent: str | None = None,
        reason: str | None = None,
    ):
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
        event = {
            "event_type": "auth_attempt",
            "user_id": user_id,
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if success:
            security_logger.info(
                f"Authentication successful: user={username}, ip={ip_address}",
                extra=event,
            )
        else:
            security_logger.warning(
                f"Authentication failed: user={username}, ip={ip_address}, reason={reason}",
                extra=event,
            )

    @staticmethod
    def log_access_denied(
        user_id: str,
        username: str,
        resource: str,
        action: str,
        ip_address: str,
        reason: str | None = None,
    ):
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
        event = {
            "event_type": "access_denied",
            "user_id": user_id,
            "username": username,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.warning(
            f"Access denied: user={username}, resource={resource}, action={action}",
            extra=event,
        )

    @staticmethod
    def log_suspicious_activity(
        description: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Log suspicious activity for security analysis.

        Args:
            description: Description of suspicious activity
            user_id: User ID if known
            ip_address: Client IP if known
            details: Additional details
        """
        event = {
            "event_type": "suspicious_activity",
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.error(
            f"Suspicious activity detected: {description}",
            extra=event,
        )

    @staticmethod
    def log_password_change(
        user_id: str,
        username: str,
        ip_address: str,
        initiated_by: str,
    ):
        """
        Log password change event.

        Args:
            user_id: User whose password changed
            username: Username
            ip_address: Client IP
            initiated_by: Who initiated (user/admin)
        """
        event = {
            "event_type": "password_change",
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "initiated_by": initiated_by,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.info(
            f"Password changed: user={username}, by={initiated_by}",
            extra=event,
        )

    @staticmethod
    def log_permission_change(
        target_user_id: str,
        target_username: str,
        admin_user_id: str,
        admin_username: str,
        changes: dict[str, Any],
        ip_address: str,
    ):
        """
        Log permission/role change.

        Args:
            target_user_id: User whose permissions changed
            target_username: Target username
            admin_user_id: Admin making the change
            admin_username: Admin username
            changes: Dictionary of changes
            ip_address: Admin's IP
        """
        event = {
            "event_type": "permission_change",
            "target_user_id": target_user_id,
            "target_username": target_username,
            "admin_user_id": admin_user_id,
            "admin_username": admin_username,
            "changes": changes,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.warning(
            f"Permissions changed: target={target_username}, admin={admin_username}",
            extra=event,
        )

    @staticmethod
    def log_data_access(
        user_id: str,
        username: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str,
    ):
        """
        Log sensitive data access.

        Args:
            user_id: User accessing data
            username: Username
            resource_type: Type of resource (e.g., "mission", "user_data")
            resource_id: Specific resource ID
            action: Action performed (read/update/delete)
            ip_address: Client IP
        """
        event = {
            "event_type": "data_access",
            "user_id": user_id,
            "username": username,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.info(
            f"Data access: user={username}, resource={resource_type}/{resource_id}, action={action}",
            extra=event,
        )

    @staticmethod
    def log_rate_limit_exceeded(
        client_id: str,
        endpoint: str,
        ip_address: str,
    ):
        """
        Log rate limit violation.

        Args:
            client_id: Client identifier
            endpoint: Endpoint being accessed
            ip_address: Client IP
        """
        event = {
            "event_type": "rate_limit_exceeded",
            "client_id": client_id,
            "endpoint": endpoint,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.warning(
            f"Rate limit exceeded: client={client_id}, endpoint={endpoint}",
            extra=event,
        )


# Convenience functions for common security events
def log_login_success(username: str, ip: str, user_id: str | None = None):
    """Log successful login."""
    SecurityEventLogger.log_auth_attempt(
        user_id=user_id,
        username=username,
        success=True,
        ip_address=ip,
    )


def log_login_failure(username: str, ip: str, reason: str = "invalid_credentials"):
    """Log failed login attempt."""
    SecurityEventLogger.log_auth_attempt(
        user_id=None,
        username=username,
        success=False,
        ip_address=ip,
        reason=reason,
    )


def log_unauthorized_access(user_id: str, resource: str, action: str, ip: str):
    """Log unauthorized access attempt."""
    SecurityEventLogger.log_access_denied(
        user_id=user_id,
        username=f"user_{user_id}",
        resource=resource,
        action=action,
        ip_address=ip,
        reason="insufficient_permissions",
    )


__all__ = [
    "SecurityEventLogger",
    "log_login_failure",
    "log_login_success",
    "log_unauthorized_access",
]
