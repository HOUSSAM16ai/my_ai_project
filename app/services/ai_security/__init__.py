"""
AI Security Service - Hexagonal Architecture
============================================
Advanced AI-powered security with threat detection and response.

نظام الأمان الخارق - معمارية سداسية

This package follows Hexagonal Architecture (Ports & Adapters):
- Domain: Pure business entities and interfaces
- Application: Business logic orchestration
- Infrastructure: Concrete implementations
- Facade: Unified entry point

Usage:
    from app.services.ai_security import get_superhuman_security_system
    
    security = get_superhuman_security_system()
    threats = security.analyze_event(event)
"""

from .domain import (
    SecurityEvent,
    ThreatDetection,
    ThreatLevel,
    ThreatType,
    UserBehaviorProfile,
)
from .facade import SuperhumanSecuritySystem, get_superhuman_security_system

__all__ = [
    # Facade
    "SuperhumanSecuritySystem",
    "get_superhuman_security_system",
    # Domain Models
    "SecurityEvent",
    "ThreatDetection",
    "ThreatLevel",
    "ThreatType",
    "UserBehaviorProfile",
]
