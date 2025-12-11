# app/services/analytics/application/nps_manager.py
"""
NPS Manager Service
===================
Single Responsibility: Manage Net Promoter Score responses and calculations.
"""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import Any


class NPSManager:
    """
    Net Promoter Score manager.
    
    Responsibilities:
    - Record NPS responses
    - Calculate NPS scores
    - Classify promoters/passives/detractors
    """
    
    def __init__(self):
        self._responses: list[dict[str, Any]] = []
    
    def record_response(
        self,
        user_id: int,
        score: int,
        comment: str = "",
    ) -> None:
        """Record NPS response"""
        if not 0 <= score <= 10:
            raise ValueError("NPS score must be between 0 and 10")
        
        response = {
            "user_id": user_id,
            "score": score,
            "comment": comment,
            "timestamp": datetime.utcnow(),
        }
        
        self._responses.append(response)
    
    def get_metrics(self) -> dict[str, Any]:
        """Calculate NPS metrics"""
        if not self._responses:
            return self._empty_metrics()
        
        scores = [r["score"] for r in self._responses]
        total = len(scores)
        
        # Classify responses
        # Promoters: 9-10
        # Passives: 7-8
        # Detractors: 0-6
        promoters = sum(1 for s in scores if s >= 9)
        passives = sum(1 for s in scores if 7 <= s <= 8)
        detractors = sum(1 for s in scores if s <= 6)
        
        promoters_percent = (promoters / total) * 100
        passives_percent = (passives / total) * 100
        detractors_percent = (detractors / total) * 100
        
        # NPS = % promoters - % detractors
        nps_score = promoters_percent - detractors_percent
        
        avg_score = statistics.mean(scores)
        
        return {
            "nps_score": nps_score,
            "promoters_percent": promoters_percent,
            "passives_percent": passives_percent,
            "detractors_percent": detractors_percent,
            "total_responses": total,
            "avg_score": avg_score,
        }
    
    def _empty_metrics(self) -> dict[str, Any]:
        """Return empty metrics"""
        return {
            "nps_score": 0.0,
            "promoters_percent": 0.0,
            "passives_percent": 0.0,
            "detractors_percent": 0.0,
            "total_responses": 0,
            "avg_score": 0.0,
        }
    
    def get_recent_comments(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent NPS comments"""
        return sorted(
            self._responses,
            key=lambda r: r["timestamp"],
            reverse=True,
        )[:limit]
