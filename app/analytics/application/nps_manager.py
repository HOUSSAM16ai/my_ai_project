"""NPS (Net Promoter Score) management use case."""

import statistics
from datetime import UTC, datetime

from app.analytics.domain import NPSMetrics, NPSStorePort


class NPSManager:
    """Handles NPS scoring logic"""

    def __init__(self, nps_store: NPSStorePort):
        self.nps_store = nps_store

    def record_nps_response(self, user_id: int, score: int, comment: str = "") -> None:
        """Record NPS response"""
        if not 0 <= score <= 10:
            raise ValueError("NPS score must be between 0 and 10")

        response = {
            "user_id": user_id,
            "score": score,
            "comment": comment,
            "timestamp": datetime.now(UTC),
        }

        self.nps_store.add_response(response)

    def get_nps_metrics(self) -> NPSMetrics:
        """Calculate NPS metrics"""
        responses = self.nps_store.get_responses()

        if not responses:
            return NPSMetrics(
                nps_score=0.0,
                promoters_percent=0.0,
                passives_percent=0.0,
                detractors_percent=0.0,
                total_responses=0,
                avg_score=0.0,
            )

        scores = [r["score"] for r in responses]
        total = len(scores)

        # Classify responses
        promoters = sum(1 for s in scores if s >= 9)
        passives = sum(1 for s in scores if 7 <= s <= 8)
        detractors = sum(1 for s in scores if s <= 6)

        promoters_percent = promoters / total * 100
        passives_percent = passives / total * 100
        detractors_percent = detractors / total * 100

        # NPS = % promoters - % detractors
        nps_score = promoters_percent - detractors_percent

        avg_score = statistics.mean(scores)

        return NPSMetrics(
            nps_score=nps_score,
            promoters_percent=promoters_percent,
            passives_percent=passives_percent,
            detractors_percent=detractors_percent,
            total_responses=total,
            avg_score=avg_score,
        )
