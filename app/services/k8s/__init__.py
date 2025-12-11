# app/services/k8s/__init__.py
"""
Kubernetes Orchestration Service - Hexagonal Architecture

Backward compatible facade for kubernetes_orchestration_service.py
"""

from app.services.k8s.facade import (
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

__all__ = [
    "KubernetesOrchestrator",
    "get_kubernetes_orchestrator",
    "Pod",
    "Node",
    "PodPhase",
    "NodeState",
    "ConsensusRole",
    "ScalingDirection",
    "RaftState",
    "AutoScalingConfig",
    "SelfHealingEvent",
]
