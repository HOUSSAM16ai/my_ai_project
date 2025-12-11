# app/services/kubernetes_orchestration_service.py
"""
Kubernetes Orchestration Service - LEGACY COMPATIBILITY
========================================================
This file now imports from the refactored orchestration module.

Original file: 715+ lines
Refactored: Delegates to orchestration/ module following Hexagonal Architecture

For new code, import from: app.services.orchestration
"""

# Legacy imports for backward compatibility
from app.services.orchestration import (
    AutoScalingConfig,
    ConsensusRole,
    KubernetesOrchestrator,
    Node,
    NodeState,
    Pod,
    PodPhase,
    RaftState,
    ScalingDirection,
    SelfHealingEvent,
    get_kubernetes_orchestrator,
)

# Re-export everything for backward compatibility
__all__ = [
    # Enums
    "PodPhase",
    "NodeState",
    "ConsensusRole",
    "ScalingDirection",
    # Models
    "Pod",
    "Node",
    "RaftState",
    "SelfHealingEvent",
    "AutoScalingConfig",
    # Service
    "KubernetesOrchestrator",
    "get_kubernetes_orchestrator",
]
