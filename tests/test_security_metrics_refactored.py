"""Tests for refactored security metrics module - Verifying SOLID principles."""

from datetime import datetime

import pytest

from app.security_metrics.api.security_metrics_facade import get_security_metrics_facade
from app.security_metrics.application.developer_scoring import DeveloperSecurityScorer
from app.security_metrics.application.report_generation import SecurityReportGenerator
from app.security_metrics.application.risk_scoring import RiskScoreCalculator
from app.security_metrics.domain.entities import SecurityFinding
from app.security_metrics.domain.value_objects import RiskLevel, Severity
from app.security_metrics.infrastructure.in_memory_repository import InMemorySecurityRepository


class TestInMemoryRepository:
    """Test repository implementation."""

    def test_save_and_retrieve_finding(self):
        """Test saving and retrieving findings."""
        repo = InMemorySecurityRepository()
        finding = SecurityFinding(
            id="F001",
            severity=Severity.HIGH,
            rule_id="R001",
            file_path="/app/test.py",
            line_number=10,
            message="SQL Injection vulnerability",
            developer_id="dev1",
        )

        repo.save_finding(finding)
        assert repo.count_findings() == 1

        findings = repo.get_findings()
        assert len(findings) == 1
        assert findings[0].id == "F001"

    def test_get_findings_by_developer(self):
        """Test filtering findings by developer."""
        repo = InMemorySecurityRepository()

        for i in range(5):
            repo.save_finding(
                SecurityFinding(
                    id=f"F{i}",
                    severity=Severity.MEDIUM,
                    rule_id="R001",
                    file_path="/app/test.py",
                    line_number=i,
                    message="Test",
                    developer_id=f"dev{i % 2}",
                )
            )

        dev0_findings = repo.get_findings_by_developer("dev0")
        assert len(dev0_findings) == 3


class TestRiskScoring:
    """Test risk scoring - SRP verification."""

    def test_calculate_risk_empty_findings(self):
        """Test risk calculation with no findings."""
        calculator = RiskScoreCalculator()
        risk = calculator.calculate([])

        assert risk.score == 0.0
        assert risk.level == RiskLevel.MINIMAL

    def test_calculate_risk_critical_findings(self):
        """Test risk calculation with critical findings."""
        calculator = RiskScoreCalculator()
        findings = [
            SecurityFinding(
                id=f"F{i}",
                severity=Severity.CRITICAL,
                rule_id="R001",
                file_path="/app/test.py",
                line_number=i,
                message="Critical issue",
            )
            for i in range(5)
        ]

        risk = calculator.calculate(findings)
        assert risk.score > 0
        assert risk.level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_risk_level_thresholds(self):
        """Test risk level determination."""
        calculator = RiskScoreCalculator()

        assert calculator._get_risk_level(90) == RiskLevel.CRITICAL
        assert calculator._get_risk_level(70) == RiskLevel.HIGH
        assert calculator._get_risk_level(50) == RiskLevel.MEDIUM
        assert calculator._get_risk_level(30) == RiskLevel.LOW
        assert calculator._get_risk_level(10) == RiskLevel.MINIMAL


class TestDeveloperScoring:
    """Test developer scoring - SRP verification."""

    def test_score_developer_no_findings(self):
        """Test scoring developer with no findings."""
        repo = InMemorySecurityRepository()
        scorer = DeveloperSecurityScorer(repo)

        score = scorer.calculate_score("dev1")
        assert score.developer_id == "dev1"
        assert score.score == 100.0
        assert score.findings_count == 0

    def test_score_developer_with_findings(self):
        """Test scoring developer with findings."""
        repo = InMemorySecurityRepository()

        for i in range(10):
            repo.save_finding(
                SecurityFinding(
                    id=f"F{i}",
                    severity=Severity.MEDIUM,
                    rule_id="R001",
                    file_path="/app/test.py",
                    line_number=i,
                    message="Test",
                    developer_id="dev1",
                    fixed=(i < 5),
                    fix_time_hours=2.0 if i < 5 else None,
                )
            )

        scorer = DeveloperSecurityScorer(repo)
        score = scorer.calculate_score("dev1")

        assert score.developer_id == "dev1"
        assert score.findings_count == 10
        assert score.fix_rate == 50.0
        assert score.score < 100.0


class TestReportGeneration:
    """Test report generation - SRP verification."""

    def test_generate_empty_report(self):
        """Test generating report with no findings."""
        repo = InMemorySecurityRepository()
        calculator = RiskScoreCalculator()
        generator = SecurityReportGenerator(repo, calculator)

        report = generator.generate({})

        assert "timestamp" in report
        assert "summary" in report
        assert report["summary"]["total_findings"] == 0

    def test_generate_report_with_findings(self):
        """Test generating report with findings."""
        repo = InMemorySecurityRepository()

        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM]:
            repo.save_finding(
                SecurityFinding(
                    id=f"F-{severity.value}",
                    severity=severity,
                    rule_id="R001",
                    file_path="/app/test.py",
                    line_number=1,
                    message=f"{severity.value} issue",
                )
            )

        calculator = RiskScoreCalculator()
        generator = SecurityReportGenerator(repo, calculator)
        report = generator.generate({})

        assert report["summary"]["total_findings"] == 3
        assert report["summary"]["critical"] == 1
        assert report["summary"]["high"] == 1
        assert report["summary"]["medium"] == 1
        assert "risk_assessment" in report
        assert "recommendations" in report


class TestSecurityMetricsFacade:
    """Test facade - Integration test."""

    def test_full_workflow(self):
        """Test complete security metrics workflow."""
        facade = get_security_metrics_facade()

        facade.add_finding(
            finding_id="F001",
            severity="CRITICAL",
            rule_id="R001",
            file_path="/app/test.py",
            line_number=10,
            message="SQL Injection",
            developer_id="dev1",
        )

        summary = facade.get_findings_summary()
        assert summary["total"] == 1
        assert summary["critical"] == 1

        risk = facade.calculate_risk()
        assert risk.score > 0

        dev_score = facade.get_developer_score("dev1")
        assert dev_score.developer_id == "dev1"
        assert dev_score.findings_count == 1

        report = facade.generate_report()
        assert report["summary"]["total_findings"] == 1

    def test_dependency_injection(self):
        """Test that dependencies can be injected - DIP verification."""
        repo = InMemorySecurityRepository()
        calculator = RiskScoreCalculator()
        generator = SecurityReportGenerator(repo, calculator)
        scorer = DeveloperSecurityScorer(repo)

        from app.security_metrics.api.security_metrics_facade import SecurityMetricsFacade

        facade = SecurityMetricsFacade(
            repository=repo, risk_calculator=calculator, report_generator=generator, developer_scorer=scorer
        )

        assert facade.repository is repo
        assert facade.risk_calculator is calculator


class TestComplexityReduction:
    """Verify complexity reduction goals."""

    def test_no_function_exceeds_complexity_10(self):
        """Verify no function has complexity > 10."""
        import subprocess

        result = subprocess.run(
            ["radon", "cc", "app/security_metrics/", "-n", "C", "-s"], capture_output=True, text=True, check=False
        )

        high_complexity_functions = [line for line in result.stdout.split("\n") if "- C" in line or "- D" in line]

        assert len(high_complexity_functions) == 0, f"Found high complexity functions: {high_complexity_functions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
