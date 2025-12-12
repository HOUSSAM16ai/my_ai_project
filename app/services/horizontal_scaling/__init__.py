"""
Horizontal Scaling Service Package
==================================

Hexagonal Architecture Implementation.
"""
from .domain.models import (
    LoadBalancingAlgorithm,
    ServerState,
    ScalingEvent,
    RegionZone,
    Server,
    ScalingMetrics,
    ConsistentHashNode,
)
from .application.manager import HorizontalScalingManager
from .application.chaos_monkey import ChaosMonkey
from .application.load_balancer import LoadBalancerStrategy as LoadBalancer
from .facade import get_scaling_orchestrator

# Re-export key components to match original API
HorizontalScalingOrchestrator = HorizontalScalingManager

__all__ = [
    "LoadBalancingAlgorithm",
    "ServerState",
    "ScalingEvent",
    "RegionZone",
    "Server",
    "ScalingMetrics",
    "ConsistentHashNode",
    "HorizontalScalingOrchestrator",
    "ChaosMonkey",
    "LoadBalancer",
    "get_scaling_orchestrator",
]
