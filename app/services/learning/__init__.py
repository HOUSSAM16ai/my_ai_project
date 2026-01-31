"""
خدمات التعلم التكيفي (Learning Services).
==========================================

تتضمن:
- StudentProfile: ملف الطالب التعليمي
- DifficultyAdjuster: مكيّف الصعوبة
- MasteryTracker: متتبع الإتقان

تتكامل مع:
- LlamaIndex: لإثراء ملف الطالب بالسياق
- DSPy: لتحسين التوصيات
"""

from app.services.learning.difficulty_adjuster import (
    DifficultyAdjuster,
    DifficultyLevel,
    DifficultyRecommendation,
    get_difficulty_adjuster,
)
from app.services.learning.mastery_tracker import (
    MasteryTracker,
    MasteryTrend,
    get_mastery_tracker,
)
from app.services.learning.student_profile import (
    MasteryLevel,
    StudentProfile,
    TopicMastery,
    get_student_profile,
    save_student_profile,
)

__all__ = [
    # Student Profile
    "StudentProfile",
    "TopicMastery",
    "MasteryLevel",
    "get_student_profile",
    "save_student_profile",
    # Difficulty Adjuster
    "DifficultyAdjuster",
    "DifficultyLevel",
    "DifficultyRecommendation",
    "get_difficulty_adjuster",
    # Mastery Tracker
    "MasteryTracker",
    "MasteryTrend",
    "get_mastery_tracker",
]
