"""
AI Security Domain Ports (Interfaces)
=====================================
Abstractions for infrastructure implementations.

واجهات المجال الأمني - تجريدات للتطبيقات البنيوية
"""

from typing import Protocol

from .models import SecurityEvent, ThreatDetection, UserBehaviorProfile


class ThreatDetectorPort(Protocol):
    """
    كاشف التهديدات - Threat detection interface

    Defines the contract for threat detection implementations.
    """

    def detect_threats(self, event: SecurityEvent) -> list[ThreatDetection]:
        """
        Detect security threats in an event.

        Args:
            event: Security event to analyze

        Returns:
            List of detected threats (empty if none)
        """
        ...

    def analyze_payload(self, payload: dict) -> list[str]:
        """
        Analyze payload for malicious patterns.

        Args:
            payload: Request payload to analyze

        Returns:
            List of detected patterns/issues
        """
        ...

class BehavioralAnalyzerPort(Protocol):
    """
    محلل السلوك - Behavioral analysis interface

    Defines the contract for user behavior analysis.
    """

    def analyze_behavior(
        self, event: SecurityEvent, profile: UserBehaviorProfile
    ) -> list[ThreatDetection]:
        """
        Analyze event against user's normal behavior.

        Args:
            event: Current security event
            profile: User's behavioral profile

        Returns:
            List of behavioral anomalies detected
        """
        ...

    def update_profile(self, event: SecurityEvent, profile: UserBehaviorProfile) -> None:
        """
        Update user profile with new event data.

        Args:
            event: New security event
            profile: Profile to update (modified in place)
        """
        ...

class ResponseSystemPort(Protocol):
    """
    نظام الاستجابة - Automated response interface

    Defines the contract for automated threat response.
    """

    def execute_response(self, detection: ThreatDetection) -> dict:
        """
        Execute automated response to a threat.

        Args:
            detection: Detected threat to respond to

        Returns:
            Response action details
        """
        ...

    def should_auto_block(self, detection: ThreatDetection) -> bool:
        """
        Determine if threat should be automatically blocked.

        Args:
            detection: Detected threat

        Returns:
            True if should auto-block
        """
        ...

class ProfileRepositoryPort(Protocol):
    """
    مستودع الملفات الشخصية - User profile storage interface
    """

    def get_profile(self, user_id: str) -> UserBehaviorProfile | None:
        """Get user behavioral profile"""
        ...

    def save_profile(self, profile: UserBehaviorProfile) -> None:
        """Save user behavioral profile"""
        ...

class ThreatLoggerPort(Protocol):
    """
    مسجل التهديدات - Threat logging interface
    """

    def log_threat(self, detection: ThreatDetection) -> None:
        """Log a detected threat"""
        ...

    def get_recent_threats(self, limit: int = 100) -> list[ThreatDetection]:
        """Get recently detected threats"""
        ...

__all__ = [
    "BehavioralAnalyzerPort",
    "ProfileRepositoryPort",
    "ResponseSystemPort",
    "ThreatDetectorPort",
    "ThreatLoggerPort",
]
