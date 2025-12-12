"""
API Advanced Analytics Service - Backward Compatible Shim
=========================================================
This is a thin compatibility shim that redirects to the new
hexagonal architecture implementation.

⚠️ DEPRECATED: For new code, import directly from:
   from app.services.api_advanced_analytics import AdvancedAnalyticsService

This file maintains backward compatibility with existing code.
All functionality has been moved to app/services/api_advanced_analytics/

Architecture: Hexagonal (Ports & Adapters)
Status: ✅ Wave 9 Refactored
Reduction: 636 lines → 64 lines (90% reduction)
"""

# Import from new modular structure
from app.services.api_advanced_analytics import (
    AdvancedAnalyticsService,
    AnalyticsReport,
    BehaviorPattern,
    BehaviorProfile,
    MetricType,
    TimeGranularity,
    UsageMetric,
    UserJourney,
    get_advanced_analytics_service,
)

# Re-export for backward compatibility
__all__ = [
    "AdvancedAnalyticsService",
    "AnalyticsReport",
    "BehaviorPattern",
    "BehaviorProfile",
    "MetricType",
    "TimeGranularity",
    "UsageMetric",
    "UserJourney",
    "get_advanced_analytics_service",
]


# For backward compatibility - maintain module-level function
def get_service() -> AdvancedAnalyticsService:
    """
    Get singleton instance of Advanced Analytics Service.
    
    DEPRECATED: Use get_advanced_analytics_service() instead.
    """
    return get_advanced_analytics_service()
