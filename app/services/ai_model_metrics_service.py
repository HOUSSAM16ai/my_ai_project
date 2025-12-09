# app/services/ai_model_metrics_service.py
# ======================================================================================
# ==      AI MODEL METRICS SERVICE - TECH GIANTS STANDARD (v1.0 SUPERHUMAN)       ==
# ======================================================================================
"""
خدمة قياس نماذج الذكاء الاصطناعي - AI Model Metrics Service
(Compatibility Layer for Refactored Service)
"""

# Re-export everything from the new location to maintain backward compatibility
from app.services.metrics.types import (
    MetricType,
    ModelType,
    DriftStatus,
    InferenceMetrics,
    AccuracyMetrics,
    NLPMetrics,
    LatencyMetrics,
    CostMetrics,
    ModelDriftMetrics,
    FairnessMetrics,
    ModelPerformanceSnapshot,
)
from app.services.metrics.service import AIModelMetricsService, get_ai_model_service

__all__ = [
    "MetricType",
    "ModelType",
    "DriftStatus",
    "InferenceMetrics",
    "AccuracyMetrics",
    "NLPMetrics",
    "LatencyMetrics",
    "CostMetrics",
    "ModelDriftMetrics",
    "FairnessMetrics",
    "ModelPerformanceSnapshot",
    "AIModelMetricsService",
    "get_ai_model_service",
]
