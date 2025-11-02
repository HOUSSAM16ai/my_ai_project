# app/analysis/__init__.py
# ======================================================================================
# ==           SUPERHUMAN ANALYSIS ENGINE (v1.0 - ML-POWERED EDITION)               ==
# ======================================================================================
"""
محرك التحليل الخارق - Superhuman Analysis Engine

Features surpassing tech giants:
- Real-time anomaly detection (better than DataDog)
- Advanced pattern recognition
- Predictive analytics with ML
- Root cause analysis
- Automated insights
"""

from app.analysis.anomaly_detector import AnomalyDetector
from app.analysis.pattern_recognizer import PatternRecognizer
from app.analysis.predictor import PredictiveAnalytics
from app.analysis.root_cause import RootCauseAnalyzer

__all__ = [
    "AnomalyDetector",
    "PatternRecognizer",
    "PredictiveAnalytics",
    "RootCauseAnalyzer",
]
