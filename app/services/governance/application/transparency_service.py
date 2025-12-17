# app/services/governance/application/transparency_service.py
"""
Transparency Service
====================
Single Responsibility: Manage transparency and audit logging.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Protocol

from app.services.governance.domain.models import ExistentialTransparencyLog


class TransparencyRepository(Protocol):
    def save(self, log: ExistentialTransparencyLog) -> None: ...
    def query(self, event_type: str | None = None, limit: int = 100) -> list[ExistentialTransparencyLog]: ...


class TransparencyService:
    """
    Existential transparency service.

    Responsibilities:
    - Log all governance events
    - Provide audit trail
    - Enable transparency queries
    """

    def __init__(self, transparency_repository: TransparencyRepository):
        self._transparency_repo = transparency_repository

    def log_event(
        self,
        event_type: str,
        subject: str,
        details: dict[str, Any],
        reasoning: str,
        impact: dict[str, Any],
    ) -> None:
        """Log transparency event"""
        event_id = hashlib.sha256(
            f"{event_type}{subject}{datetime.utcnow()}".encode()
        ).hexdigest()[:16]

        log = ExistentialTransparencyLog(
            event_type=event_type,
            subject=subject,
            details_json=details,
            reasoning=reasoning,
            impact_json=impact,
            event_hash=event_id,
        )

        self._transparency_repo.save(log)

    def query_logs(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ExistentialTransparencyLog]:
        """Query transparency logs"""
        return self._transparency_repo.query(event_type, limit)
