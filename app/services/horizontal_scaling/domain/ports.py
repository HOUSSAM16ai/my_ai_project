"""
Horizontal Scaling Domain Ports
===============================

Interfaces (Protocols) for the Horizontal Scaling system.
Defines contracts for repositories and external services.
"""
from __future__ import annotations

from typing import Protocol, List, Optional
from .models import Server, ScalingMetrics, ScalingEvent, LoadBalancingAlgorithm


class LoadBalancerPort(Protocol):
    """Interface for load balancing operations."""

    def add_server(self, server: Server) -> None:
        ...

    def remove_server(self, server_id: str) -> None:
        ...

    def select_server(self, request_key: Optional[str] = None) -> Optional[Server]:
        ...

    def get_stats(self) -> dict:
        ...


class ServerRepositoryPort(Protocol):
    """Interface for persisting server state."""

    def save(self, server: Server) -> None:
        ...

    def get(self, server_id: str) -> Optional[Server]:
        ...

    def list_all(self) -> List[Server]:
        ...

    def delete(self, server_id: str) -> None:
        ...


class MetricsRepositoryPort(Protocol):
    """Interface for storing scaling metrics."""

    def save_metrics(self, metrics: ScalingMetrics) -> None:
        ...

    def get_latest(self) -> Optional[ScalingMetrics]:
        ...

    def get_history(self, limit: int = 100) -> List[ScalingMetrics]:
        ...
