"""Security report generation use case - Single Responsibility Principle."""

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.security_metrics.domain.entities import RiskScore, SecurityFinding
from app.security_metrics.domain.interfaces import ReportGenerator, RiskCalculator, SecurityRepository
from app.security_metrics.domain.value_objects import RiskLevel, Severity


class SecurityReportGenerator(ReportGenerator):
    """Security report generator - SRP: Only generates security reports."""

    def __init__(self, repository: SecurityRepository, risk_calculator: RiskCalculator):
        self.repository = repository
        self.risk_calculator = risk_calculator

    def generate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate comprehensive security report - Complexity < 10."""
        findings = self.repository.get_findings()
        risk_score = self.risk_calculator.calculate(findings)

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(findings),
            "risk_assessment": self._format_risk_score(risk_score),
            "findings_breakdown": self._breakdown_findings(findings),
            "recommendations": self._generate_recommendations(risk_score, findings),
        }

    def _generate_summary(self, findings: list[SecurityFinding]) -> dict[str, Any]:
        """Generate summary statistics - Complexity < 10."""
        summary = {"total_findings": len(findings), "critical": 0, "high": 0, "medium": 0, "low": 0, "fixed": 0, "unfixed": 0}

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
            else:
                summary["unfixed"] += 1

        return summary

    def _format_risk_score(self, risk_score: RiskScore) -> dict[str, Any]:
        """Format risk score for report."""
        return {"score": risk_score.score, "level": risk_score.level.value, "breakdown": risk_score.breakdown}

    def _breakdown_findings(self, findings: list[SecurityFinding]) -> dict[str, list[dict]]:
        """Break down findings by severity - Complexity < 10."""
        by_severity: dict[str, list[dict]] = defaultdict(list)

        for finding in findings:
            by_severity[finding.severity.value].append(
                {
                    "id": finding.id,
                    "rule_id": finding.rule_id,
                    "file_path": finding.file_path,
                    "line_number": finding.line_number,
                    "message": finding.message,
                    "fixed": finding.fixed,
                }
            )

        return dict(by_severity)

    def _generate_recommendations(self, risk_score: RiskScore, findings: list[SecurityFinding]) -> list[str]:
        """Generate recommendations - Complexity < 10."""
        recommendations = []

        if risk_score.level == RiskLevel.CRITICAL:
            recommendations.append("⚠️ Immediate action required: Critical security issues detected")

        critical_count = self._count_unfixed_by_severity(findings, Severity.CRITICAL)
        if critical_count > 0:
            recommendations.append(f"🔴 Fix {critical_count} critical findings immediately")

        high_count = self._count_unfixed_by_severity(findings, Severity.HIGH)
        if high_count > 0:
            recommendations.append(f"🟠 Address {high_count} high severity findings")

        unfixed_count = sum(1 for f in findings if not f.fixed)
        if unfixed_count > 20:
            recommendations.append(f"📊 {unfixed_count} total unfixed findings - prioritize remediation")

        return recommendations

    def _count_unfixed_by_severity(self, findings: list[SecurityFinding], severity: Severity) -> int:
        """Count unfixed findings by severity."""
        return sum(1 for f in findings if f.severity == severity and not f.fixed)
