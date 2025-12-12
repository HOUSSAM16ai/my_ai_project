"""
Simple Behavioral Analyzer - Infrastructure Implementation
==========================================================
Basic behavioral analysis implementation.

محلل السلوك البسيط
"""

import uuid
from datetime import datetime

from ...domain.models import SecurityEvent, ThreatDetection, ThreatLevel, ThreatType, UserBehaviorProfile


class SimpleBehavioralAnalyzer:
    """
    محلل سلوك بسيط
    
    Simple implementation of behavioral analysis.
    """

    def analyze_behavior(
        self, event: SecurityEvent, profile: UserBehaviorProfile
    ) -> list[ThreatDetection]:
        """
        Analyze event against user profile.
        
        Args:
            event: Current security event
            profile: User's behavioral profile
            
        Returns:
            List of detected anomalies
        """
        threats = []

        # Check if endpoint is unusual
        if profile.typical_endpoints and event.endpoint not in profile.typical_endpoints:
            threats.append(
                ThreatDetection(
                    detection_id=str(uuid.uuid4()),
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    threat_level=ThreatLevel.MEDIUM,
                    description=f"Unusual endpoint access: {event.endpoint}",
                    source_ip=event.source_ip,
                    user_id=event.user_id,
                    confidence=0.70,
                    evidence=[f"User typically accesses: {', '.join(profile.typical_endpoints[:3])}"],
                    recommended_action="monitor",
                    detected_at=datetime.now(),
                )
            )

        return threats

    def update_profile(self, event: SecurityEvent, profile: UserBehaviorProfile) -> None:
        """
        Update user profile with new event.
        
        Args:
            event: New security event
            profile: Profile to update (modified in place)
        """
        # Add endpoint if not in typical list
        if event.endpoint not in profile.typical_endpoints:
            profile.typical_endpoints.append(event.endpoint)
            # Keep only recent 20 endpoints
            profile.typical_endpoints = profile.typical_endpoints[-20:]

        # Update timestamp
        profile.last_updated = datetime.now()


__all__ = ["SimpleBehavioralAnalyzer"]
