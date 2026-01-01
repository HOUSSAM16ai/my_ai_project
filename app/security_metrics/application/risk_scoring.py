"""Risk scoring use case - Single Responsibility Principle."""

import typing
from datetime import datetime

from app.security_metrics.domain.entities import RiskScore, SecurityFinding
from app.security_metrics.domain.interfaces import RiskCalculator
from app.security_metrics.domain.value_objects import RiskLevel, Severity

class RiskScoreCalculator(RiskCalculator):
    """Risk score calculator - SRP: Only calculates risk scores."""

    SEVERITY_WEIGHTS: typing.ClassVar[dict[Severity, float]] = {
        Severity.CRITICAL: 10.0,
        Severity.HIGH: 7.5,
        Severity.MEDIUM: 5.0,
        Severity.LOW: 2.5,
        Severity.INFO: 1.0,
    }

    def calculate(self, findings: list[SecurityFinding]) -> RiskScore:
        """Calculate risk score - Complexity < 10."""
        if not findings:
            return RiskScore(score=0.0, level=RiskLevel.MINIMAL, breakdown={}, timestamp=datetime.now())

        base_score = self._calculate_base_score(findings)
        exposure_factor = self._calculate_exposure_factor(findings)
        velocity_factor = self._calculate_velocity_factor(findings)

        final_score = min(100.0, base_score * exposure_factor * velocity_factor)

        return RiskScore(
            score=round(final_score, 2),
            level=self._get_risk_level(final_score),
            breakdown={"base": base_score, "exposure": exposure_factor, "velocity": velocity_factor},
            timestamp=datetime.now(),
        )

    def _calculate_base_score(self, findings: list[SecurityFinding]) -> float:
        """Calculate base score - Complexity < 10."""
        total_weight = sum(
            self.SEVERITY_WEIGHTS[finding.severity] for finding in findings if not finding.false_positive
        )
        return min(100.0, total_weight)

    def _calculate_exposure_factor(self, findings: list[SecurityFinding]) -> float:
        """Calculate exposure factor - Complexity < 10."""
        if not findings:
            return 1.0

        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        if critical_count > 0:
            return 1.2

        return 1.0

    def _calculate_velocity_factor(self, findings: list[SecurityFinding]) -> float:
        """Calculate velocity factor - Complexity < 10."""
        if not findings:
            return 1.0

        unfixed_count = sum(1 for f in findings if not f.fixed)
        if unfixed_count > 10:
            return 1.1

        return 1.0

    def _get_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level - Complexity < 10."""
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 60:
            return RiskLevel.HIGH
        if score >= 40:
            return RiskLevel.MEDIUM
        if score >= 20:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL
