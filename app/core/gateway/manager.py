"""
Mesh Manager Module.
Handles the lifecycle and prioritization of Neural Nodes.
"""

import time
import logging
from typing import Protocol

from app.core.gateway.circuit_breaker import CircuitBreaker
from app.core.gateway.node import NeuralNode

logger = logging.getLogger(__name__)

class NodeRanker(Protocol):
    """Protocol for ranking nodes (Strategy Pattern)."""
    def get_ranked_nodes(self, prompt: str | None = None) -> list[str]: ...


class DefaultRanker:
    """Default ranking strategy: simple list order."""
    def __init__(self, nodes_map: dict[str, NeuralNode]):
        self._nodes_map = nodes_map

    def get_ranked_nodes(self, prompt: str | None = None) -> list[str]:
        return list(self._nodes_map.keys())


class NodeManager:
    """
    Manages the fleet of Neural Nodes.
    Responsibility: Initialization, Health Checking, Prioritization.
    """

    def __init__(
        self,
        primary_model: str,
        fallback_models: list[str],
        safety_net_model: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.primary_model = primary_model
        self.fallback_models = fallback_models
        self.safety_net_model = safety_net_model
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.nodes_map: dict[str, NeuralNode] = self._initialize_nodes()
        self.ranker: NodeRanker = DefaultRanker(self.nodes_map)

    def _initialize_nodes(self) -> dict[str, NeuralNode]:
        """Initialize all neural nodes with circuit breakers."""
        nodes = {}

        def create_breaker(name: str) -> CircuitBreaker:
            return CircuitBreaker(name, self.failure_threshold, self.recovery_timeout)

        # 1. Primary
        nodes[self.primary_model] = NeuralNode(
            model_id=self.primary_model,
            circuit_breaker=create_breaker("Primary-Cortex"),
        )

        # 2. Fallbacks
        for idx, model_id in enumerate(self.fallback_models):
            nodes[model_id] = NeuralNode(
                model_id=model_id,
                circuit_breaker=create_breaker(f"Backup-Synapse-{idx + 1}"),
            )

        # 3. Safety Net (Unbreakable)
        nodes[self.safety_net_model] = NeuralNode(
            model_id=self.safety_net_model,
            circuit_breaker=CircuitBreaker("Safety-Net", 999999, 1.0),
        )
        return nodes

    def get_prioritized_nodes(self, prompt: str) -> list[NeuralNode]:
        """
        Returns a healthy, prioritized list of nodes for execution.
        """
        final_nodes: list[NeuralNode] = []
        now = time.time()

        # 1. Get Ranked IDs
        try:
            ranked_models = self.ranker.get_ranked_nodes(prompt)
        except Exception as exc:
            logger.warning("Ranker failed; falling back to static order.", exc_info=exc)
            ranked_models = [
                self.primary_model,
                *self.fallback_models,
                self.safety_net_model
            ]

        # Ensure we only consider known nodes
        candidates = [m for m in ranked_models if m in self.nodes_map]

        # If ranker returned empty or invalid, fallback to defaults
        if not candidates:
             candidates = [
                self.primary_model,
                *self.fallback_models,
                self.safety_net_model
            ]

        # 2. Filter by Health
        for model_id in candidates:
            node = self.nodes_map.get(model_id)
            if not node:
                continue

            # Safety Net is always available
            if model_id == self.safety_net_model:
                final_nodes.append(node)
                continue

            # Check Circuit Breaker & Rate Limit
            if node.circuit_breaker.allow_request() and node.rate_limit_cooldown_until <= now:
                final_nodes.append(node)

        # 3. Ensure Safety Net is present as last resort if not already there
        safety_node = self.nodes_map.get(self.safety_net_model)
        if safety_node and safety_node not in final_nodes:
            final_nodes.append(safety_node)

        return final_nodes
