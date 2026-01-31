"""
كاشف أنماط الأخطاء (Pattern Detector).
======================================

يحلل أخطاء الطالب لاكتشاف الأنماط المتكررة.
"""

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import ClassVar

from app.services.learning.student_profile import get_student_profile

logger = logging.getLogger(__name__)


@dataclass
class ErrorPattern:
    """نمط خطأ مكتشف."""

    pattern_type: str
    description: str
    frequency: int
    affected_topics: list[str]
    example_errors: list[str]
    remediation: str


class PatternDetector:
    """
    يكتشف أنماط الأخطاء المتكررة.

    الأنماط المكتشفة:
    - أخطاء حسابية متكررة
    - سوء فهم مفاهيم
    - تخطي خطوات
    - أخطاء إشارات
    """

    # أنماط الأخطاء المعروفة
    KNOWN_PATTERNS: ClassVar = {
        "calculation": {
            "description": "أخطاء في العمليات الحسابية",
            "keywords": ["حساب", "ضرب", "قسمة", "جمع", "طرح"],
            "remediation": "تدرب على العمليات الأساسية وتحقق من إجاباتك",
        },
        "sign_errors": {
            "description": "أخطاء في الإشارات (+ / -)",
            "keywords": ["إشارة", "سالب", "موجب"],
            "remediation": "انتبه للإشارات في كل خطوة",
        },
        "concept_confusion": {
            "description": "خلط بين المفاهيم",
            "keywords": ["خلط", "فرق", "مشابه"],
            "remediation": "ارسم جدول مقارنة بين المفاهيم المتشابهة",
        },
        "incomplete_steps": {
            "description": "تخطي خطوات في الحل",
            "keywords": ["ناقص", "خطوة", "نسيت"],
            "remediation": "اكتب كل الخطوات حتى لو بدت بديهية",
        },
        "formula_errors": {
            "description": "استخدام خاطئ للصيغ",
            "keywords": ["صيغة", "قانون", "معادلة"],
            "remediation": "راجع الصيغ وتأكد من شروط استخدامها",
        },
    }

    async def detect_patterns(
        self,
        student_id: int,
        days: int = 30,
    ) -> list[ErrorPattern]:
        """
        يكشف أنماط الأخطاء للطالب.
        """
        profile = await get_student_profile(student_id)
        cutoff = datetime.now() - timedelta(days=days)

        # جمع الأخطاء
        errors = [
            e for e in profile.learning_history if e.event_type == "wrong" and e.timestamp >= cutoff
        ]

        if not errors:
            return []

        # تحليل الأنماط
        patterns = []

        # تحليل المواضيع الأكثر أخطاءً
        topic_errors = Counter(e.topic_id for e in errors)

        for topic_id, count in topic_errors.most_common(5):
            if count >= 3:  # 3 أخطاء أو أكثر
                topic_name = profile.topic_mastery.get(topic_id)
                topic_name = topic_name.topic_name if topic_name else topic_id

                patterns.append(
                    ErrorPattern(
                        pattern_type="recurring_topic",
                        description=f"أخطاء متكررة في {topic_name}",
                        frequency=count,
                        affected_topics=[topic_name],
                        example_errors=[],
                        remediation=f"ركز على فهم أساسيات {topic_name}",
                    )
                )

        # تحليل تسلسل الأخطاء
        consecutive = self._find_consecutive_errors(errors)
        if consecutive >= 3:
            patterns.append(
                ErrorPattern(
                    pattern_type="consecutive_errors",
                    description="أخطاء متتالية تشير لإحباط",
                    frequency=consecutive,
                    affected_topics=[],
                    example_errors=[],
                    remediation="خذ استراحة ثم عد بذهن صافٍ",
                )
            )

        logger.info(f"Detected {len(patterns)} error patterns for student {student_id}")

        return patterns

    def _find_consecutive_errors(self, errors: list) -> int:
        """يجد أطول سلسلة أخطاء متتالية."""

        if not errors:
            return 0

        # ترتيب حسب الوقت
        sorted_errors = sorted(errors, key=lambda e: e.timestamp)

        max_consecutive = 1
        current = 1

        for i in range(1, len(sorted_errors)):
            # إذا كان الفارق أقل من ساعة، نعتبرها متتالية
            diff = (sorted_errors[i].timestamp - sorted_errors[i - 1].timestamp).total_seconds()
            if diff < 3600:  # ساعة
                current += 1
                max_consecutive = max(max_consecutive, current)
            else:
                current = 1

        return max_consecutive

    async def get_improvement_plan(
        self,
        student_id: int,
    ) -> dict:
        """يولّد خطة تحسين بناءً على الأنماط."""

        patterns = await self.detect_patterns(student_id)
        profile = await get_student_profile(student_id)

        plan = {
            "student_id": student_id,
            "patterns_found": len(patterns),
            "focus_areas": [],
            "daily_goals": [],
            "weekly_goals": [],
        }

        # مناطق التركيز
        for pattern in patterns[:3]:
            plan["focus_areas"].append(
                {
                    "area": pattern.description,
                    "action": pattern.remediation,
                }
            )

        # أهداف يومية
        if profile.weaknesses:
            plan["daily_goals"].append(f"حل تمرين واحد في {profile.weaknesses[0]}")
        plan["daily_goals"].append("مراجعة 10 دقائق")

        # أهداف أسبوعية
        plan["weekly_goals"].append("إكمال 5 تمارين بنجاح")
        if patterns:
            plan["weekly_goals"].append(f"التغلب على: {patterns[0].description}")

        return plan


# Singleton
_detector: PatternDetector | None = None


def get_pattern_detector() -> PatternDetector:
    """يحصل على كاشف الأنماط."""
    global _detector
    if _detector is None:
        _detector = PatternDetector()
    return _detector
