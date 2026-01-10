"""
Automated Response System - Infrastructure Implementation
=========================================================
Simple automated threat response implementation.

نظام الاستجابة التلقائية
"""

from app.services.ai_security.domain.models import ThreatDetection, ThreatLevel


class SimpleResponseSystem:
    """
    نظام استجابة بسيط

    Simple implementation of automated threat response.
    """

    def __init__(self):
        """Initialize response system"""
        self.blocked_ips: set[str] = set()

    def execute_response(self, detection: ThreatDetection) -> dict:
        """
        Execute automated response.

        Args:
            detection: Detected threat

        Returns:
            Response details
        """
        response = {
            "detection_id": detection.detection_id,
            "action": "none",
            "timestamp": detection.detected_at.isoformat(),
        }

        if self.should_auto_block(detection):
            # Add IP to block list
            self.blocked_ips.add(detection.source_ip)
            response["action"] = "blocked"
            response["blocked_ip"] = detection.source_ip

        return response

    def should_auto_block(self, detection: ThreatDetection) -> bool:
        """
        Determine if threat should be auto-blocked.

        Args:
            detection: Detected threat

        Returns:
            True if should auto-block
        """
        # Auto-block critical threats with high confidence
        return detection.threat_level == ThreatLevel.CRITICAL and detection.confidence >= 0.90

    def is_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips

__all__ = ["SimpleResponseSystem"]
