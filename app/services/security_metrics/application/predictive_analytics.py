"""
Predictive Analytics Application Service
ML-based risk prediction and trend analysis
"""

import statistics

from ..domain.models import RiskPrediction, SecurityMetrics, TrendDirection
from ..domain.ports import PredictiveAnalyticsPort


class LinearRegressionPredictor(PredictiveAnalyticsPort):
    """
    Predictive analytics using linear regression
    Inspired by: Google's Predictive Security, AWS GuardDuty ML
    """

    def predict_future_risk(
        self, historical_metrics: list[SecurityMetrics], days_ahead: int = 30
    ) -> RiskPrediction:
        """Predict future risk using linear regression"""
        if len(historical_metrics) < 7:
            return RiskPrediction(
                predicted_risk=0.0,
                confidence=0.0,
                trend=TrendDirection.STABLE,
                slope=0.0,
                current_risk=0.0,
            )

        risk_scores = [m.overall_risk_score for m in historical_metrics[-30:]]
        n = len(risk_scores)
        x = list(range(n))
        y = risk_scores

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        slope = 0 if denominator == 0 else numerator / denominator
        intercept = y_mean - slope * x_mean

        future_x = n + days_ahead
        predicted_risk = slope * future_x + intercept
        predicted_risk = max(0, min(100, predicted_risk))

        ss_total = sum((y[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))

        r_squared = 0 if ss_total == 0 else 1 - ss_residual / ss_total
        confidence = max(0, min(100, r_squared * 100))

        trend = self._determine_trend(slope)

        return RiskPrediction(
            predicted_risk=round(predicted_risk, 2),
            confidence=round(confidence, 2),
            trend=trend,
            slope=round(slope, 4),
            current_risk=risk_scores[-1],
        )

    def _determine_trend(self, slope: float) -> TrendDirection:
        """Determine trend direction from slope"""
        if slope > 0.5:
            return TrendDirection.DEGRADING
        elif slope < -0.5:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.STABLE
