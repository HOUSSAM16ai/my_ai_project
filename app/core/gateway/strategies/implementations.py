from abc import ABC, abstractmethod
from typing import Any

from app.core.gateway.models import RoutingStrategy


class BaseRoutingStrategy(ABC):
    @abstractmethod
    def calculate_scores(self, candidates: list[dict[str, Any]]) -> None:
        pass


class CostOptimizedStrategy(BaseRoutingStrategy):
    def calculate_scores(self, candidates: list[dict[str, Any]]) -> None:
        for c in candidates:
            c["score"] = 1.0 / (c["cost"] + 0.001)


class LatencyBasedStrategy(BaseRoutingStrategy):
    def calculate_scores(self, candidates: list[dict[str, Any]]) -> None:
        for c in candidates:
            c["score"] = 1.0 / (c["latency"] + 0.001)


class IntelligentRoutingStrategy(BaseRoutingStrategy):
    def calculate_scores(self, candidates: list[dict[str, Any]]) -> None:
        if not candidates:
            return

        min_cost = min(c["cost"] for c in candidates)
        max_cost = max(c["cost"] for c in candidates)
        cost_range = max_cost - min_cost if max_cost > min_cost else 1.0

        min_latency = min(c["latency"] for c in candidates)
        max_latency = max(c["latency"] for c in candidates)
        latency_range = max_latency - min_latency if max_latency > min_latency else 1.0

        for c in candidates:
            norm_cost = (c["cost"] - min_cost) / cost_range if cost_range > 0 else 0.0
            norm_latency = (
                (c["latency"] - min_latency) / latency_range if latency_range > 0 else 0.0
            )

            # Score: Higher is better.
            c["score"] = (
                (1.0 - norm_cost) * 0.3 + (1.0 - norm_latency) * 0.5 + c["health_score"] * 0.2
            )


class FallbackStrategy(BaseRoutingStrategy):
    def calculate_scores(self, candidates: list[dict[str, Any]]) -> None:
        for c in candidates:
            cost_score = 1.0 / (c["cost"] + 0.001)
            latency_score = 1.0 / (c["latency"] + 0.001)
            c["score"] = cost_score * 0.3 + latency_score * 0.5 + c["health_score"] * 0.2


STRATEGY_MAP = {
    RoutingStrategy.COST_OPTIMIZED: CostOptimizedStrategy(),
    RoutingStrategy.LATENCY_BASED: LatencyBasedStrategy(),
    RoutingStrategy.INTELLIGENT: IntelligentRoutingStrategy(),
}


def get_strategy(strategy_enum: RoutingStrategy) -> BaseRoutingStrategy:
    return STRATEGY_MAP.get(strategy_enum, FallbackStrategy())
