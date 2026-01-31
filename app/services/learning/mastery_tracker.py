"""
متتبع الإتقان (Mastery Tracker).
================================

يتتبع تقدم الطالب في إتقان المفاهيم عبر الزمن.

المعايير:
- CS50 2025: توثيق عربي
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.services.learning.student_profile import StudentProfile, get_student_profile

logger = logging.getLogger(__name__)


class MasterySnapshot(BaseModel):
    """لقطة من الإتقان في نقطة زمنية."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    topic_id: str
    mastery_score: float
    accuracy: float
    attempts: int


class MasteryTrend(BaseModel):
    """اتجاه الإتقان عبر الزمن."""
    
    topic_id: str
    topic_name: str
    current_score: float
    previous_score: float
    change: float
    trend: str = Field(..., description="improving, declining, stable")
    prediction_7_days: float


class MasteryTracker:
    """
    يتتبع ويحلل تقدم إتقان الطالب.
    
    المميزات:
    - تتبع التقدم عبر الزمن
    - كشف الاتجاهات (تحسن/تراجع)
    - التنبؤ بالإتقان المستقبلي
    - تحديد المواضيع التي تحتاج مراجعة
    """
    
    # عتبة التغيير المهم
    SIGNIFICANT_CHANGE = 0.1  # 10%
    
    # فترة النسيان (Forgetting Curve)
    DECAY_DAYS = 14  # بعد أسبوعين، يبدأ النسيان
    DECAY_RATE = 0.05  # 5% انخفاض في الإتقان
    
    async def get_progress_report(
        self,
        student_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        يولّد تقرير تقدم شامل.
        
        Args:
            student_id: معرف الطالب
            days: عدد الأيام للتحليل
            
        Returns:
            dict: تقرير التقدم
        """
        profile = await get_student_profile(student_id)
        
        trends = self._analyze_trends(profile, days)
        at_risk_topics = self._identify_at_risk_topics(profile)
        study_plan = self._generate_study_plan(profile, at_risk_topics)
        
        return {
            "student_id": student_id,
            "period_days": days,
            "overall_mastery": profile.overall_mastery,
            "overall_accuracy": profile.overall_accuracy,
            "total_attempts": profile.total_attempts,
            "trends": [t.model_dump() for t in trends],
            "at_risk_topics": at_risk_topics,
            "study_plan": study_plan,
            "strengths": profile.strengths,
            "weaknesses": profile.weaknesses,
        }
    
    def _analyze_trends(
        self,
        profile: StudentProfile,
        days: int,
    ) -> list[MasteryTrend]:
        """يحلل اتجاهات الإتقان."""
        
        trends = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for topic_id, tm in profile.topic_mastery.items():
            # حساب الإتقان السابق من التاريخ
            old_events = [
                e for e in profile.learning_history
                if e.topic_id == topic_id and e.timestamp < cutoff
            ]
            
            if old_events:
                old_correct = sum(1 for e in old_events if e.event_type == "correct")
                previous_score = old_correct / len(old_events) if old_events else 0.5
            else:
                previous_score = 0.5
            
            current_score = tm.mastery_score
            change = current_score - previous_score
            
            # تحديد الاتجاه
            if change > self.SIGNIFICANT_CHANGE:
                trend = "improving"
            elif change < -self.SIGNIFICANT_CHANGE:
                trend = "declining"
            else:
                trend = "stable"
            
            # التنبؤ (linear projection)
            prediction = min(1.0, max(0.0, current_score + change * 0.5))
            
            trends.append(MasteryTrend(
                topic_id=topic_id,
                topic_name=tm.topic_name,
                current_score=current_score,
                previous_score=previous_score,
                change=change,
                trend=trend,
                prediction_7_days=prediction,
            ))
        
        return trends
    
    def _identify_at_risk_topics(
        self,
        profile: StudentProfile,
    ) -> list[dict[str, Any]]:
        """يحدد المواضيع المعرضة للنسيان."""
        
        at_risk = []
        now = datetime.now()
        
        for topic_id, tm in profile.topic_mastery.items():
            if tm.last_practiced is None:
                continue
            
            days_since_practice = (now - tm.last_practiced).days
            
            if days_since_practice > self.DECAY_DAYS:
                # حساب الانخفاض المتوقع
                decay_periods = (days_since_practice - self.DECAY_DAYS) // 7
                expected_decay = decay_periods * self.DECAY_RATE
                predicted_mastery = max(0.0, tm.mastery_score - expected_decay)
                
                at_risk.append({
                    "topic_id": topic_id,
                    "topic_name": tm.topic_name,
                    "days_since_practice": days_since_practice,
                    "current_mastery": tm.mastery_score,
                    "predicted_mastery": predicted_mastery,
                    "urgency": "high" if predicted_mastery < 0.5 else "medium",
                })
        
        # ترتيب حسب الإلحاح
        at_risk.sort(key=lambda x: x["predicted_mastery"])
        
        return at_risk
    
    def _generate_study_plan(
        self,
        profile: StudentProfile,
        at_risk: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """يولّد خطة دراسة شخصية."""
        
        # أولوية 1: المواضيع المعرضة للنسيان
        review_topics = [t["topic_name"] for t in at_risk[:3]]
        
        # أولوية 2: نقاط الضعف
        weak_topics = profile.weaknesses[:2]
        
        # المواضيع المقترحة للممارسة
        practice_topics = list(set(review_topics + weak_topics))[:5]
        
        # حساب الوقت المقترح
        suggested_time = len(practice_topics) * 15  # 15 دقيقة لكل موضوع
        
        return {
            "review_topics": review_topics,
            "practice_topics": practice_topics,
            "suggested_time_minutes": suggested_time,
            "focus_message": self._generate_focus_message(profile, at_risk),
        }
    
    def _generate_focus_message(
        self,
        profile: StudentProfile,
        at_risk: list[dict[str, Any]],
    ) -> str:
        """يولّد رسالة تحفيزية."""
        
        if profile.overall_mastery >= 0.8:
            return "ممتاز! أنت في مستوى متقدم. حافظ على التقدم! 🏆"
        elif profile.overall_mastery >= 0.6:
            msg = "أداء جيد! "
            if at_risk:
                msg += f"راجع {at_risk[0]['topic_name']} لتجنب النسيان."
            return msg + " 📚"
        elif profile.overall_mastery >= 0.4:
            return f"تحتاج تركيز على: {', '.join(profile.weaknesses[:2])}. لا تستسلم! 💪"
        else:
            return "ابدأ بالأساسيات. كل خطوة صغيرة تقربك من النجاح! 🌟"
    
    async def apply_decay(self, student_id: int) -> None:
        """يطبق منحنى النسيان على المواضيع غير المُمارَسة."""
        
        profile = await get_student_profile(student_id)
        now = datetime.now()
        
        for topic_id, tm in profile.topic_mastery.items():
            if tm.last_practiced is None:
                continue
            
            days_since = (now - tm.last_practiced).days
            
            if days_since > self.DECAY_DAYS:
                decay_periods = (days_since - self.DECAY_DAYS) // 7
                decay = decay_periods * self.DECAY_RATE
                new_score = max(0.1, tm.mastery_score - decay)  # minimum 10%
                
                if new_score < tm.mastery_score:
                    tm.mastery_score = new_score
                    logger.info(
                        f"Applied decay to student {student_id}, "
                        f"topic {topic_id}: {tm.mastery_score:.2f}"
                    )


# Singleton
_tracker: MasteryTracker | None = None


def get_mastery_tracker() -> MasteryTracker:
    """يحصل على متتبع الإتقان."""
    global _tracker
    if _tracker is None:
        _tracker = MasteryTracker()
    return _tracker
