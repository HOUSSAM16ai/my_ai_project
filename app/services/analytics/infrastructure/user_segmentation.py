# app/services/analytics/infrastructure/user_segmentation.py
"""
User Segmentation Implementation
=================================
Concrete implementation of UserSegmentationPort for user classification.

Uses rule-based segmentation. Production systems could use ML-based
segmentation with features from behavior, demographics, and engagement.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

from app.services.analytics.domain.models import UserSegment
from app.services.analytics.domain.ports import UserSegmentationPort


class InMemoryUserSegmentation(UserSegmentationPort):
    """
    In-memory rule-based user segmentation.
    
    Features:
    - Rule-based classification
    - Thread-safe operations
    - Real-time segment updates
    - Segment analytics
    """
    
    def __init__(self):
        """Initialize user segmentation."""
        self._user_segments: dict[int, UserSegment] = {}
        self._segment_users: dict[UserSegment, set[int]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def classify_user(
        self,
        user_id: int,
        user_data: dict[str, Any],
    ) -> UserSegment:
        """
        Classify user into a segment based on behavior data.
        
        Args:
            user_id: User identifier
            user_data: User behavior data including:
                - total_events: Total number of events
                - total_sessions: Total number of sessions
                - avg_session_duration: Average session duration
                - days_since_signup: Days since user signed up
                - total_conversions: Number of conversions
                
        Returns:
            UserSegment classification
        """
        with self._lock:
            # Extract metrics
            total_events = user_data.get("total_events", 0)
            total_sessions = user_data.get("total_sessions", 0)
            days_since_signup = user_data.get("days_since_signup", 0)
            total_conversions = user_data.get("total_conversions", 0)
            
            # Rule-based classification
            segment = self._apply_segmentation_rules(
                total_events=total_events,
                total_sessions=total_sessions,
                days_since_signup=days_since_signup,
                total_conversions=total_conversions,
            )
            
            # Update segment tracking
            old_segment = self._user_segments.get(user_id)
            if old_segment and old_segment != segment:
                self._segment_users[old_segment].discard(user_id)
            
            self._user_segments[user_id] = segment
            self._segment_users[segment].add(user_id)
            
            return segment
    
    def _apply_segmentation_rules(
        self,
        total_events: int,
        total_sessions: int,
        days_since_signup: int,
        total_conversions: int,
    ) -> UserSegment:
        """
        Apply segmentation rules to classify user.
        
        Segmentation logic:
        - NEW: Less than 7 days since signup, few sessions
        - ACTIVE: Regular engagement, multiple sessions
        - POWER: High engagement, many events and sessions
        - AT_RISK: Previously active but declining engagement
        - CHURNED: No activity in last 30 days
        """
        # New users (less than 7 days, low activity)
        if days_since_signup < 7:
            return UserSegment.NEW
        
        # Power users (high engagement)
        if total_events > 100 and total_sessions > 20:
            return UserSegment.POWER
        
        # Active users (regular engagement)
        if total_events > 20 and total_sessions > 5:
            return UserSegment.ACTIVE
        
        # At-risk users (some activity but declining)
        if total_events > 10 and total_sessions > 2:
            return UserSegment.AT_RISK
        
        # Churned users (very low or no activity)
        return UserSegment.CHURNED
    
    def get_segment_users(
        self,
        segment: UserSegment,
    ) -> list[int]:
        """
        Get all users in a segment.
        
        Args:
            segment: User segment
            
        Returns:
            List of user IDs in segment
        """
        with self._lock:
            return list(self._segment_users.get(segment, set()))
    
    def update_segmentation(self) -> dict[UserSegment, int]:
        """
        Update all user segments and return counts.
        
        This is a no-op in the current implementation since segmentation
        happens on-demand in classify_user(). In a production system,
        this could trigger batch re-segmentation of all users.
        
        Returns:
            Dictionary mapping segments to user counts
        """
        with self._lock:
            return {
                segment: len(users)
                for segment, users in self._segment_users.items()
            }
    
    def get_segment_stats(self) -> dict[str, Any]:
        """
        Get statistics about all segments.
        
        Returns:
            Dictionary with segment statistics
        """
        with self._lock:
            total_users = sum(len(users) for users in self._segment_users.values())
            
            segment_stats = {}
            for segment, users in self._segment_users.items():
                count = len(users)
                percentage = (count / total_users * 100) if total_users > 0 else 0.0
                
                segment_stats[segment.value] = {
                    "count": count,
                    "percentage": percentage,
                }
            
            return {
                "total_users": total_users,
                "segments": segment_stats,
            }


__all__ = [
    "InMemoryUserSegmentation",
]
