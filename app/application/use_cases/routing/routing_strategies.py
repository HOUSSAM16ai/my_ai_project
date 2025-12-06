"""Routing strategies using Strategy Pattern."""

import random
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.core.interfaces.strategy_interface import StrategyInterface


@dataclass
class ServiceEndpoint:
    """Service endpoint information."""

    id: str
    url: str
    weight: float = 1.0
    active_connections: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    health_score: float = 1.0
    last_health_check: float = 0.0


@dataclass
class RoutingRequest:
    """Request to be routed."""

    request_id: str
    method: str
    path: str
    headers: dict[str, str]
    body: Any = None
    metadata: dict[str, Any] | None = None


class RoutingStrategy(StrategyInterface[RoutingRequest, ServiceEndpoint], ABC):
    """Base routing strategy."""

    def __init__(self, endpoints: list[ServiceEndpoint]):
        self.endpoints = endpoints
        self._current_index = 0

    @abstractmethod
    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select endpoint for request."""

    def is_applicable(self, context: dict[str, Any]) -> bool:
        """Check if strategy is applicable."""
        return len(self.endpoints) > 0


class RoundRobinStrategy(RoutingStrategy):
    """Round-robin routing strategy."""

    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select next endpoint in rotation."""
        if not self.endpoints:
            raise ValueError("No endpoints available")

        endpoint = self.endpoints[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.endpoints)
        return endpoint

    def get_name(self) -> str:
        return "round_robin"


class LeastConnectionsStrategy(RoutingStrategy):
    """Least connections routing strategy."""

    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select endpoint with fewest active connections."""
        if not self.endpoints:
            raise ValueError("No endpoints available")

        return min(self.endpoints, key=lambda e: e.active_connections)

    def get_name(self) -> str:
        return "least_connections"


class WeightedStrategy(RoutingStrategy):
    """Weighted random routing strategy."""

    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select endpoint based on weights."""
        if not self.endpoints:
            raise ValueError("No endpoints available")

        total_weight = sum(e.weight for e in self.endpoints)
        rand_val = random.uniform(0, total_weight)

        cumulative = 0.0
        for endpoint in self.endpoints:
            cumulative += endpoint.weight
            if rand_val <= cumulative:
                return endpoint

        return self.endpoints[-1]

    def get_name(self) -> str:
        return "weighted"


class LatencyBasedStrategy(RoutingStrategy):
    """Latency-based routing strategy."""

    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select endpoint with lowest latency."""
        if not self.endpoints:
            raise ValueError("No endpoints available")

        return min(self.endpoints, key=lambda e: e.avg_latency_ms)

    def get_name(self) -> str:
        return "latency_based"


class HealthAwareStrategy(RoutingStrategy):
    """Health-aware routing strategy."""

    def __init__(self, endpoints: list[ServiceEndpoint], health_threshold: float = 0.5):
        super().__init__(endpoints)
        self.health_threshold = health_threshold

    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select healthy endpoint with best score."""
        if not self.endpoints:
            raise ValueError("No endpoints available")

        healthy_endpoints = [e for e in self.endpoints if e.health_score >= self.health_threshold]

        if not healthy_endpoints:
            healthy_endpoints = self.endpoints

        return max(healthy_endpoints, key=lambda e: e.health_score)

    def get_name(self) -> str:
        return "health_aware"


class IntelligentStrategy(RoutingStrategy):
    """ML-based intelligent routing strategy."""

    def __init__(self, endpoints: list[ServiceEndpoint]):
        super().__init__(endpoints)
        self._performance_history: dict[str, list[float]] = defaultdict(list)

    def execute(self, request: RoutingRequest) -> ServiceEndpoint:
        """Select endpoint using ML-based prediction."""
        if not self.endpoints:
            raise ValueError("No endpoints available")

        scores = []
        for endpoint in self.endpoints:
            score = self._calculate_score(endpoint, request)
            scores.append((score, endpoint))

        return max(scores, key=lambda x: x[0])[1]

    def _calculate_score(self, endpoint: ServiceEndpoint, request: RoutingRequest) -> float:
        """Calculate endpoint score based on multiple factors."""
        latency_score = 1.0 / (1.0 + endpoint.avg_latency_ms / 100.0)
        health_score = endpoint.health_score
        load_score = 1.0 / (1.0 + endpoint.active_connections / 10.0)

        history = self._performance_history.get(endpoint.id, [])
        history_score = sum(history[-10:]) / len(history) if history else 0.5

        return (
            0.3 * latency_score + 0.3 * health_score + 0.2 * load_score + 0.2 * history_score
        )

    def record_performance(self, endpoint_id: str, success: bool):
        """Record endpoint performance for learning."""
        score = 1.0 if success else 0.0
        self._performance_history[endpoint_id].append(score)

        if len(self._performance_history[endpoint_id]) > 100:
            self._performance_history[endpoint_id] = self._performance_history[endpoint_id][-100:]

    def get_name(self) -> str:
        return "intelligent"


class StrategyFactory:
    """Factory for creating routing strategies."""

    _strategies = {
        "round_robin": RoundRobinStrategy,
        "least_connections": LeastConnectionsStrategy,
        "weighted": WeightedStrategy,
        "latency_based": LatencyBasedStrategy,
        "health_aware": HealthAwareStrategy,
        "intelligent": IntelligentStrategy,
    }

    @classmethod
    def create(cls, strategy_name: str, endpoints: list[ServiceEndpoint]) -> RoutingStrategy:
        """Create routing strategy by name."""
        strategy_class = cls._strategies.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        return strategy_class(endpoints)

    @classmethod
    def register(cls, name: str, strategy_class: type[RoutingStrategy]):
        """Register custom strategy."""
        cls._strategies[name] = strategy_class

    @classmethod
    def list_strategies(cls) -> list[str]:
        """List available strategies."""
        return list(cls._strategies.keys())
