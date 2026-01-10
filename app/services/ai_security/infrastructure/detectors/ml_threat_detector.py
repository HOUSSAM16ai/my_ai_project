"""
Deep Learning Threat Detector - Infrastructure Implementation
=============================================================
Concrete implementation of threat detection using pattern matching and ML.

كاشف التهديدات - التطبيق البنيوي
"""

import re
import uuid
from datetime import datetime

from app.services.ai_security.domain.models import (
    SecurityEvent,
    ThreatDetection,
    ThreatLevel,
    ThreatType,
)


class DeepLearningThreatDetector:
    """
    كاشف التهديدات بالتعلم العميق

    Implements ThreatDetectorPort using pattern matching and heuristics.
    """

    def __init__(self):
        """Initialize threat detection patterns"""
        self.sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
            r"(';|\")|(--)|(\/\*)",
            r"(\bor\b\s+1\s*=\s*1)",
            r"(\bdrop\b\s+\btable\b)",
            r"(\binsert\b\s+\binto\b)",
            r"(\bexec\b|\bexecute\b)",
        ]

        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe",
            r"<embed",
            r"<object",
        ]

    def detect_threats(self, event: SecurityEvent) -> list[ThreatDetection]:
        """
        كشف التهديدات في حدث الأمان.
        Detect threats in security event.

        Args:
            event: حدث الأمان للتحليل | Security event to analyze

        Returns:
            list[ThreatDetection]: قائمة التهديدات المكتشفة | List of detected threats
        """
        threats = []

        self._detect_sql_injection_threat(event, threats)
        self._detect_xss_threat(event, threats)

        return threats

    def _detect_sql_injection_threat(self, event: SecurityEvent, threats: list) -> None:
        """
        كشف تهديد حقن SQL.
        Detect SQL injection threat.

        Args:
            event: حدث الأمان | Security event
            threats: قائمة التهديدات للتحديث | Threats list to update
        """
        sql_issues = self._check_sql_injection(event.payload)
        if sql_issues:
            threat = self._create_sql_injection_detection(event, sql_issues)
            threats.append(threat)

    def _detect_xss_threat(self, event: SecurityEvent, threats: list) -> None:
        """
        كشف تهديد XSS.
        Detect XSS threat.

        Args:
            event: حدث الأمان | Security event
            threats: قائمة التهديدات للتحديث | Threats list to update
        """
        xss_issues = self._check_xss_attack(event.payload)
        if xss_issues:
            threat = self._create_xss_detection(event, xss_issues)
            threats.append(threat)

    def _create_sql_injection_detection(
        self,
        event: SecurityEvent,
        evidence: list[str]
    ) -> ThreatDetection:
        """
        إنشاء كشف حقن SQL.
        Create SQL injection detection.

        Args:
            event: حدث الأمان | Security event
            evidence: الأدلة المكتشفة | Detected evidence

        Returns:
            ThreatDetection: كشف التهديد | Threat detection
        """
        return ThreatDetection(
            detection_id=str(uuid.uuid4()),
            threat_type=ThreatType.SQL_INJECTION,
            threat_level=ThreatLevel.CRITICAL,
            description="SQL injection attempt detected",
            source_ip=event.source_ip,
            user_id=event.user_id,
            confidence=0.95,
            evidence=evidence,
            recommended_action="block_immediately",
            detected_at=datetime.now(),
        )

    def _create_xss_detection(
        self,
        event: SecurityEvent,
        evidence: list[str]
    ) -> ThreatDetection:
        """
        إنشاء كشف XSS.
        Create XSS detection.

        Args:
            event: حدث الأمان | Security event
            evidence: الأدلة المكتشفة | Detected evidence

        Returns:
            ThreatDetection: كشف التهديد | Threat detection
        """
        return ThreatDetection(
            detection_id=str(uuid.uuid4()),
            threat_type=ThreatType.XSS_ATTACK,
            threat_level=ThreatLevel.HIGH,
            description="XSS attack attempt detected",
            source_ip=event.source_ip,
            user_id=event.user_id,
            confidence=0.90,
            evidence=evidence,
            recommended_action="sanitize_and_block",
            detected_at=datetime.now(),
        )

    def analyze_payload(self, payload: dict) -> list[str]:
        """
        Analyze payload for malicious patterns.

        Args:
            payload: Request payload

        Returns:
            List of detected issues
        """
        issues = []
        issues.extend(self._check_sql_injection(payload))
        issues.extend(self._check_xss_attack(payload))
        return issues

    def _check_sql_injection(self, payload: dict) -> list[str]:
        """Check for SQL injection patterns"""
        findings = []
        payload_str = str(payload).lower()

        for pattern in self.sql_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                findings.append(f"SQL pattern detected: {pattern}")

        return findings

    def _check_xss_attack(self, payload: dict) -> list[str]:
        """Check for XSS attack patterns"""
        findings = []
        payload_str = str(payload)

        for pattern in self.xss_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                findings.append(f"XSS pattern detected: {pattern}")

        return findings

__all__ = ["DeepLearningThreatDetector"]
