"""
Security Metrics Package - SOLID Principles Applied
==================================================
Simplified architecture using KISS principle - direct access to application services.

Usage:
    from app.services.security_metrics import MetricsCalculator

    calculator = MetricsCalculator(findings_repo)
    metrics = calculator.calculate_metrics(service_id)
"""

from .application.metrics_calculator import MetricsCalculator
from .application.predictive_analytics import PredictiveAnalytics
from .application.risk_calculator import RiskCalculator
from .domain.models import (
    RiskPrediction,
    SecurityFinding,
    SecurityMetrics,
    Severity,
    TrendDirection,
)

__all__ = [
    # Application Services (Direct Access - KISS)
    "MetricsCalculator",
    "PredictiveAnalytics",
    "RiskCalculator",
    # Domain Models
    "RiskPrediction",
    "SecurityFinding",
    "SecurityMetrics",
    "Severity",
    "TrendDirection",
]
