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

    def analyze_event(self, event: SecurityEvent) -> list[ThreatDetection]:
        """
        تحليل حدث الأمان للكشف عن التهديدات.
        Analyze security event for threats.

        Performs:
        1. Pattern-based threat detection | كشف التهديدات بناءً على الأنماط
        2. Behavioral anomaly detection | كشف الشذوذ السلوكي
        3. Automated response if needed | استجابة تلقائية عند الحاجة
        4. Threat logging | تسجيل التهديدات

        Args:
            event: حدث الأمان للتحليل | Security event to analyze

        Returns:
            list[ThreatDetection]: قائمة التهديدات المكتشفة | List of detected threats
        """
        all_threats: list[ThreatDetection] = []

        self._detect_pattern_threats(event, all_threats)
        self._analyze_user_behavior(event, all_threats)
        self._process_threats_response(all_threats)

        return all_threats

    def _detect_pattern_threats(self, event: SecurityEvent, all_threats: list) -> None:
        """
        كشف التهديدات بناءً على الأنماط.
        Detect pattern-based threats.
        
        Args:
            event: حدث الأمان | Security event
            all_threats: قائمة التهديدات للتحديث | Threats list to update
        """
        pattern_threats = self.threat_detector.detect_threats(event)
        all_threats.extend(pattern_threats)

    def _analyze_user_behavior(self, event: SecurityEvent, all_threats: list) -> None:
        """
        تحليل سلوك المستخدم.
        Analyze user behavior.
        
        Args:
            event: حدث الأمان | Security event
            all_threats: قائمة التهديدات للتحديث | Threats list to update
        """
        if not event.user_id:
            return
            
        profile = self.profile_repo.get_profile(event.user_id)
        if not profile:
            return

        behavioral_threats = self.behavioral_analyzer.analyze_behavior(event, profile)
        all_threats.extend(behavioral_threats)
        
        self._update_user_profile(event, profile)

    def _update_user_profile(self, event: SecurityEvent, profile) -> None:
        """
        تحديث ملف المستخدم.
        Update user profile.
        
        Args:
            event: حدث الأمان | Security event
            profile: ملف المستخدم | User profile
        """
        self.behavioral_analyzer.update_profile(event, profile)
        self.profile_repo.save_profile(profile)

    def _process_threats_response(self, all_threats: list[ThreatDetection]) -> None:
        """
        معالجة الاستجابة للتهديدات.
        Process threats response.
        
        Args:
            all_threats: قائمة التهديدات | Threats list
        """
        for threat in all_threats:
            self._handle_single_threat(threat)

    def _handle_single_threat(self, threat: ThreatDetection) -> None:
        """
        معالجة تهديد واحد.
        Handle single threat.
        
        Args:
            threat: التهديد | Threat
        """
        if self.response_system.should_auto_block(threat):
            self.response_system.execute_response(threat)
            threat.auto_blocked = True

        self.threat_logger.log_threat(threat)

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
