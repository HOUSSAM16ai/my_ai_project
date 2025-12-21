"""
Risk Calculator Application Service
Implements advanced risk scoring algorithms
"""

from datetime import datetime

from ..domain.models import SecurityFinding
from ..domain.ports import RiskCalculatorPort


class AdvancedRiskCalculator(RiskCalculatorPort):
    """
    Advanced risk calculator using FAANG-style algorithms
    Inspired by: Google's Risk Score, Meta's Security Score
    """

    def __init__(self):
        self.severity_weights = {
            "CRITICAL": 10.0,
            "HIGH": 7.5,
            "MEDIUM": 5.0,
            "LOW": 2.5,
            "INFO": 1.0,
        }

        self.cwe_risk_multipliers = {
            "CWE-89": 2.0,  # SQL Injection
            "CWE-79": 1.8,  # XSS
            "CWE-798": 2.5,  # Hard-coded credentials
            "CWE-327": 1.5,  # Broken crypto
            "CWE-22": 1.7,  # Path traversal
        }

    def calculate_risk_score(
        self, findings: list[SecurityFinding], code_metrics: dict | None = None
    ) -> float:
        """
        Calculate advanced risk score
        Formula: Risk = Σ(Severity × Age × Exposure × CWE_multiplier) / Normalization
        """
        if not findings:
            return 0.0

        code_metrics = code_metrics or {}
        public_endpoints = code_metrics.get("public_endpoints", 10)

        total_risk = 0.0

        for finding in findings:
            if finding.fixed or finding.false_positive:
                continue

            severity_score = self.severity_weights.get(finding.severity.value, 1.0)
            age_factor = self._calculate_age_factor(finding.first_seen)
            exposure_factor = self.calculate_exposure_factor(finding.file_path, public_endpoints)
            cwe_multiplier = self.cwe_risk_multipliers.get(finding.cwe_id, 1.0)

            finding_risk = severity_score * age_factor * exposure_factor * cwe_multiplier
            total_risk += finding_risk

        normalization_factor = len(findings) * 10.0
        risk_score = (total_risk / normalization_factor) * 100
        risk_score = min(risk_score, 100.0)

        return round(risk_score, 2)

    def calculate_exposure_factor(self, file_path: str, public_endpoints: int) -> float:
        """Calculate file exposure factor"""
        exposure = 1.0

        high_exposure_patterns = [
            "api/",
            "routes/",
            "views/",
            "controllers/",
            "auth/",
            "login",
            "admin/",
        ]

        for pattern in high_exposure_patterns:
            if pattern in file_path.lower():
                exposure *= 1.5

        low_exposure_patterns = ["test_", "tests/", "migrations/", "scripts/"]

        for pattern in low_exposure_patterns:
            if pattern in file_path.lower():
                exposure *= 0.5

        return min(exposure, 3.0)

    def _calculate_age_factor(self, first_seen: datetime) -> float:
        """Calculate age factor (older findings = higher risk)"""
        age_days = (datetime.now() - first_seen).days
        age_factor = 1 + (age_days / 30.0)
        return min(age_factor, 5.0)
