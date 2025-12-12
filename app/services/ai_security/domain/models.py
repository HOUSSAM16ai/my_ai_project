"""
AI Security Domain Models
==========================
Pure business entities with zero external dependencies.

نماذج المجال الأمني - كيانات نقية بدون تبعيات خارجية
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ThreatLevel(Enum):
    """مستوى التهديد - Threat severity level"""

    CRITICAL = "critical"  # فوري - احتمال هجوم
    HIGH = "high"  # عالي - نشاط مشبوه
    MEDIUM = "medium"  # متوسط - سلوك غير عادي
    LOW = "low"  # منخفض - انحراف بسيط
    INFO = "info"  # معلومات فقط


class ThreatType(Enum):
    """نوع التهديد - Type of security threat"""

    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALFORMED_REQUEST = "malformed_request"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


@dataclass
class SecurityEvent:
    """
    حدث أمني - Security event from system monitoring
    
    Represents a single security-relevant event in the system.
    """

    event_id: str
    timestamp: datetime
    source_ip: str
    user_id: str | None
    event_type: str
    endpoint: str
    method: str
    payload: dict[str, Any]
    headers: dict[str, str]
    response_code: int
    response_time: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "endpoint": self.endpoint,
            "method": self.method,
            "response_code": self.response_code,
            "response_time": self.response_time,
        }


@dataclass
class ThreatDetection:
    """
    اكتشاف تهديد - Detected security threat
    
    Represents a detected threat with evidence and recommended action.
    """

    detection_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    description: str
    source_ip: str
    user_id: str | None
    confidence: float  # 0-1
    evidence: list[str]
    recommended_action: str
    auto_blocked: bool = False
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "detection_id": self.detection_id,
            "threat_type": self.threat_type.value,
            "threat_level": self.threat_level.value,
            "description": self.description,
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "auto_blocked": self.auto_blocked,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class UserBehaviorProfile:
    """
    ملف سلوك المستخدم - User behavioral profile
    
    Tracks normal user behavior patterns for anomaly detection.
    """

    user_id: str
    typical_endpoints: list[str]
    typical_hours: list[int]  # 0-23
    typical_request_rate: float
    typical_countries: list[str]
    avg_session_duration: float
    typical_user_agents: list[str]
    risk_score: float = 0.0  # 0-100
    last_updated: datetime = field(default_factory=datetime.now)


__all__ = [
    "ThreatLevel",
    "ThreatType",
    "SecurityEvent",
    "ThreatDetection",
    "UserBehaviorProfile",
]
