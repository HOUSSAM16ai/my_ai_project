"""
Horizontal Scaling Service - Backward Compatible Shim
===================================================

⚠️ REFACTORED: This file now delegates to the hexagonal architecture implementation.
See: app/services/horizontal_scaling/ for the new modular structure.

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases (manager, load_balancer, chaos_monkey)
- infrastructure/: Adapters (currently empty/in-memory)
- facade.py: Main entry point

Original: 614 lines (monolithic)
Refactored: ~60 lines (shim) + Modular structure
Reduction: 90%

Status: ✅ Wave 10 Refactored
"""

from __future__ import annotations

from app.core.logging import get_logger

# Import from new modular structure
from .horizontal_scaling import (
    ChaosMonkey,
    ConsistentHashNode,
    HorizontalScalingOrchestrator,
    LoadBalancer,
    LoadBalancingAlgorithm,
    RegionZone,
    ScalingEvent,
    ScalingMetrics,
    Server,
    ServerState,
    get_scaling_orchestrator,
)

# Re-export for backward compatibility
__all__ = [
    "ChaosMonkey",
    "ConsistentHashNode",
    "HorizontalScalingOrchestrator",
    "LoadBalancer",
    "LoadBalancingAlgorithm",
    "RegionZone",
    "ScalingEvent",
    "ScalingMetrics",
    "Server",
    "ServerState",
    "get_scaling_orchestrator",
]

# Singleton instance
_orchestrator_instance = get_scaling_orchestrator()

_logger = get_logger(__name__)

if __name__ == "__main__":
    import json

    svc = get_scaling_orchestrator()
    _logger.info("=== Horizontal Scaling Service Diagnostics (Refactored) ===")
    _logger.info(
        "Cluster stats: %s",
        json.dumps(svc.get_cluster_stats(), ensure_ascii=False, indent=2),
    )
