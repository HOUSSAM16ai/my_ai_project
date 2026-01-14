"""
Centralized audit service package.
Provides high-precision logging for sensitive operations.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.audit import AuditLog
from app.core.domain.common import utc_now
from app.services.audit.enums import AuditAction
from app.services.audit.schemas import AuditLogEntry

logger = logging.getLogger(__name__)


class AuditService:
    """
    High-precision audit service with strict schema validation and async persistence.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        actor_user_id: int | None,
        action: str | AuditAction,
        target_type: str,
        target_id: str | None,
        metadata: Mapping[str, object],
        ip: str | None,
        user_agent: str | None,
    ) -> AuditLog:
        """
        Record an audit log entry with strict validation.

        Args:
            actor_user_id: ID of the user performing the action (or None for system).
            action: The action performed (AuditAction enum preferred).
            target_type: Domain entity type (e.g., 'user', 'policy').
            target_id: ID of the modified entity.
            metadata: Contextual data (JSON serializable).
            ip: IP address.
            user_agent: User agent string.

        Returns:
            The persisted AuditLog ORM instance.
        """
        # 1. Validate Input using Pydantic Schema (High Precision)
        try:
            # Normalize action to string if it's an Enum
            action_str = action.value if isinstance(action, AuditAction) else str(action)

            payload = AuditLogEntry(
                actor_user_id=actor_user_id,
                action=action_str,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata, # type: ignore
                ip=ip,
                user_agent=user_agent
            )
        except Exception as e:
            # Fallback for critical audit failures (Diagnosis)
            logger.error(f"Audit log validation failed: {e}. Payload: {metadata}")
            # We still want to log, maybe with a 'validation_failed' tag?
            # For now, we raise to ensure developers fix the call site,
            # or we could degrade gracefully. Let's strict fail for 'High Precision'.
            raise

        # 2. Construct Domain Entity
        # Note: We cast metadata to dict explicitly to ensure SQLAlchemy compatibility
        details_dict = dict(payload.metadata) if payload.metadata else {}

        entry = AuditLog(
            actor_user_id=payload.actor_user_id,
            action=str(payload.action),
            target_type=payload.target_type,
            target_id=payload.target_id,
            details=details_dict,
            ip=payload.ip,
            user_agent=payload.user_agent,
            created_at=utc_now(),
        )

        # 3. Persist (Async)
        try:
            self.session.add(entry)
            await self.session.commit()
            await self.session.refresh(entry)
            return entry
        except Exception as e:
            logger.error(f"Failed to persist audit log: {e}")
            await self.session.rollback()
            raise
