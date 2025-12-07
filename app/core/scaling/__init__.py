"""
Horizontal scaling infrastructure.
"""

from app.core.scaling.health_checker import HealthChecker
from app.core.scaling.load_balancer import LoadBalancer
from app.core.scaling.service_registry import ServiceRegistry

__all__ = ["HealthChecker", "LoadBalancer", "ServiceRegistry"]
