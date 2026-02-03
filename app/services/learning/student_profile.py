"""
ملف الطالب التعليمي (Student Profile).
======================================

يتتبع مستوى الطالب، نقاط قوته وضعفه، وتاريخ تعلمه.

المعايير:
- CS50 2025: توثيق عربي
- SICP: Data Abstraction
"""

import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MasteryLevel(StrEnum):
    """مستويات الإتقان."""

    NOVICE = "novice"  # مبتدئ (0-25%)
    DEVELOPING = "developing"  # متطور (25-50%)
    PROFICIENT = "proficient"  # متقن (50-75%)
    EXPERT = "expert"  # خبير (75-100%)


class TopicMastery(BaseModel):
    """إتقان موضوع معين."""

    topic_id: str = Field(..., description="معرف الموضوع")
    topic_name: str = Field(..., description="اسم الموضوع")
    mastery_score: float = Field(0.0, ge=0.0, le=1.0, description="درجة الإتقان")
    attempts: int = Field(0, description="عدد المحاولات")
    correct_count: int = Field(0, description="عدد الإجابات الصحيحة")
    last_practiced: datetime | None = Field(None, description="آخر ممارسة")

    @property
    def level(self) -> MasteryLevel:
        """يحسب مستوى الإتقان."""
        if self.mastery_score < 0.25:
            return MasteryLevel.NOVICE
        if self.mastery_score < 0.50:
            return MasteryLevel.DEVELOPING
        if self.mastery_score < 0.75:
            return MasteryLevel.PROFICIENT
        return MasteryLevel.EXPERT

    @property
    def accuracy(self) -> float:
        """يحسب نسبة الدقة."""
        if self.attempts == 0:
            return 0.0
        return self.correct_count / self.attempts


class LearningEvent(BaseModel):
    """حدث تعليمي (محاولة، إجابة، إلخ)."""

    timestamp: datetime = Field(default_factory=datetime.now)
    topic_id: str
    event_type: str = Field(..., description="نوع الحدث: attempt, correct, wrong, hint")
    content_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class StudentProfile(BaseModel):
    """
    ملف الطالب التعليمي الكامل.

    يتتبع:
    - إتقان المواضيع المختلفة
    - نقاط القوة والضعف
    - تاريخ التعلم
    - التفضيلات
    """

    student_id: int = Field(..., description="معرف الطالب")
    name: str = Field("", description="اسم الطالب")
    grade_level: str = Field("ثالثة ثانوي", description="المستوى الدراسي")
    branch: str = Field("علوم تجريبية", description="الشعبة")

    # إتقان المواضيع
    topic_mastery: dict[str, TopicMastery] = Field(default_factory=dict)

    # نقاط القوة والضعف
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    # تاريخ التعلم
    learning_history: list[LearningEvent] = Field(default_factory=list)

    # التفضيلات
    preferred_difficulty: str = Field("متوسط", description="الصعوبة المفضلة")
    preferred_style: str = Field("شرح مفصل", description="أسلوب الشرح المفضل")

    # إحصائيات
    total_attempts: int = Field(0)
    total_correct: int = Field(0)
    total_time_spent_minutes: int = Field(0)

    @property
    def overall_mastery(self) -> float:
        """يحسب الإتقان العام."""
        if not self.topic_mastery:
            return 0.0
        scores = [tm.mastery_score for tm in self.topic_mastery.values()]
        return sum(scores) / len(scores)

    @property
    def overall_accuracy(self) -> float:
        """يحسب الدقة الإجمالية."""
        if self.total_attempts == 0:
            return 0.0
        return self.total_correct / self.total_attempts

    def record_attempt(
        self,
        topic_id: str,
        topic_name: str,
        is_correct: bool,
        content_id: str | None = None,
    ) -> None:
        """يسجل محاولة حل."""

        # تحديث إتقان الموضوع
        if topic_id not in self.topic_mastery:
            self.topic_mastery[topic_id] = TopicMastery(
                topic_id=topic_id,
                topic_name=topic_name,
            )

        tm = self.topic_mastery[topic_id]
        tm.attempts += 1
        if is_correct:
            tm.correct_count += 1
        tm.last_practiced = datetime.now()

        # إعادة حساب الإتقان باستخدام ELO-like formula
        if is_correct:
            tm.mastery_score = min(1.0, tm.mastery_score + 0.1 * (1 - tm.mastery_score))
        else:
            tm.mastery_score = max(0.0, tm.mastery_score - 0.05)

        # تحديث الإحصائيات الإجمالية
        self.total_attempts += 1
        if is_correct:
            self.total_correct += 1

        # تسجيل الحدث
        event = LearningEvent(
            topic_id=topic_id,
            event_type="correct" if is_correct else "wrong",
            content_id=content_id,
        )
        self.learning_history.append(event)

        # تحديث نقاط القوة والضعف
        self._update_strengths_weaknesses()

        logger.info(
            f"Recorded attempt for student {self.student_id}: "
            f"topic={topic_id}, correct={is_correct}, "
            f"new_mastery={tm.mastery_score:.2f}"
        )

    def _update_strengths_weaknesses(self) -> None:
        """يحدّث نقاط القوة والضعف."""

        if not self.topic_mastery:
            return

        sorted_topics = sorted(
            self.topic_mastery.items(),
            key=lambda x: x[1].mastery_score,
            reverse=True,
        )

        # أقوى 3 مواضيع
        self.strengths = [tm.topic_name for _, tm in sorted_topics[:3] if tm.mastery_score >= 0.6]

        # أضعف 3 مواضيع
        self.weaknesses = [tm.topic_name for _, tm in sorted_topics[-3:] if tm.mastery_score < 0.5]

    def get_recommended_topics(self, limit: int = 5) -> list[str]:
        """يقترح مواضيع للمراجعة بناءً على الضعف."""

        # المواضيع الضعيفة أولاً
        weak_topics = [
            (topic_id, tm) for topic_id, tm in self.topic_mastery.items() if tm.mastery_score < 0.6
        ]

        # ترتيب حسب الأولوية: الأضعف + الأقدم ممارسة
        weak_topics.sort(key=lambda x: (x[1].mastery_score, x[1].last_practiced or datetime.min))

        return [tm.topic_name for _, tm in weak_topics[:limit]]

    def to_brief(self) -> str:
        """يحوّل الملف لنص موجز للسياق."""

        lines = [
            f"👤 الطالب: {self.name or f'#{self.student_id}'}",
            f"📚 المستوى: {self.grade_level} - {self.branch}",
            f"📊 الإتقان العام: {self.overall_mastery:.0%}",
            f"🎯 الدقة: {self.overall_accuracy:.0%}",
        ]

        if self.strengths:
            lines.append(f"💪 نقاط القوة: {', '.join(self.strengths)}")

        if self.weaknesses:
            lines.append(f"⚠️ يحتاج تحسين: {', '.join(self.weaknesses)}")

        return "\n".join(lines)


# Cache for student profiles (in production, use Redis or DB)
_profile_cache: dict[int, StudentProfile] = {}


async def get_student_profile(student_id: int) -> StudentProfile:
    """يجلب أو ينشئ ملف طالب."""

    if student_id not in _profile_cache:
        # في الإنتاج: جلب من قاعدة البيانات
        _profile_cache[student_id] = StudentProfile(student_id=student_id)

    return _profile_cache[student_id]


async def save_student_profile(profile: StudentProfile) -> None:
    """يحفظ ملف الطالب."""

    _profile_cache[profile.student_id] = profile
    # في الإنتاج: حفظ في قاعدة البيانات
    logger.info(f"Saved profile for student {profile.student_id}")
