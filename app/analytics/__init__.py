"""
Analytics Module - Clean Architecture Implementation

This module provides analytics capabilities following SOLID principles.
"""

from app.analytics.api.analytics_facade import AnalyticsFacade
from app.analytics.domain.entities import Anomaly, UsageMetric, UserJourney

__all__ = ["AnalyticsFacade", "UsageMetric", "UserJourney", "Anomaly"]
