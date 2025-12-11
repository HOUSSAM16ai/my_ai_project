# app/services/analytics/application/report_generator.py
"""
Report Generator Service
=========================
Single Responsibility: Generate analytics reports and user segmentation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol

from app.services.analytics.domain.models import UserSegment


class UserRepository(Protocol):
    """Protocol for user storage"""
    def get_all(self) -> dict[int, dict[str, Any]]: ...
    def get_active_users(self, days: int) -> set[int]: ...


class EngagementAnalyzer(Protocol):
    """Protocol for engagement metrics"""
    def get_engagement_metrics(self, **kwargs) -> dict[str, Any]: ...


class ConversionAnalyzer(Protocol):
    """Protocol for conversion metrics"""
    def get_conversion_metrics(self, **kwargs) -> dict[str, Any]: ...


class RetentionAnalyzer(Protocol):
    """Protocol for retention metrics"""
    def get_retention_metrics(self, **kwargs) -> dict[str, Any]: ...


class NPSManager(Protocol):
    """Protocol for NPS metrics"""
    def get_metrics(self) -> dict[str, Any]: ...


class ReportGenerator:
    """
    Analytics report generator.
    
    Responsibilities:
    - User segmentation
    - Export metrics summaries
    - Generate comprehensive reports
    """
    
    def __init__(
        self,
        engagement_analyzer: EngagementAnalyzer,
        conversion_analyzer: ConversionAnalyzer,
        retention_analyzer: RetentionAnalyzer,
        nps_manager: NPSManager,
        user_repository: UserRepository,
    ):
        self._engagement = engagement_analyzer
        self._conversion = conversion_analyzer
        self._retention = retention_analyzer
        self._nps = nps_manager
        self._user_repo = user_repository
    
    def segment_users(self) -> dict[str, list[int]]:
        """Segment users based on behavior"""
        users = self._user_repo.get_all()
        now = datetime.utcnow()
        
        segments = {
            UserSegment.NEW.value: [],
            UserSegment.ACTIVE.value: [],
            UserSegment.POWER.value: [],
            UserSegment.AT_RISK.value: [],
            UserSegment.CHURNED.value: [],
            UserSegment.RESURRECTED.value: [],
        }
        
        for user_id, data in users.items():
            first_seen = data.get("first_seen", now)
            last_seen = data.get("last_seen", now)
            total_events = data.get("total_events", 0)
            
            days_since_signup = (now - first_seen).days
            days_since_last_seen = (now - last_seen).days
            
            # Segment logic
            if days_since_signup <= 7:
                segments[UserSegment.NEW.value].append(user_id)
            elif days_since_last_seen > 30:
                if days_since_last_seen > 90:
                    segments[UserSegment.CHURNED.value].append(user_id)
                else:
                    segments[UserSegment.AT_RISK.value].append(user_id)
            elif total_events > 100:
                segments[UserSegment.POWER.value].append(user_id)
            elif days_since_last_seen <= 7:
                segments[UserSegment.ACTIVE.value].append(user_id)
            
            # Resurrected: came back after being churned
            if days_since_last_seen <= 7 and 30 < max(
                (now - data.get("previous_visit", now)).days, 0
            ) < 90:
                segments[UserSegment.RESURRECTED.value].append(user_id)
        
        return segments
    
    def export_metrics_summary(self) -> dict[str, Any]:
        """Generate comprehensive metrics summary"""
        engagement = self._engagement.get_engagement_metrics()
        conversion = self._conversion.get_conversion_metrics()
        retention = self._retention.get_retention_metrics()
        nps = self._nps.get_metrics()
        segments = self.segment_users()
        
        # Calculate segment sizes
        segment_counts = {k: len(v) for k, v in segments.items()}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "engagement": engagement,
            "conversion": conversion,
            "retention": retention,
            "nps": nps,
            "segments": segment_counts,
            "health_score": self._calculate_health_score(
                engagement, conversion, retention, nps
            ),
        }
    
    def _calculate_health_score(
        self,
        engagement: dict[str, Any],
        conversion: dict[str, Any],
        retention: dict[str, Any],
        nps: dict[str, Any],
    ) -> float:
        """Calculate overall product health score (0-100)"""
        # Weighted average of key metrics
        weights = {
            "engagement": 0.3,
            "conversion": 0.3,
            "retention": 0.3,
            "nps": 0.1,
        }
        
        # Normalize metrics to 0-100 scale
        engagement_score = min(engagement.get("stickiness", 0) * 100, 100)
        conversion_score = min(conversion.get("conversion_rate", 0) * 100, 100)
        retention_score = retention.get("day_7_retention", 0) * 100
        nps_score = (nps.get("nps_score", 0) + 100) / 2  # NPS is -100 to 100
        
        health_score = (
            engagement_score * weights["engagement"] +
            conversion_score * weights["conversion"] +
            retention_score * weights["retention"] +
            nps_score * weights["nps"]
        )
        
        return round(health_score, 2)
