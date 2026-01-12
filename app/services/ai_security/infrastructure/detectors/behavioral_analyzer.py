"""
Simple Behavioral Analyzer - Infrastructure Implementation
==========================================================
Basic behavioral analysis implementation.

محلل السلوك البسيط
"""

import uuid
from datetime import datetime

from app.services.ai_security.domain.models import (
    SecurityEvent,
    ThreatDetection,
    ThreatLevel,
    ThreatType,
    UserBehaviorProfile,
)


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
        تحليل الحدث مقابل ملف المستخدم

        Args:
            event: Current security event | الحدث الأمني الحالي
            profile: User's behavioral profile | ملف السلوك للمستخدم

        Returns:
            List of detected anomalies | قائمة الشذوذات المكتشفة
        """
        threats = []

        # Check if endpoint is unusual
        if self._is_unusual_endpoint(event, profile):
            threat = self._create_unusual_endpoint_threat(event, profile)
            threats.append(threat)

        return threats

    def _is_unusual_endpoint(self, event: SecurityEvent, profile: UserBehaviorProfile) -> bool:
        """
        تحقق إذا كان نقطة النهاية غير معتادة | Check if endpoint is unusual

        Args:
            event: الحدث الأمني | Security event
            profile: ملف المستخدم | User profile

        Returns:
            True إذا كان غير معتاد | True if unusual
        """
        return profile.typical_endpoints and event.endpoint not in profile.typical_endpoints

    def _create_unusual_endpoint_threat(
        self, event: SecurityEvent, profile: UserBehaviorProfile
    ) -> ThreatDetection:
        """
        إنشاء كشف تهديد لنقطة نهاية غير معتادة
        Create threat detection for unusual endpoint

        Args:
            event: الحدث الأمني | Security event
            profile: ملف المستخدم | User profile

        Returns:
            كشف التهديد | Threat detection
        """
        typical_endpoints_sample = ", ".join(profile.typical_endpoints[:3])

        return ThreatDetection(
            detection_id=str(uuid.uuid4()),
            threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
            threat_level=ThreatLevel.MEDIUM,
            description=f"Unusual endpoint access: {event.endpoint}",
            source_ip=event.source_ip,
            user_id=event.user_id,
            confidence=0.70,
            evidence=[f"User typically accesses: {typical_endpoints_sample}"],
            recommended_action="monitor",
            detected_at=datetime.now(),
        )

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
