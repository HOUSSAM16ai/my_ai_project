"""
Security Metrics Package - SOLID Principles Applied
==================================================
Simplified architecture using KISS principle - direct access to application services.

Usage:
    from app.services.security_metrics import ComprehensiveMetricsCalculator

    calculator = ComprehensiveMetricsCalculator()
    metrics = calculator.calculate_metrics(findings)
"""

from .application.metrics_calculator import ComprehensiveMetricsCalculator
from .application.predictive_analytics import LinearRegressionPredictor
from .application.risk_calculator import AdvancedRiskCalculator
from .domain.models import (
    RiskPrediction,
    SecurityFinding,
    SecurityMetrics,
    Severity,
    TrendDirection,
)

# Backward compatibility aliases
MetricsCalculator = ComprehensiveMetricsCalculator
PredictiveAnalytics = LinearRegressionPredictor
RiskCalculator = AdvancedRiskCalculator

__all__ = [
    "AdvancedRiskCalculator",
    # Application Services (Direct Access - KISS)
    "ComprehensiveMetricsCalculator",
    "LinearRegressionPredictor",
    "MetricsCalculator",  # Backward compatibility
    "PredictiveAnalytics",  # Backward compatibility
    "RiskCalculator",  # Backward compatibility
    # Domain Models
    "RiskPrediction",
    "SecurityFinding",
    "SecurityMetrics",
    "Severity",
    "TrendDirection",
]
