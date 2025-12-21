"""Security Metrics Facade - Unified interface following Facade Pattern."""

from typing import Any

from app.security_metrics.application.developer_scoring import DeveloperSecurityScorer
from app.security_metrics.application.report_generation import SecurityReportGenerator
from app.security_metrics.application.risk_scoring import RiskScoreCalculator
from app.security_metrics.domain.entities import DeveloperSecurityScore, RiskScore, SecurityFinding
from app.security_metrics.domain.interfaces import (
    ReportGenerator,
    RiskCalculator,
    SecurityRepository,
)
from app.security_metrics.domain.value_objects import Severity
from app.security_metrics.infrastructure.in_memory_repository import InMemorySecurityRepository


class SecurityMetricsFacade:
    """
    Security Metrics Facade - Unified interface for all security metrics operations.

    This class follows the Facade Pattern and Dependency Inversion Principle.
    All dependencies are injected through the constructor.
    """

    def __init__(
        self,
        repository: SecurityRepository,
        risk_calculator: RiskCalculator,
        report_generator: ReportGenerator,
        developer_scorer: DeveloperSecurityScorer,
    ):
        self.repository = repository
        self.risk_calculator = risk_calculator
        self.report_generator = report_generator
        self.developer_scorer = developer_scorer

    def add_finding(
        self,
        finding_id: str,
        severity: str,
        rule_id: str,
        file_path: str,
        line_number: int,
        message: str,
        developer_id: str | None = None,
        cwe_id: str | None = None,
        owasp_category: str | None = None,
    ) -> None:
        """Add a security finding."""
        finding = SecurityFinding(
            id=finding_id,
            severity=Severity[severity],
            rule_id=rule_id,
            file_path=file_path,
            line_number=line_number,
            message=message,
            developer_id=developer_id,
            cwe_id=cwe_id,
            owasp_category=owasp_category,
        )
        self.repository.save_finding(finding)

    def calculate_risk(self) -> RiskScore:
        """Calculate current risk score."""
        findings = self.repository.get_findings()
        return self.risk_calculator.calculate(findings)

    def get_developer_score(self, developer_id: str) -> DeveloperSecurityScore:
        """Get security score for a developer."""
        return self.developer_scorer.calculate_score(developer_id)

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive security report."""
        return self.report_generator.generate({})

    def get_findings_summary(self) -> dict[str, int]:
        """Get quick summary of findings."""
        findings = self.repository.get_findings()

        summary = {
            "total": len(findings),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "fixed": 0,
        }

        for f in findings:
            if f.severity == Severity.CRITICAL:
                summary["critical"] += 1
            elif f.severity == Severity.HIGH:
                summary["high"] += 1
            elif f.severity == Severity.MEDIUM:
                summary["medium"] += 1
            elif f.severity == Severity.LOW:
                summary["low"] += 1

            if f.fixed:
                summary["fixed"] += 1

        return summary


def get_security_metrics_facade() -> SecurityMetricsFacade:
    """
    Factory function to create SecurityMetricsFacade with default dependencies.

    This demonstrates Dependency Injection and makes testing easier.
    """
    repository = InMemorySecurityRepository()
    risk_calculator = RiskScoreCalculator()
    report_generator = SecurityReportGenerator(repository, risk_calculator)
    developer_scorer = DeveloperSecurityScorer(repository)

    return SecurityMetricsFacade(
        repository=repository,
        risk_calculator=risk_calculator,
        report_generator=report_generator,
        developer_scorer=developer_scorer,
    )


# Singleton instance for backward compatibility
_security_metrics_instance: SecurityMetricsFacade | None = None


def get_security_metrics_service() -> SecurityMetricsFacade:
    """Get singleton instance of security metrics facade."""
    global _security_metrics_instance
    if _security_metrics_instance is None:
        _security_metrics_instance = get_security_metrics_facade()
    return _security_metrics_instance
