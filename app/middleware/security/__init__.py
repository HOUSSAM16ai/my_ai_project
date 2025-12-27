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

from .rate_limit_middleware import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware

__all__ = [
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]

__version__ = "1.0.0-aurora"
