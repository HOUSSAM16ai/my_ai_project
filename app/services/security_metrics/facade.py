"""
Security Metrics Engine Facade
Unified interface for security metrics operations
"""
from .application.metrics_calculator import ComprehensiveMetricsCalculator
from .application.predictive_analytics import LinearRegressionPredictor
from .application.risk_calculator import AdvancedRiskCalculator
from .domain.models import RiskPrediction, SecurityFinding, SecurityMetrics
from .infrastructure.in_memory_repositories import (
    InMemoryFindingsRepository,
    InMemoryMetricsRepository,
)


class SecurityMetricsEngine:
    """
    Security Metrics Engine Facade
    Provides unified access to all security metrics functionality
    """

    def __init__(self, risk_calculator: (AdvancedRiskCalculator | None)=
        None, metrics_calculator: (ComprehensiveMetricsCalculator | None)=
        None, predictor: (LinearRegressionPredictor | None)=None,
        findings_repo: (InMemoryFindingsRepository | None)=None,
        metrics_repo: (InMemoryMetricsRepository | None)=None):
        self.risk_calculator = risk_calculator or AdvancedRiskCalculator()
        self.metrics_calculator = (metrics_calculator or
            ComprehensiveMetricsCalculator())
        self.predictor = predictor or LinearRegressionPredictor()
        self.findings_repo = findings_repo or InMemoryFindingsRepository()
        self.metrics_repo = metrics_repo or InMemoryMetricsRepository()
        self.findings_history: list[SecurityFinding] = []
        self.metrics_history: list[SecurityMetrics] = []

    def calculate_advanced_risk_score(self, findings: list[SecurityFinding],
        code_metrics: (dict | None)=None) ->float:
        """Calculate advanced risk score"""
        return self.risk_calculator.calculate_risk_score(findings, code_metrics
            )

    def predict_future_risk(self, historical_metrics: list[SecurityMetrics],
        days_ahead: int=30) ->RiskPrediction:
        """Predict future risk"""
        return self.predictor.predict_future_risk(historical_metrics,
            days_ahead)

    def add_finding(self, finding: SecurityFinding) ->None:
        """Add a security finding"""
        self.findings_repo.save_finding(finding)
        self.findings_history.append(finding)

    def get_findings(self, filters: (dict | None)=None) ->list[SecurityFinding
        ]:
        """Get findings with filters"""
        return self.findings_repo.get_findings(filters)

    def save_metrics(self, metrics: SecurityMetrics) ->None:
        """Save metrics"""
        self.metrics_repo.save_metrics(metrics)
        self.metrics_history.append(metrics)

    def get_historical_metrics(self, days: int=30) ->list[SecurityMetrics]:
        """Get historical metrics"""
        return self.metrics_repo.get_historical_metrics(days)


_engine_instance: SecurityMetricsEngine | None = None


def get_security_metrics_engine() ->SecurityMetricsEngine:
    """Get singleton instance of SecurityMetricsEngine"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SecurityMetricsEngine()
    return _engine_instance
