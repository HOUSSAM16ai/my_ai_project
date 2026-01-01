"""
AI Security Service - SOLID Principles Applied
============================================
Advanced AI-powered security with threat detection and response.

نظام الأمان الخارق - تطبيق مبادئ SOLID

Simplified architecture using KISS principle:
- Domain: Pure business entities and interfaces
- Application: SecurityManager (direct access, no facade)
- Infrastructure: Concrete implementations

Usage:
    from app.services.ai_security import get_security_manager

    security = get_security_manager()
    threats = security.analyze_event(event)
"""

from .application.security_manager import SecurityManager
from .domain import (
    SecurityEvent,
    ThreatDetection,
    ThreatLevel,
    ThreatType,
    UserBehaviorProfile,
)

# Singleton instance
_manager_instance: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """
    Get singleton Security Manager instance.
    
    Returns:
        SecurityManager: The security manager instance
    """
    global _manager_instance
    if _manager_instance is None:
        from .infrastructure import (
            DeepLearningThreatDetector,
            InMemoryProfileRepository,
            InMemoryThreatLogger,
            SimpleBehavioralAnalyzer,
            SimpleResponseSystem,
        )
        
        _manager_instance = SecurityManager(
            threat_detector=DeepLearningThreatDetector(),
            behavioral_analyzer=SimpleBehavioralAnalyzer(),
            response_system=SimpleResponseSystem(),
            profile_repo=InMemoryProfileRepository(),
            threat_logger=InMemoryThreatLogger(),
        )
    return _manager_instance


# Backward compatibility
get_superhuman_security_system = get_security_manager


__all__ = [
    # Domain Models
    "SecurityEvent",
    "SecurityManager",
    "ThreatDetection",
    "ThreatLevel",
    "ThreatType",
    "UserBehaviorProfile",
    # Functions
    "get_security_manager",
    "get_superhuman_security_system",  # Backward compatibility
]
