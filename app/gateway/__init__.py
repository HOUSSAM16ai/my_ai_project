"""
بوابة API المركزية (API Gateway).

يوفر هذا المكون نقطة دخول موحدة لجميع الخدمات المصغرة
مع دعم التوجيه، المصادقة، وتحديد المعدل.
"""

__all__ = [
    "APIGateway",
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "GatewayConfig",
    "ServiceDiscovery",
    "ServiceRegistry",
]

from app.gateway.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from app.gateway.config import GatewayConfig
from app.gateway.discovery import ServiceDiscovery
from app.gateway.gateway import APIGateway
from app.gateway.registry import ServiceRegistry
