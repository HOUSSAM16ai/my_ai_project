"""Domain interfaces - Contracts for implementations."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from app.security_metrics.domain.entities import RiskScore, SecurityFinding, SecurityMetrics

class SecurityRepository(Protocol):
    """Repository for storing and retrieving security data."""

    def save_finding(self, finding: SecurityFinding) -> None:
        """Save a security finding."""
        ...

    def get_findings(self) -> list[SecurityFinding]:
        """Get all security findings."""
        ...

    def get_findings_by_developer(self, developer_id: str) -> list[SecurityFinding]:
        """Get findings for a specific developer."""
        ...

    def save_metrics(self, metrics: SecurityMetrics) -> None:
        """Save security metrics."""
        ...

    def get_metrics_history(self, days: int) -> list[SecurityMetrics]:
        """Get metrics history for the last N days."""
        ...

class RiskCalculator(ABC):
    """Interface for risk calculation - Open/Closed Principle."""

    @abstractmethod
    def calculate(self, findings: list[SecurityFinding]) -> RiskScore:
        """Calculate risk score from findings."""
        pass

class ReportGenerator(ABC):
    """Interface for report generation - Open/Closed Principle."""

    @abstractmethod
    def generate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate a security report."""
        pass
