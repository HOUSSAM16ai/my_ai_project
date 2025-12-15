"""
AI Security Service Facade
==========================
Unified entry point maintaining backward compatibility.

واجهة خدمة الأمان AI - نقطة دخول موحدة
"""
from typing import Optional
from .application.security_manager import SecurityManager
from .domain.models import SecurityEvent, ThreatDetection, UserBehaviorProfile
from .infrastructure import DeepLearningThreatDetector, InMemoryProfileRepository, InMemoryThreatLogger, SimpleBehavioralAnalyzer, SimpleResponseSystem


class SuperhumanSecuritySystem:
    """
    نظام الأمان الخارق - Superhuman Security System
    
    Facade providing unified interface to AI security capabilities.
    Maintains backward compatibility with original monolithic implementation.
    """

    def __init__(self):
        """
        Initialize security system with default implementations.
        
        Creates all necessary components using dependency injection.
        """
        self._threat_detector = DeepLearningThreatDetector()
        self._behavioral_analyzer = SimpleBehavioralAnalyzer()
        self._response_system = SimpleResponseSystem()
        self._profile_repo = InMemoryProfileRepository()
        self._threat_logger = InMemoryThreatLogger()
        self._security_manager = SecurityManager(threat_detector=self.
            _threat_detector, behavioral_analyzer=self._behavioral_analyzer,
            response_system=self._response_system, profile_repo=self.
            _profile_repo, threat_logger=self._threat_logger)

    def analyze_event(self, event: SecurityEvent) ->list[ThreatDetection]:
        """
        Analyze security event for threats.
        
        Args:
            event: Security event to analyze
            
        Returns:
            List of detected threats
        """
        return self._security_manager.analyze_event(event)

    def get_recent_threats(self, limit: int=100) ->list[ThreatDetection]:
        """
        Get recently detected threats.
        
        Args:
            limit: Maximum number of threats to return
            
        Returns:
            List of recent threat detections
        """
        return self._security_manager.get_recent_threats(limit)

    def get_user_profile(self, user_id: str) ->Optional[UserBehaviorProfile]:
        """
        Get user behavioral profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile or None if not found
        """
        return self._security_manager.get_user_profile(user_id)


_security_system_instance: Optional[SuperhumanSecuritySystem] = None


def get_superhuman_security_system() ->SuperhumanSecuritySystem:
    """
    Get singleton instance of security system.
    
    Returns:
        SuperhumanSecuritySystem instance
    """
    global _security_system_instance
    if _security_system_instance is None:
        _security_system_instance = SuperhumanSecuritySystem()
    return _security_system_instance


__all__ = ['SuperhumanSecuritySystem', 'get_superhuman_security_system']
