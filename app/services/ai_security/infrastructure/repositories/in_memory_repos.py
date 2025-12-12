"""
In-Memory Repositories - Infrastructure Implementation
======================================================
Simple in-memory storage for profiles and logs.

المستودعات في الذاكرة - التطبيق البنيوي
"""

from collections import deque
from typing import Optional

from ...domain.models import ThreatDetection, UserBehaviorProfile


class InMemoryProfileRepository:
    """
    مستودع الملفات الشخصية في الذاكرة
    
    In-memory storage for user behavioral profiles.
    """

    def __init__(self):
        """Initialize empty profile storage"""
        self._profiles: dict[str, UserBehaviorProfile] = {}

    def get_profile(self, user_id: str) -> Optional[UserBehaviorProfile]:
        """Get user profile by ID"""
        return self._profiles.get(user_id)

    def save_profile(self, profile: UserBehaviorProfile) -> None:
        """Save or update user profile"""
        self._profiles[profile.user_id] = profile

    def delete_profile(self, user_id: str) -> None:
        """Delete user profile"""
        self._profiles.pop(user_id, None)


class InMemoryThreatLogger:
    """
    مسجل التهديدات في الذاكرة
    
    In-memory storage for detected threats.
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize threat logger.
        
        Args:
            max_size: Maximum number of threats to keep in memory
        """
        self._threats: deque[ThreatDetection] = deque(maxlen=max_size)

    def log_threat(self, detection: ThreatDetection) -> None:
        """Log a detected threat"""
        self._threats.append(detection)

    def get_recent_threats(self, limit: int = 100) -> list[ThreatDetection]:
        """Get recently detected threats"""
        # Return most recent threats (from end of deque)
        recent = list(self._threats)
        return recent[-limit:] if len(recent) > limit else recent

    def clear(self) -> None:
        """Clear all logged threats"""
        self._threats.clear()


__all__ = [
    "InMemoryProfileRepository",
    "InMemoryThreatLogger",
]
