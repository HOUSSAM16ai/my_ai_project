"""
بوابة الذكاء الاصطناعي (AI Gateway).

يعمل هذا الملف كواجهة (Facade) للوحدات الذرية الموجودة في `app/core/gateway/`.
يحافظ على التوافق مع الإصدارات السابقة مع تطبيق SRP عبر البنية الجديدة.

المبادئ (Principles):
- Harvard CS50 2025: توثيق عربي، صرامة الأنواع
- Berkeley SICP: Abstraction Barriers (الواجهة تخفي التعقيد)
- SOLID: Facade Pattern (واجهة مبسطة لنظام معقد)

الاستخدام (Usage):
    client = get_ai_client()
    response = await client.generate("prompt")
"""

import logging
from typing import Any

from app.core.gateway.circuit_breaker import CircuitBreaker, CircuitState
from app.core.gateway.connection import ConnectionManager

# --- Import Atomic Modules ---
from app.core.gateway.exceptions import (
    AIAllModelsExhaustedError,
    AICircuitOpenError,
    AIConnectionError,
    AIError,
    AIProviderError,
    AIRateLimitError,
)
from app.core.gateway.mesh import AIClient, NeuralRoutingMesh, get_ai_client
from app.core.gateway.node import NeuralNode
from app.core.superhuman_performance_optimizer import get_performance_optimizer

# Re-export key components for backward compatibility
__all__ = [
    "AIAllModelsExhaustedError",
    "AICircuitOpenError",
    "AIClient",
    "AIConnectionError",
    "AIError",
    "AIProviderError",
    "AIRateLimitError",
    "CircuitBreaker",
    "CircuitState",
    "ConnectionManager",
    "NeuralNode",
    "NeuralRoutingMesh",
    "get_ai_client",
    "ai_gateway",
    "get_performance_report",
    "get_recommended_model",
]

logger = logging.getLogger(__name__)
_performance_optimizer = get_performance_optimizer()


def get_performance_report() -> dict[str, "Any"]:
    """
    الحصول على تقرير أداء شامل من محسن الأداء.
    
    يفوض العملية إلى خدمة المحسن (Optimizer Service).
    
    Returns:
        تقرير مفصل عن أداء النماذج المختلفة
    """
    return _performance_optimizer.get_detailed_report()


def get_recommended_model(available_models: list[str], context: str = "") -> str:
    """
    الحصول على النموذج الموصى به بناءً على الأداء التاريخي.
    
    يستخدم الذكاء الاصطناعي لاختيار أفضل نموذج بناءً على السياق والأداء السابق.
    
    Args:
        available_models: قائمة النماذج المتاحة
        context: السياق الحالي (اختياري)
        
    Returns:
        اسم النموذج الموصى به
    """
    return _performance_optimizer.get_recommended_model(available_models, context)

class AIGatewayFacade:
    """Facade for AI Gateway operations."""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> AIClient:
        if not self._client:
            self._client = get_ai_client()
        return self._client

    async def generate_text(self, prompt: str, **kwargs) -> Any:
        return await self.client.generate_text(prompt, **kwargs)

    async def forge_new_code(self, **kwargs) -> Any:
        return await self.client.forge_new_code(**kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)

# Singleton instance
ai_gateway = AIGatewayFacade()
