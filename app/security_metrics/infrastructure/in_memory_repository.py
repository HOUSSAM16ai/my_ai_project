"""In-memory security repository - Dependency Inversion Principle."""

import threading
from datetime import datetime, timedelta

from app.security_metrics.domain.entities import SecurityFinding, SecurityMetrics


class InMemorySecurityRepository:
    """In-memory security repository - DIP: Implements domain interface."""

    def __init__(self):
        self._findings: list[SecurityFinding] = []
        self._metrics: list[SecurityMetrics] = []
        self._lock = threading.Lock()

    def save_finding(self, finding: SecurityFinding) -> None:
        """Save a security finding."""
        with self._lock:
            self._findings.append(finding)

    def get_findings(self) -> list[SecurityFinding]:
        """Get all security findings."""
        with self._lock:
            return list(self._findings)

    def get_findings_by_developer(self, developer_id: str) -> list[SecurityFinding]:
        """Get findings for a specific developer."""
        with self._lock:
            return [f for f in self._findings if f.developer_id == developer_id]

    def save_metrics(self, metrics: SecurityMetrics) -> None:
        """Save security metrics."""
        with self._lock:
            self._metrics.append(metrics)

    def get_metrics_history(self, days: int) -> list[SecurityMetrics]:
        """Get metrics history for the last N days."""
        with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            return [m for m in self._metrics if m.timestamp > cutoff]

    def clear(self) -> None:
        """Clear all data."""
        with self._lock:
            self._findings.clear()
            self._metrics.clear()

    def count_findings(self) -> int:
        """Get total count of findings."""
        with self._lock:
            return len(self._findings)
