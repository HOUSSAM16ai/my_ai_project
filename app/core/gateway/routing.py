from typing import Any

import logging
import threading
from collections import deque
from datetime import UTC, datetime

from .models import LoadBalancerState, ProtocolType, RoutingDecision, RoutingStrategy
from .providers.anthropic import AnthropicAdapter
from .providers.base import ModelProviderAdapter
from .providers.openai import OpenAIAdapter
from .strategies.implementations import get_strategy

logger = logging.getLogger(__name__)

class SuperCircuitBreaker:
    """
    قاطع الدائرة الخارق - Super Circuit Breaker
    Prevents cascading failures in the network surface.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state: dict[str, dict[str, Any]] = {}
        self.lock = threading.RLock()

    def report_failure(self, service_id: str) -> None:
        with self.lock:
            if service_id not in self.state:
                self.state[service_id] = {
                    "failures": 0,
                    "last_failure": None,
                    "open": False,
                }
            self.state[service_id]["failures"] += 1
            self.state[service_id]["last_failure"] = datetime.now(UTC)

            if self.state[service_id]["failures"] >= self.failure_threshold:
                self.state[service_id]["open"] = True
                logger.warning(
                    f"Circuit Breaker OPEN for {service_id}. Failures: {self.state[service_id]['failures']}"
                )

    def report_success(self, service_id: str) -> None:
        with self.lock:
            if service_id in self.state:
                self.state[service_id]["failures"] = 0
                self.state[service_id]["open"] = False

    def is_open(self, service_id: str) -> bool:
        with self.lock:
            if service_id not in self.state:
                return False
            if not self.state[service_id]["open"]:
                return False

            # Check if recovery timeout has passed
            last_failure = self.state[service_id].get("last_failure")
            if last_failure:
                elapsed = (datetime.now(UTC) - last_failure).total_seconds()
                if elapsed > self.recovery_timeout:
                    # Half-open state - allow one request to try
                    logger.info(f"Circuit Breaker HALF-OPEN for {service_id}")
                    return False
            return True

class IntelligentRouter:
    """
    محرك التوجيه الذكي - Intelligent routing engine

    Features:
    - Cost-aware routing
    - Latency-optimized routing
    - Load balancing across providers
    - Super Circuit Breaker integration
    - Predictive routing based on historical data
    """

    def __init__(self):
        self.provider_adapters: dict[str, ModelProviderAdapter] = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
        }
        self.routing_history: deque = deque(maxlen=10000)
        self.circuit_breaker = SuperCircuitBreaker()

        # Correctly handle dynamic LoadBalancerState initialization
        # We use a custom dict that initializes missing keys with the key as service_id
        class AutoInitDict(dict):
            def __missing__(self, key):
                value = LoadBalancerState(service_id=str(key))
                self[key] = value
                return value

        self.provider_stats: dict[str, LoadBalancerState] = AutoInitDict()
        self.lock = threading.RLock()

    # TODO: Split this function (39 lines) - KISS principle
    def _evaluate_candidates(
        self, model_type: str, estimated_tokens: int, constraints: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Filter and prepare candidates based on basic constraints."""
        max_cost = constraints.get("max_cost", float("inf"))
        max_latency = constraints.get("max_latency", float("inf"))
        candidates = []

        for provider_name, adapter in self.provider_adapters.items():
            # Check Circuit Breaker
            if self.circuit_breaker.is_open(provider_name):
                logger.warning(f"Skipping {provider_name} due to open circuit.")
                continue

            try:
                cost = adapter.estimate_cost(model_type, estimated_tokens)
                latency = adapter.estimate_latency(model_type, estimated_tokens)

                # Check constraints
                if cost > max_cost or latency > max_latency:
                    continue

                # Get provider health
                with self.lock:
                    stats = self.provider_stats[provider_name]
                health_score = 1.0 if stats.is_healthy else 0.0

                candidates.append(
                    {
                        "provider": provider_name,
                        "cost": cost,
                        "latency": latency,
                        "health_score": health_score,
                    }
                )

            except Exception as e:
                logger.warning(f"Error evaluating provider {provider_name}: {e}")
                continue
        return candidates
    def _apply_strategy_and_select_best(
        self, candidates: list[dict[str, Any]], strategy: RoutingStrategy
    ) -> dict[str, Any]:
        """Apply the routing strategy and select the best candidate."""
        strategy_impl = get_strategy(strategy)
        strategy_impl.calculate_scores(candidates)
        return max(candidates, key=lambda x: x["score"])

    def _create_routing_decision(
        self,
        best_candidate: dict[str, Any],
        strategy: RoutingStrategy,
        candidate_count: int,
    ) -> RoutingDecision:
        """Create a RoutingDecision object from the best candidate."""
        return RoutingDecision(
            service_id=str(best_candidate["provider"]),
            base_url=f"https://api.{best_candidate['provider']}.com",  # Placeholder
            protocol=ProtocolType.REST,
            estimated_latency_ms=float(best_candidate["latency"]),
            estimated_cost=float(best_candidate["cost"]),
            confidence_score=float(best_candidate["score"]),
            reasoning=f"Selected {best_candidate['provider']} based on {strategy.value} strategy",
            metadata={"all_candidates": candidate_count},
        )

    def _record_decision(
        self,
        decision: RoutingDecision,
        model_type: str,
        estimated_tokens: int,
    ) -> None:
        """Record the routing decision in history."""
        with self.lock:
            self.routing_history.append(
                {
                    "timestamp": datetime.now(UTC),
                    "decision": decision,
                    "model_type": model_type,
                    "tokens": estimated_tokens,
                }
            )

    def route_request(
        self,
        model_type: str,
        estimated_tokens: int,
        strategy: RoutingStrategy = RoutingStrategy.INTELLIGENT,
        constraints: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """
        توجيه ذكي للطلبات - Intelligent request routing

        Args:
            model_type: Type of model needed (e.g., 'gpt-4', 'claude-3')
            estimated_tokens: Estimated token count
            strategy: Routing strategy to use
            constraints: Additional constraints (max_cost, max_latency, etc.)

        Returns:
            RoutingDecision with selected provider and reasoning
        """
        constraints = constraints or {}
        candidates = self._evaluate_candidates(model_type, estimated_tokens, constraints)

        if not candidates:
            raise ValueError("No suitable provider found for routing (or all circuits open)")

        best_candidate = self._apply_strategy_and_select_best(candidates, strategy)
        decision = self._create_routing_decision(best_candidate, strategy, len(candidates))
        self._record_decision(decision, model_type, estimated_tokens)

        return decision

    def update_provider_stats(self, provider: str, success: bool, latency_ms: float) -> None:
        """Update provider statistics after request"""
        # Update Circuit Breaker
        if success:
            self.circuit_breaker.report_success(provider)
        else:
            self.circuit_breaker.report_failure(provider)

        with self.lock:
            stats = self.provider_stats[provider]
            stats.total_requests += 1
            if not success:
                stats.total_errors += 1

            # Update average latency
            stats.avg_latency_ms = (
                stats.avg_latency_ms * (stats.total_requests - 1) + latency_ms
            ) / stats.total_requests

            # Update health status based on error rate
            error_rate = (
                stats.total_errors / stats.total_requests if stats.total_requests > 0 else 0
            )
            stats.is_healthy = error_rate < 0.1  # Unhealthy if >10% error rate
