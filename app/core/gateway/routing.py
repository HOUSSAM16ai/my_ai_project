import logging
import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any

from .models import LoadBalancerState, ProtocolType, RoutingDecision, RoutingStrategy
from .providers.anthropic import AnthropicAdapter
from .providers.base import ModelProviderAdapter
from .providers.openai import OpenAIAdapter

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

    def report_failure(self, service_id: str):
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

    def report_success(self, service_id: str):
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
        max_cost = constraints.get("max_cost", float("inf"))
        max_latency = constraints.get("max_latency", float("inf"))

        # Evaluate all available providers
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

        if not candidates:
            raise ValueError("No suitable provider found for routing (or all circuits open)")

        # Calculate scores with normalization for INTELLIGENT strategy
        if strategy == RoutingStrategy.INTELLIGENT and len(candidates) > 0:
            # Find min/max for normalization
            min_cost = min(c["cost"] for c in candidates)
            max_cost = max(c["cost"] for c in candidates)
            cost_range = max_cost - min_cost if max_cost > min_cost else 1.0

            min_latency = min(c["latency"] for c in candidates)
            max_latency = max(c["latency"] for c in candidates)
            latency_range = max_latency - min_latency if max_latency > min_latency else 1.0

            for c in candidates:
                # Normalize to [0, 1] where 0 is best (min) and 1 is worst (max)
                norm_cost = (c["cost"] - min_cost) / cost_range if cost_range > 0 else 0.0
                norm_latency = (
                    (c["latency"] - min_latency) / latency_range if latency_range > 0 else 0.0
                )

                # Score: Higher is better.
                # Invert normalized metrics so 1.0 is best, 0.0 is worst.
                # Use slightly modified weights to emphasize performance quality
                c["score"] = (
                    (1.0 - norm_cost) * 0.3 + (1.0 - norm_latency) * 0.5 + c["health_score"] * 0.2
                )
        else:
            # Legacy/Single-factor strategies
            for c in candidates:
                if strategy == RoutingStrategy.COST_OPTIMIZED:
                    c["score"] = 1.0 / (c["cost"] + 0.001)
                elif strategy == RoutingStrategy.LATENCY_BASED:
                    c["score"] = 1.0 / (c["latency"] + 0.001)
                else:
                    # Fallback for INTELLIGENT if only 1 candidate (normalization irrelevant)
                    # or other future strategies
                    cost_score = 1.0 / (c["cost"] + 0.001)
                    latency_score = 1.0 / (c["latency"] + 0.001)
                    c["score"] = cost_score * 0.3 + latency_score * 0.5 + c["health_score"] * 0.2

        # Select best candidate
        best = max(candidates, key=lambda x: x["score"])

        decision = RoutingDecision(
            service_id=str(best["provider"]),
            base_url=f"https://api.{best['provider']}.com",  # Placeholder
            protocol=ProtocolType.REST,
            estimated_latency_ms=float(best["latency"]),
            estimated_cost=float(best["cost"]),
            confidence_score=float(best["score"]),
            reasoning=f"Selected {best['provider']} based on {strategy.value} strategy",
            metadata={"all_candidates": len(candidates)},
        )

        # Record routing decision
        with self.lock:
            self.routing_history.append(
                {
                    "timestamp": datetime.now(UTC),
                    "decision": decision,
                    "model_type": model_type,
                    "tokens": estimated_tokens,
                }
            )

        return decision

    def update_provider_stats(self, provider: str, success: bool, latency_ms: float):
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
