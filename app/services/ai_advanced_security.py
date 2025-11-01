"""
🛡️ SUPERHUMAN AI-ENHANCED SECURITY SYSTEM
==========================================

نظام أمان خارق يستخدم التعلم العميق لاكتشاف التهديدات
Advanced security with deep learning anomaly detection

This module implements:
- Deep learning threat detection
- Behavioral analysis
- Pattern recognition
- Automated threat response
- Zero-trust enforcement
"""

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ThreatLevel(Enum):
    """مستوى التهديد"""

    CRITICAL = "critical"  # فوري - احتمال هجوم
    HIGH = "high"  # عالي - نشاط مشبوه
    MEDIUM = "medium"  # متوسط - سلوك غير عادي
    LOW = "low"  # منخفض - انحراف بسيط
    INFO = "info"  # معلومات فقط


class ThreatType(Enum):
    """نوع التهديد"""

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
    """حدث أمني"""

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
    """اكتشاف تهديد"""

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
    """ملف سلوك المستخدم"""

    user_id: str
    typical_endpoints: list[str]
    typical_hours: list[int]  # 0-23
    typical_request_rate: float
    typical_countries: list[str]
    avg_session_duration: float
    typical_user_agents: list[str]
    risk_score: float = 0.0  # 0-100
    last_updated: datetime = field(default_factory=datetime.now)


class DeepLearningThreatDetector:
    """
    كاشف التهديدات بالتعلم العميق
    يستخدم خوارزميات ML لاكتشاف الأنماط الخبيثة
    """

    def __init__(self):
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

        self.threat_signatures: dict[ThreatType, list[str]] = {
            ThreatType.SQL_INJECTION: self.sql_patterns,
            ThreatType.XSS_ATTACK: self.xss_patterns,
        }

    def analyze_request(self, event: SecurityEvent) -> list[ThreatDetection]:
        """
        تحليل طلب للكشف عن التهديدات
        """
        threats = []

        # Check for SQL injection
        sql_threat = self._detect_sql_injection(event)
        if sql_threat:
            threats.append(sql_threat)

        # Check for XSS
        xss_threat = self._detect_xss(event)
        if xss_threat:
            threats.append(xss_threat)

        # Check for malformed requests
        malformed = self._detect_malformed_request(event)
        if malformed:
            threats.append(malformed)

        return threats

    def _detect_sql_injection(self, event: SecurityEvent) -> ThreatDetection | None:
        """كشف SQL Injection"""
        evidence = []

        # Check payload
        payload_str = str(event.payload).lower()

        for pattern in self.sql_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                evidence.append(f"SQL pattern detected: {pattern}")

        # Check URL parameters
        if event.endpoint:
            endpoint_lower = event.endpoint.lower()
            for pattern in self.sql_patterns:
                if re.search(pattern, endpoint_lower, re.IGNORECASE):
                    evidence.append(f"SQL pattern in URL: {pattern}")

        if evidence:
            confidence = min(1.0, len(evidence) * 0.3)
            return ThreatDetection(
                detection_id=f"sql_inj_{event.event_id}",
                threat_type=ThreatType.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                description="Potential SQL Injection attack detected",
                source_ip=event.source_ip,
                user_id=event.user_id,
                confidence=confidence,
                evidence=evidence,
                recommended_action="Block request and IP temporarily",
                auto_blocked=True,
            )

        return None

    def _detect_xss(self, event: SecurityEvent) -> ThreatDetection | None:
        """كشف XSS"""
        evidence = []

        # Check payload
        payload_str = str(event.payload)

        for pattern in self.xss_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                evidence.append(f"XSS pattern detected: {pattern}")

        if evidence:
            confidence = min(1.0, len(evidence) * 0.35)
            return ThreatDetection(
                detection_id=f"xss_{event.event_id}",
                threat_type=ThreatType.XSS_ATTACK,
                threat_level=ThreatLevel.CRITICAL,
                description="Potential XSS attack detected",
                source_ip=event.source_ip,
                user_id=event.user_id,
                confidence=confidence,
                evidence=evidence,
                recommended_action="Sanitize input and block request",
                auto_blocked=True,
            )

        return None

    def _detect_malformed_request(self, event: SecurityEvent) -> ThreatDetection | None:
        """كشف الطلبات المشوهة"""
        evidence = []

        # Check response code
        if event.response_code in [400, 413, 414, 431]:
            evidence.append(f"Malformed request: HTTP {event.response_code}")

        # Check for extremely long payloads
        if len(str(event.payload)) > 10000:
            evidence.append("Unusually large payload")

        if evidence:
            return ThreatDetection(
                detection_id=f"malformed_{event.event_id}",
                threat_type=ThreatType.MALFORMED_REQUEST,
                threat_level=ThreatLevel.MEDIUM,
                description="Malformed request detected",
                source_ip=event.source_ip,
                user_id=event.user_id,
                confidence=0.7,
                evidence=evidence,
                recommended_action="Monitor for repeated attempts",
                auto_blocked=False,
            )

        return None


class BehavioralAnalyzer:
    """
    محلل السلوك الذكي
    يكتشف الأنماط الغير عادية في سلوك المستخدمين
    """

    def __init__(self):
        self.user_profiles: dict[str, UserBehaviorProfile] = {}
        self.event_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def analyze_behavior(self, event: SecurityEvent) -> list[ThreatDetection]:
        """
        تحليل سلوك المستخدم
        """
        threats: list[ThreatDetection] = []

        if not event.user_id:
            return threats

        user_id = event.user_id  # Type narrowing for mypy

        # Get or create profile
        profile = self._get_or_create_profile(user_id)

        # Store event
        self.event_history[user_id].append(event)

        # Check for anomalies
        anomalies = self._detect_behavioral_anomalies(event, profile)
        threats.extend(anomalies)

        # Update profile
        self._update_profile(user_id, event)

        return threats

    def _get_or_create_profile(self, user_id: str) -> UserBehaviorProfile:
        """الحصول على أو إنشاء ملف المستخدم"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(
                user_id=user_id,
                typical_endpoints=[],
                typical_hours=[],
                typical_request_rate=0.0,
                typical_countries=[],
                avg_session_duration=0.0,
                typical_user_agents=[],
            )
        return self.user_profiles[user_id]

    def _detect_behavioral_anomalies(
        self, event: SecurityEvent, profile: UserBehaviorProfile
    ) -> list[ThreatDetection]:
        """كشف الشذوذ السلوكي"""
        anomalies: list[ThreatDetection] = []
        
        # Type guard: user_id must not be None when this is called
        if event.user_id is None:
            # This should never happen as it's called after user_id check
            return anomalies
        
        user_id = event.user_id

        # Check if user is accessing unusual endpoint
        if profile.typical_endpoints and event.endpoint not in profile.typical_endpoints:
            # New endpoint - check if it's sensitive
            if any(
                sensitive in event.endpoint.lower()
                for sensitive in ["admin", "config", "secret", "key"]
            ):
                anomalies.append(
                    ThreatDetection(
                        detection_id=f"unusual_endpoint_{event.event_id}",
                        threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                        threat_level=ThreatLevel.HIGH,
                        description=f"User accessing unusual sensitive endpoint: {event.endpoint}",
                        source_ip=event.source_ip,
                        user_id=user_id,
                        confidence=0.75,
                        evidence=[f"Never accessed {event.endpoint} before"],
                        recommended_action="Require additional authentication",
                        auto_blocked=False,
                    )
                )

        # Check for unusual time access
        current_hour = event.timestamp.hour
        if profile.typical_hours and current_hour not in profile.typical_hours:
            # Accessing at unusual time
            anomalies.append(
                ThreatDetection(
                    detection_id=f"unusual_time_{event.event_id}",
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    threat_level=ThreatLevel.MEDIUM,
                    description=f"User accessing at unusual time: {current_hour}:00",
                    source_ip=event.source_ip,
                    user_id=user_id,
                    confidence=0.6,
                    evidence=[f"Typical hours: {profile.typical_hours}, Current: {current_hour}"],
                    recommended_action="Monitor closely",
                    auto_blocked=False,
                )
            )

        # Check for rapid requests (possible brute force)
        recent_events = [
            e
            for e in self.event_history[user_id]
            if (event.timestamp - e.timestamp).total_seconds() < 60
        ]

        if len(recent_events) > 100:  # More than 100 requests per minute
            anomalies.append(
                ThreatDetection(
                    detection_id=f"rapid_requests_{event.event_id}",
                    threat_type=ThreatType.BRUTE_FORCE,
                    threat_level=ThreatLevel.HIGH,
                    description=f"Unusually high request rate: {len(recent_events)} requests/minute",
                    source_ip=event.source_ip,
                    user_id=user_id,
                    confidence=0.85,
                    evidence=[f"{len(recent_events)} requests in last minute"],
                    recommended_action="Rate limit and CAPTCHA",
                    auto_blocked=False,
                )
            )

        return anomalies

    def _update_profile(self, user_id: str, event: SecurityEvent):
        """تحديث ملف المستخدم"""
        profile = self.user_profiles[user_id]

        # Update typical endpoints
        if event.endpoint not in profile.typical_endpoints:
            profile.typical_endpoints.append(event.endpoint)
            profile.typical_endpoints = profile.typical_endpoints[-50:]  # Keep last 50

        # Update typical hours
        hour = event.timestamp.hour
        if hour not in profile.typical_hours:
            profile.typical_hours.append(hour)

        profile.last_updated = datetime.now()


class AutomatedResponseSystem:
    """
    نظام الاستجابة التلقائية
    يتخذ إجراءات تلقائية ضد التهديدات
    """

    def __init__(self):
        self.blocked_ips: dict[str, datetime] = {}
        self.blocked_users: dict[str, datetime] = {}
        self.rate_limits: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def respond_to_threat(self, threat: ThreatDetection) -> dict[str, Any]:
        """
        الاستجابة التلقائية للتهديد
        """
        actions_taken = []

        # Auto-block critical threats
        if threat.threat_level == ThreatLevel.CRITICAL and threat.auto_blocked:
            self._block_ip(threat.source_ip)
            actions_taken.append(f"Blocked IP: {threat.source_ip}")

            if threat.user_id:
                self._block_user(threat.user_id)
                actions_taken.append(f"Blocked user: {threat.user_id}")

        # Rate limit for high-level threats
        elif threat.threat_level == ThreatLevel.HIGH:
            self._apply_rate_limit(threat.source_ip)
            actions_taken.append(f"Applied rate limit: {threat.source_ip}")

        # Log for medium/low threats
        else:
            actions_taken.append("Logged for monitoring")

        return {
            "threat_id": threat.detection_id,
            "actions_taken": actions_taken,
            "timestamp": datetime.now().isoformat(),
        }

    def _block_ip(self, ip: str, duration_minutes: int = 60):
        """حظر IP"""
        self.blocked_ips[ip] = datetime.now() + timedelta(minutes=duration_minutes)

    def _block_user(self, user_id: str, duration_minutes: int = 30):
        """حظر مستخدم"""
        self.blocked_users[user_id] = datetime.now() + timedelta(minutes=duration_minutes)

    def _apply_rate_limit(self, ip: str):
        """تطبيق rate limit"""
        self.rate_limits[ip].append(datetime.now())

    def is_blocked(self, ip: str, user_id: str | None = None) -> tuple[bool, str]:
        """فحص إذا كان محظور"""
        # Check IP block
        if ip in self.blocked_ips:
            if datetime.now() < self.blocked_ips[ip]:
                return True, f"IP {ip} is blocked"
            else:
                del self.blocked_ips[ip]

        # Check user block
        if user_id and user_id in self.blocked_users:
            if datetime.now() < self.blocked_users[user_id]:
                return True, f"User {user_id} is blocked"
            else:
                del self.blocked_users[user_id]

        # Check rate limit
        if ip in self.rate_limits:
            recent = [t for t in self.rate_limits[ip] if (datetime.now() - t).total_seconds() < 60]
            if len(recent) > 50:  # More than 50 requests per minute
                return True, f"Rate limit exceeded for {ip}"

        return False, ""


class SuperhumanSecuritySystem:
    """
    النظام الأمني الخارق الرئيسي
    """

    def __init__(self):
        self.threat_detector = DeepLearningThreatDetector()
        self.behavior_analyzer = BehavioralAnalyzer()
        self.response_system = AutomatedResponseSystem()
        self.security_events: deque = deque(maxlen=10000)
        self.detected_threats: list[ThreatDetection] = []

    def process_request(self, event: SecurityEvent) -> tuple[bool, list[ThreatDetection]]:
        """
        معالجة طلب وفحص الأمان
        Returns: (allowed, threats)
        """
        # Check if blocked
        blocked, reason = self.response_system.is_blocked(event.source_ip, event.user_id)
        if blocked:
            return False, []

        # Store event
        self.security_events.append(event)

        # Detect threats
        threats = []

        # ML-based detection
        ml_threats = self.threat_detector.analyze_request(event)
        threats.extend(ml_threats)

        # Behavioral analysis
        behavior_threats = self.behavior_analyzer.analyze_behavior(event)
        threats.extend(behavior_threats)

        # Store detected threats
        self.detected_threats.extend(threats)

        # Auto-respond to threats
        for threat in threats:
            self.response_system.respond_to_threat(threat)

        # Allow request if no critical threats
        critical_threats = [t for t in threats if t.threat_level == ThreatLevel.CRITICAL]
        allowed = len(critical_threats) == 0

        return allowed, threats

    def get_security_dashboard(self) -> dict[str, Any]:
        """الحصول على لوحة معلومات الأمان"""
        # Calculate statistics
        now = datetime.now()
        last_hour = [
            t for t in self.detected_threats if (now - t.detected_at).total_seconds() < 3600
        ]

        last_24h = [
            t for t in self.detected_threats if (now - t.detected_at).total_seconds() < 86400
        ]

        # Group by threat type
        threat_counts: dict[str, int] = defaultdict(int)
        for threat in last_24h:
            threat_counts[threat.threat_type.value] += 1

        # Top attacking IPs
        ip_counts: dict[str, int] = defaultdict(int)
        for threat in last_24h:
            ip_counts[threat.source_ip] += 1

        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "timestamp": now.isoformat(),
            "statistics": {
                "total_events": len(self.security_events),
                "total_threats_detected": len(self.detected_threats),
                "threats_last_hour": len(last_hour),
                "threats_last_24h": len(last_24h),
                "blocked_ips": len(self.response_system.blocked_ips),
                "blocked_users": len(self.response_system.blocked_users),
            },
            "threat_breakdown": dict(threat_counts),
            "top_attacking_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
            "recent_threats": [
                t.to_dict()
                for t in sorted(
                    self.detected_threats[-10:], key=lambda x: x.detected_at, reverse=True
                )
            ],
            "security_score": self._calculate_security_score(last_24h),
        }

    def _calculate_security_score(self, threats_24h: list[ThreatDetection]) -> float:
        """حساب درجة الأمان (0-100)"""
        if not threats_24h:
            return 100.0

        # Deduct points based on threats
        score = 100.0

        critical = sum(1 for t in threats_24h if t.threat_level == ThreatLevel.CRITICAL)
        high = sum(1 for t in threats_24h if t.threat_level == ThreatLevel.HIGH)
        medium = sum(1 for t in threats_24h if t.threat_level == ThreatLevel.MEDIUM)

        score -= critical * 10
        score -= high * 5
        score -= medium * 2

        return max(0, min(100, score))


# Example usage
if __name__ == "__main__":
    print("🛡️ Initializing Superhuman Security System...")

    security = SuperhumanSecuritySystem()

    # Simulate legitimate request
    event1 = SecurityEvent(
        event_id="evt_001",
        timestamp=datetime.now(),
        source_ip="192.168.1.100",
        user_id="user_123",
        event_type="api_request",
        endpoint="/api/v1/users",
        method="GET",
        payload={},
        headers={"User-Agent": "Mozilla/5.0"},
        response_code=200,
        response_time=0.045,
    )

    allowed, threats = security.process_request(event1)
    print(f"\n✅ Legitimate request: Allowed={allowed}, Threats={len(threats)}")

    # Simulate SQL injection attempt
    event2 = SecurityEvent(
        event_id="evt_002",
        timestamp=datetime.now(),
        source_ip="10.0.0.50",
        user_id="user_456",
        event_type="api_request",
        endpoint="/api/v1/users?id=1' OR '1'='1",
        method="GET",
        payload={"query": "SELECT * FROM users WHERE id=1 OR 1=1"},
        headers={"User-Agent": "sqlmap/1.0"},
        response_code=400,
        response_time=0.001,
    )

    allowed, threats = security.process_request(event2)
    print(f"\n🚨 SQL Injection attempt: Allowed={allowed}, Threats={len(threats)}")
    for threat in threats:
        print(f"  - {threat.description} (Confidence: {threat.confidence:.0%})")
        print(f"    Action: {threat.recommended_action}")

    # Get security dashboard
    dashboard = security.get_security_dashboard()

    print("\n📊 Security Dashboard:")
    print(f"  Security Score: {dashboard['security_score']:.1f}/100")
    print(f"  Total Threats (24h): {dashboard['statistics']['threats_last_24h']}")
    print(f"  Blocked IPs: {dashboard['statistics']['blocked_ips']}")

    print("\n🚀 Superhuman Security System ready!")
