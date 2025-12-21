# app/services/adaptive/application/__init__.py
"""Application layer for adaptive microservices"""

from app.services.adaptive.application.health_monitor import PredictiveHealthMonitor
from app.services.adaptive.application.intelligent_router import IntelligentRouter
from app.services.adaptive.application.scaling_engine import AIScalingEngine

__all__ = [
    "AIScalingEngine",
    "IntelligentRouter",
    "PredictiveHealthMonitor",
]
