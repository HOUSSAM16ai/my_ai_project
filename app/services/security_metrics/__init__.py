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
from .application.predictive_analytics import PredictiveAnalytics
from .application.risk_calculator import RiskCalculator
from .domain.models import (
    RiskPrediction,
    SecurityFinding,
    SecurityMetrics,
    Severity,
    TrendDirection,
)

# Backward compatibility alias
MetricsCalculator = ComprehensiveMetricsCalculator

__all__ = [
    # Application Services (Direct Access - KISS)
    "ComprehensiveMetricsCalculator",
    "MetricsCalculator",  # Backward compatibility
    "PredictiveAnalytics",
    "RiskCalculator",
    # Domain Models
    "RiskPrediction",
    "SecurityFinding",
    "SecurityMetrics",
    "Severity",
    "TrendDirection",
]
