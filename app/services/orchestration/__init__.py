# app/services/orchestration/__init__.py
"""
Orchestration Module - Kubernetes Orchestration
================================================
Kubernetes orchestration service following Hexagonal Architecture.

Refactored from monolithic KubernetesOrchestrator (715 lines)
into clean layered architecture.

Architecture:
- Domain Layer: Pure business logic and entities
- Application Layer: Use cases and orchestration
- Infrastructure Layer: External adapters and persistence
"""

from app.services.orchestration.domain import (
    AutoScalingConfig,
    ConsensusRole,
    Node,
    NodeState,
    Pod,
    PodPhase,
    RaftState,
    ScalingDirection,
    SelfHealingEvent,
)

__all__ = [
    # Domain models
    "AutoScalingConfig",
    "ConsensusRole",
    "Node",
    "NodeState",
    "Pod",
    "PodPhase",
    "RaftState",
    "ScalingDirection",
    "SelfHealingEvent",
]
