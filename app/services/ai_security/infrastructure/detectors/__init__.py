"""
Infrastructure Detectors Module
===============================
Concrete threat detection implementations.
"""

from .behavioral_analyzer import SimpleBehavioralAnalyzer
from .ml_threat_detector import DeepLearningThreatDetector

__all__ = [
    "DeepLearningThreatDetector",
    "SimpleBehavioralAnalyzer",
]
