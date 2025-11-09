# app/middleware/security/__init__.py
# ======================================================================================
# ==                    MIDDLEWARE SECURITY MODULE (v∞ - Aurora Edition)            ==
# ======================================================================================
"""
وحدة الأمان - Security Module

Comprehensive security mesh for the superhuman middleware architecture.
Provides layered defense with AI-powered threat detection, Zero Trust
authentication, adaptive rate limiting, and WAF protection.

Security Philosophy:
    "Defense in Depth with AI Adaptation"
    - Multiple independent security layers
    - AI-powered behavioral analysis
    - Zero Trust continuous verification
    - Adaptive rate limiting per user tier
    - Policy-based access control
"""

from .ai_threat_middleware import AIThreatMiddleware
from .policy_enforcer import PolicyEnforcer
from .rate_limit_middleware import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware
from .superhuman_orchestrator import SuperhumanSecurityOrchestrator
from .telemetry_guard import TelemetryGuard
from .waf_middleware import WAFMiddleware
from .zero_trust_middleware import ZeroTrustMiddleware

__all__ = [
    "WAFMiddleware",
    "RateLimitMiddleware",
    "ZeroTrustMiddleware",
    "AIThreatMiddleware",
    "PolicyEnforcer",
    "SecurityHeadersMiddleware",
    "TelemetryGuard",
    "SuperhumanSecurityOrchestrator",
]

__version__ = "1.0.0-aurora"
