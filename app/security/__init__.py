# app/security/__init__.py
# ======================================================================================
# ==           SUPERHUMAN SECURITY MODULE (v1.0 - QUANTUM-GRADE EDITION)            ==
# ======================================================================================
"""
نظام الأمان الخارق - Superhuman Security System

This module provides world-class security features that surpass tech giants:
- Multi-layer defense system
- AI-powered threat detection
- Zero-trust architecture
- Quantum-safe encryption preparation
- Real-time threat mitigation
"""

from app.security.encryption import QuantumSafeEncryption
from app.security.rate_limiter import AdaptiveRateLimiter
from app.security.threat_detector import AIThreatDetector
from app.security.waf import WebApplicationFirewall
from app.security.zero_trust import ZeroTrustAuthenticator

__all__ = [
    "WebApplicationFirewall",
    "AdaptiveRateLimiter",
    "ZeroTrustAuthenticator",
    "AIThreatDetector",
    "QuantumSafeEncryption",
]
