"""
خدمات التحليل التنبؤي (Analytics Services).
============================================

تتضمن:
- PredictiveAnalyzer: التنبؤ بنقاط الضعف
- PatternDetector: كشف أنماط الأخطاء

تتكامل مع:
- DSPy: لتحسين التنبؤات
- LlamaIndex: لتحليل تاريخ الطالب
"""

from app.services.analytics.pattern_detector import (
    ErrorPattern,
    PatternDetector,
    get_pattern_detector,
)
from app.services.analytics.predictive_analyzer import (
    PredictiveAnalyzer,
    StrugglePrediction,
    get_predictive_analyzer,
)

__all__ = [
    # Predictive Analyzer
    "PredictiveAnalyzer",
    "StrugglePrediction",
    "get_predictive_analyzer",
    # Pattern Detector
    "PatternDetector",
    "ErrorPattern",
    "get_pattern_detector",
]
