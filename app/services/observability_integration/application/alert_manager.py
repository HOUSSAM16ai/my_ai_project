"""
Alert Manager - Application Service
"""

import uuid
from datetime import UTC, datetime

from ..domain.models import Alert, AlertSeverity
from ..domain.ports import IAlertRepository


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self, repository: IAlertRepository):
        self._repository = repository

    def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        source: str,
        metadata: dict | None = None,
    ) -> Alert:
        """Trigger a new alert"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            name=name,
            severity=severity,
            message=message,
            source=source,
            metadata=metadata or {},
            triggered_at=datetime.now(UTC),
        )
        self._repository.store_alert(alert)
        return alert

    def resolve_alert(self, alert_id: str) -> None:
        """Resolve an alert"""
        self._repository.resolve_alert(alert_id)

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = self._repository.get_active_alerts()
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_critical_alerts(self) -> list[Alert]:
        """Get critical alerts"""
        return self.get_active_alerts(severity=AlertSeverity.CRITICAL)
