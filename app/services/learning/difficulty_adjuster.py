"""
مُكيّف الصعوبة (Difficulty Adjuster).
=====================================

يكيّف صعوبة المحتوى التعليمي بناءً على مستوى الطالب.

المعايير:
- CS50 2025: توثيق عربي
- SICP: Procedural Abstraction
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from app.services.learning.student_profile import MasteryLevel, StudentProfile

logger = logging.getLogger(__name__)


class DifficultyLevel(StrEnum):
    """مستويات الصعوبة."""

    EASY = "easy"  # سهل (للمبتدئين)
    MEDIUM = "medium"  # متوسط (المستوى القياسي)
    HARD = "hard"  # صعب (للمتقدمين)
    CHALLENGE = "challenge"  # تحدي (للخبراء)


@dataclass
class DifficultyRecommendation:
    """توصية بمستوى الصعوبة."""

    level: DifficultyLevel
    reason: str
    topic_focus: list[str]
    suggested_hints: int


class DifficultyAdjuster:
    """
    يكيّف صعوبة المحتوى بناءً على أداء الطالب.

    الخوارزمية:
    1. يحلل إتقان الطالب للموضوع
    2. يحلل الأداء الأخير (آخر 5 محاولات)
    3. يحدد الصعوبة المناسبة
    4. يقترح عدد التلميحات
    """

    # جدول التعيين: (مستوى الإتقان × دقة أخيرة) → صعوبة
    ADJUSTMENT_MATRIX: ClassVar = {
        # (mastery_level, recent_accuracy) -> difficulty
        (MasteryLevel.NOVICE, "low"): DifficultyLevel.EASY,
        (MasteryLevel.NOVICE, "high"): DifficultyLevel.EASY,
        (MasteryLevel.DEVELOPING, "low"): DifficultyLevel.EASY,
        (MasteryLevel.DEVELOPING, "high"): DifficultyLevel.MEDIUM,
        (MasteryLevel.PROFICIENT, "low"): DifficultyLevel.MEDIUM,
        (MasteryLevel.PROFICIENT, "high"): DifficultyLevel.HARD,
        (MasteryLevel.EXPERT, "low"): DifficultyLevel.MEDIUM,
        (MasteryLevel.EXPERT, "high"): DifficultyLevel.CHALLENGE,
    }

    # عدد التلميحات المقترحة حسب الصعوبة
    HINTS_BY_DIFFICULTY: ClassVar = {
        DifficultyLevel.EASY: 3,
        DifficultyLevel.MEDIUM: 2,
        DifficultyLevel.HARD: 1,
        DifficultyLevel.CHALLENGE: 0,
    }

    def recommend(
        self,
        profile: StudentProfile,
        topic_id: str,
    ) -> DifficultyRecommendation:
        """
        يوصي بمستوى الصعوبة للطالب في موضوع معين.

        Args:
            profile: ملف الطالب
            topic_id: معرف الموضوع

        Returns:
            DifficultyRecommendation: التوصية
        """
        # 1. الحصول على مستوى الإتقان
        if topic_id in profile.topic_mastery:
            topic_mastery = profile.topic_mastery[topic_id]
            mastery_level = topic_mastery.level
            recent_accuracy = self._calculate_recent_accuracy(profile, topic_id)
        else:
            # موضوع جديد
            mastery_level = MasteryLevel.NOVICE
            recent_accuracy = "low"

        # 2. تحديد الصعوبة من المصفوفة
        accuracy_category = "high" if recent_accuracy >= 0.7 else "low"
        difficulty = self.ADJUSTMENT_MATRIX.get(
            (mastery_level, accuracy_category),
            DifficultyLevel.MEDIUM,
        )

        # 3. بناء التوصية
        reason = self._build_reason(mastery_level, recent_accuracy, difficulty)
        topic_focus = self._determine_focus_topics(profile, topic_id)
        hints = self.HINTS_BY_DIFFICULTY[difficulty]

        recommendation = DifficultyRecommendation(
            level=difficulty,
            reason=reason,
            topic_focus=topic_focus,
            suggested_hints=hints,
        )

        logger.info(
            f"Difficulty recommendation for student {profile.student_id} "
            f"on topic {topic_id}: {difficulty.value} "
            f"(mastery={mastery_level.value}, accuracy={recent_accuracy:.0%})"
        )

        return recommendation

    def _calculate_recent_accuracy(
        self,
        profile: StudentProfile,
        topic_id: str,
        window: int = 5,
    ) -> float:
        """يحسب الدقة في آخر N محاولات."""

        recent_events = [
            e
            for e in profile.learning_history[-20:]
            if e.topic_id == topic_id and e.event_type in ("correct", "wrong")
        ][-window:]

        if not recent_events:
            return 0.0

        correct = sum(1 for e in recent_events if e.event_type == "correct")
        return correct / len(recent_events)

    def _build_reason(
        self,
        mastery: MasteryLevel,
        accuracy: float,
        difficulty: DifficultyLevel,
    ) -> str:
        """يبني تفسير التوصية."""

        reasons = {
            DifficultyLevel.EASY: f"مستوى إتقانك ({mastery.value}) يحتاج تعزيز الأساسيات",
            DifficultyLevel.MEDIUM: f"مستواك مناسب للتمارين المتوسطة (دقة: {accuracy:.0%})",
            DifficultyLevel.HARD: f"أداؤك ممتاز! جاهز للتحديات (دقة: {accuracy:.0%})",
            DifficultyLevel.CHALLENGE: "أنت خبير! حان وقت التحديات الصعبة 🏆",
        }
        return reasons.get(difficulty, "")

    def _determine_focus_topics(
        self,
        profile: StudentProfile,
        current_topic: str,
    ) -> list[str]:
        """يحدد المواضيع التي يجب التركيز عليها."""

        focus = []

        # الموضوع الحالي
        if current_topic in profile.topic_mastery:
            tm = profile.topic_mastery[current_topic]
            if tm.mastery_score < 0.7:
                focus.append(tm.topic_name)

        # المواضيع الضعيفة المرتبطة
        for topic_id, tm in profile.topic_mastery.items():
            if tm.mastery_score < 0.5 and topic_id != current_topic:
                focus.append(tm.topic_name)
                if len(focus) >= 3:
                    break

        return focus

    def adjust_content(
        self,
        content: str,
        difficulty: DifficultyLevel,
    ) -> dict[str, object]:
        """
        يكيّف المحتوى حسب الصعوبة.

        Returns:
            dict: {
                "content": str,
                "show_hints": bool,
                "show_solution_steps": bool,
                "time_limit_multiplier": float,
            }
        """
        adjustments = {
            DifficultyLevel.EASY: {
                "content": content,
                "show_hints": True,
                "show_solution_steps": True,
                "time_limit_multiplier": 1.5,
            },
            DifficultyLevel.MEDIUM: {
                "content": content,
                "show_hints": True,
                "show_solution_steps": False,
                "time_limit_multiplier": 1.0,
            },
            DifficultyLevel.HARD: {
                "content": content,
                "show_hints": False,
                "show_solution_steps": False,
                "time_limit_multiplier": 0.8,
            },
            DifficultyLevel.CHALLENGE: {
                "content": content,
                "show_hints": False,
                "show_solution_steps": False,
                "time_limit_multiplier": 0.6,
            },
        }
        return adjustments.get(difficulty, adjustments[DifficultyLevel.MEDIUM])


# Singleton
_adjuster: DifficultyAdjuster | None = None


def get_difficulty_adjuster() -> DifficultyAdjuster:
    """يحصل على مكيّف الصعوبة."""
    global _adjuster
    if _adjuster is None:
        _adjuster = DifficultyAdjuster()
    return _adjuster
