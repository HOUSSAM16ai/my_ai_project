"""
Security Manager - Application Service
======================================
Orchestrates threat detection, analysis, and response.

مدير الأمان - خدمة التطبيق الرئيسية
"""

from typing import Optional

from ..domain.models import SecurityEvent, ThreatDetection
from ..domain.ports import (
    BehavioralAnalyzerPort,
    ProfileRepositoryPort,
    ResponseSystemPort,
    ThreatDetectorPort,
    ThreatLoggerPort,
)

class SecurityManager:
    """
    مدير الأمان الرئيسي - Main security orchestrator

    Coordinates threat detection, behavioral analysis, and automated response.
    """

    # TODO: Reduce parameters (6 params) - Use config object
    def __init__(
        self,
        threat_detector: ThreatDetectorPort,
        behavioral_analyzer: BehavioralAnalyzerPort,
        response_system: ResponseSystemPort,
        profile_repo: ProfileRepositoryPort,
        threat_logger: ThreatLoggerPort,
    ):
        """
        Initialize security manager with dependencies.

        Args:
            threat_detector: Threat detection implementation
            behavioral_analyzer: Behavioral analysis implementation
            response_system: Automated response implementation
            profile_repo: User profile storage
            threat_logger: Threat logging implementation
        """
        self.threat_detector = threat_detector
        self.behavioral_analyzer = behavioral_analyzer
        self.response_system = response_system
        self.profile_repo = profile_repo
        self.threat_logger = threat_logger

    # TODO: Split this function (44 lines) - KISS principle
    def analyze_event(self, event: SecurityEvent) -> list[ThreatDetection]:
        """
        Analyze security event for threats.

        Performs:
        1. Pattern-based threat detection
        2. Behavioral anomaly detection
        3. Automated response if needed
        4. Threat logging

        Args:
            event: Security event to analyze

        Returns:
            List of detected threats
        """
        all_threats: list[ThreatDetection] = []

        # Step 1: Pattern-based threat detection
        pattern_threats = self.threat_detector.detect_threats(event)
        all_threats.extend(pattern_threats)

        # Step 2: Behavioral analysis (if user identified)
        if event.user_id:
            profile = self.profile_repo.get_profile(event.user_id)
            if profile:
                behavioral_threats = self.behavioral_analyzer.analyze_behavior(
                    event, profile
                )
                all_threats.extend(behavioral_threats)

                # Update profile with new data
                self.behavioral_analyzer.update_profile(event, profile)
                self.profile_repo.save_profile(profile)

        # Step 3: Execute automated response for critical threats
        for threat in all_threats:
            if self.response_system.should_auto_block(threat):
                self.response_system.execute_response(threat)
                threat.auto_blocked = True

            # Log all threats
            self.threat_logger.log_threat(threat)

        return all_threats

    def get_recent_threats(self, limit: int = 100) -> list[ThreatDetection]:
        """
        Get recently detected threats.

        Args:
            limit: Maximum number of threats to return

        Returns:
            List of recent threat detections
        """
        return self.threat_logger.get_recent_threats(limit)

    def get_user_profile(self, user_id: str) -> Optional:
        """
        Get user behavioral profile.

        Args:
            user_id: User identifier

        Returns:
            User profile or None if not found
        """
        return self.profile_repo.get_profile(user_id)

__all__ = ["SecurityManager"]
