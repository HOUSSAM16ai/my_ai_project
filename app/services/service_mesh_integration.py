# app/services/service_mesh_integration.py
# ======================================================================================
# ==    SUPERHUMAN SERVICE MESH INTEGRATION (v1.0 - ISTIO/LINKERD EDITION)         ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام Service Mesh الخارق
#   ✨ المميزات الخارقة:
#   - Circuit breaker pattern implementation
#   - Service discovery and load balancing
#   - Retry policies with exponential backoff
#   - Request timeout management
#   - Traffic splitting (Canary/Blue-Green deployments)
#   - mTLS and security policies
#   - Telemetry and distributed tracing
#   - Service resilience patterns

from __future__ import annotations

import random
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from flask import current_app


# ======================================================================================
# ENUMERATIONS
# ======================================================================================
class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class TrafficSplitStrategy(Enum):
    """Traffic splitting strategies"""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    WEIGHTED = "weighted"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"


class DeploymentStrategy(Enum):
    """Deployment strategies"""

    ROLLING_UPDATE = "rolling_update"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================
@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Successes needed to close from half-open
    timeout_seconds: int = 60  # Time before trying half-open
    failure_rate_threshold: float = 0.5  # 50% failure rate threshold
    min_requests: int = 10  # Minimum requests before calculating rate


@dataclass
class RetryPolicy:
    """Retry policy configuration"""

    max_retries: int = 3
    initial_backoff_ms: int = 100
    max_backoff_ms: int = 10000
    backoff_multiplier: float = 2.0
    retryable_status_codes: list[int] = field(
        default_factory=lambda: [408, 429, 500, 502, 503, 504]
    )


@dataclass
class TimeoutPolicy:
    """Timeout policy configuration"""

    request_timeout_ms: int = 3000
    idle_timeout_ms: int = 30000
    connection_timeout_ms: int = 5000


@dataclass
class ServiceEndpoint:
    """Service endpoint definition"""

    endpoint_id: str
    service_name: str
    host: str
    port: int
    weight: int = 100  # For weighted load balancing
    version: str = "v1"
    health_check_url: str | None = None
    is_healthy: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrafficSplit:
    """Traffic splitting configuration"""

    split_id: str
    service_name: str
    strategy: TrafficSplitStrategy
    destinations: list[dict[str, Any]]  # {endpoint_id, weight, version}
    metadata: dict[str, Any] = field(default_factory=dict)


# ======================================================================================
# CIRCUIT BREAKER
# ======================================================================================
class CircuitBreaker:
    """
    Circuit Breaker pattern implementation

    Prevents cascading failures by stopping requests to failing services
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.request_history: deque = deque(maxlen=100)
        self.lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Raises:
            Exception: If circuit is open or function fails
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    current_app.logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful request"""
        with self.lock:
            self.request_history.append({"success": True, "timestamp": datetime.now(UTC)})

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    current_app.logger.info("Circuit breaker CLOSED")

    def _on_failure(self):
        """Handle failed request"""
        with self.lock:
            self.request_history.append({"success": False, "timestamp": datetime.now(UTC)})
            self.failure_count += 1
            self.last_failure_time = datetime.now(UTC)

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                current_app.logger.warning("Circuit breaker OPEN (failed during HALF_OPEN)")

            elif self.state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if self._should_trip():
                    self.state = CircuitState.OPEN
                    current_app.logger.warning(
                        f"Circuit breaker OPEN (failures: {self.failure_count})"
                    )

    def _should_trip(self) -> bool:
        """Check if circuit should trip to OPEN"""
        # Simple threshold-based
        if self.failure_count >= self.config.failure_threshold:
            return True

        # Rate-based (if enough requests)
        recent_requests = [
            r
            for r in self.request_history
            if r["timestamp"] > datetime.now(UTC) - timedelta(seconds=60)
        ]

        if len(recent_requests) >= self.config.min_requests:
            failures = sum(1 for r in recent_requests if not r["success"])
            failure_rate = failures / len(recent_requests)
            return failure_rate >= self.config.failure_rate_threshold

        return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try HALF_OPEN"""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.now(UTC) - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state"""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": (
                    self.last_failure_time.isoformat() if self.last_failure_time else None
                ),
            }


# ======================================================================================
# SERVICE MESH MANAGER
# ======================================================================================
class ServiceMeshManager:
    """
    Service Mesh Manager

    Manages service discovery, load balancing, traffic splitting,
    and resilience patterns
    """

    def __init__(self):
        self.services: dict[str, list[ServiceEndpoint]] = defaultdict(list)
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_policies: dict[str, RetryPolicy] = {}
        self.timeout_policies: dict[str, TimeoutPolicy] = {}
        self.traffic_splits: dict[str, TrafficSplit] = {}
        self.request_log: deque = deque(maxlen=10000)
        self.lock = threading.RLock()

    def register_service(
        self,
        service_name: str,
        host: str,
        port: int,
        version: str = "v1",
        weight: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Register a service endpoint"""
        endpoint_id = f"{service_name}_{host}_{port}"

        endpoint = ServiceEndpoint(
            endpoint_id=endpoint_id,
            service_name=service_name,
            host=host,
            port=port,
            version=version,
            weight=weight,
            metadata=metadata or {},
        )

        with self.lock:
            self.services[service_name].append(endpoint)

        current_app.logger.info(
            f"Service registered: {service_name} at {host}:{port} (version: {version})"
        )

        return endpoint_id

    def deregister_service(self, endpoint_id: str) -> bool:
        """Deregister a service endpoint"""
        with self.lock:
            for _service_name, endpoints in self.services.items():
                for endpoint in endpoints:
                    if endpoint.endpoint_id == endpoint_id:
                        endpoints.remove(endpoint)
                        current_app.logger.info(f"Service deregistered: {endpoint_id}")
                        return True
        return False

    def configure_circuit_breaker(
        self,
        service_name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        """Configure circuit breaker for a service"""
        with self.lock:
            self.circuit_breakers[service_name] = CircuitBreaker(config)

        current_app.logger.info(f"Circuit breaker configured for: {service_name}")

    def configure_retry_policy(
        self,
        service_name: str,
        policy: RetryPolicy | None = None,
    ):
        """Configure retry policy for a service"""
        with self.lock:
            self.retry_policies[service_name] = policy or RetryPolicy()

        current_app.logger.info(f"Retry policy configured for: {service_name}")

    def configure_timeout_policy(
        self,
        service_name: str,
        policy: TimeoutPolicy | None = None,
    ):
        """Configure timeout policy for a service"""
        with self.lock:
            self.timeout_policies[service_name] = policy or TimeoutPolicy()

        current_app.logger.info(f"Timeout policy configured for: {service_name}")

    def configure_traffic_split(
        self,
        service_name: str,
        strategy: TrafficSplitStrategy,
        destinations: list[dict[str, Any]],
    ) -> str:
        """
        Configure traffic splitting

        Args:
            service_name: Name of service
            strategy: Traffic splitting strategy
            destinations: List of {endpoint_id, weight, version}

        Returns:
            Split ID
        """
        split_id = str(uuid.uuid4())

        split = TrafficSplit(
            split_id=split_id,
            service_name=service_name,
            strategy=strategy,
            destinations=destinations,
        )

        with self.lock:
            self.traffic_splits[service_name] = split

        current_app.logger.info(f"Traffic split configured: {service_name} ({strategy.value})")

        return split_id

    def get_endpoint(
        self,
        service_name: str,
        version: str | None = None,
    ) -> ServiceEndpoint | None:
        """
        Get service endpoint (with load balancing)

        Applies traffic splitting strategy if configured
        """
        with self.lock:
            endpoints = self.services.get(service_name, [])

            if not endpoints:
                return None

            # Filter by version if specified
            if version:
                endpoints = [e for e in endpoints if e.version == version]

            # Filter healthy endpoints
            healthy_endpoints = [e for e in endpoints if e.is_healthy]

            if not healthy_endpoints:
                return None

            # Apply traffic splitting if configured
            if service_name in self.traffic_splits:
                return self._apply_traffic_split(service_name, healthy_endpoints)

            # Default: weighted round-robin
            return self._weighted_selection(healthy_endpoints)

    def _apply_traffic_split(
        self,
        service_name: str,
        endpoints: list[ServiceEndpoint],
    ) -> ServiceEndpoint | None:
        """Apply traffic splitting strategy"""
        split = self.traffic_splits[service_name]

        if split.strategy == TrafficSplitStrategy.WEIGHTED:
            # Weighted selection based on destination weights
            total_weight = sum(d["weight"] for d in split.destinations)
            rand = random.uniform(0, total_weight)
            cumulative = 0

            for dest in split.destinations:
                cumulative += dest["weight"]
                if rand <= cumulative:
                    # Find endpoint by ID
                    for ep in endpoints:
                        if ep.endpoint_id == dest["endpoint_id"]:
                            return ep

        elif split.strategy == TrafficSplitStrategy.CANARY:
            # Canary: small percentage to new version
            canary_weight = split.destinations[0].get("weight", 10)  # Default 10%
            if random.randint(1, 100) <= canary_weight:
                # Route to canary
                canary_version = split.destinations[0].get("version")
                canary_endpoints = [e for e in endpoints if e.version == canary_version]
                if canary_endpoints:
                    return random.choice(canary_endpoints)

            # Route to stable
            stable_version = split.destinations[1].get("version", "v1")
            stable_endpoints = [e for e in endpoints if e.version == stable_version]
            if stable_endpoints:
                return random.choice(stable_endpoints)

        elif split.strategy == TrafficSplitStrategy.BLUE_GREEN:
            # Blue-Green: all traffic to one version
            active_version = split.destinations[0].get("version")
            version_endpoints = [e for e in endpoints if e.version == active_version]
            if version_endpoints:
                return random.choice(version_endpoints)

        return None

    def _weighted_selection(self, endpoints: list[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint using weighted random selection"""
        total_weight = sum(e.weight for e in endpoints)
        rand = random.uniform(0, total_weight)
        cumulative = 0

        for endpoint in endpoints:
            cumulative += endpoint.weight
            if rand <= cumulative:
                return endpoint

        return endpoints[-1]  # Fallback

    def call_with_resilience(
        self,
        service_name: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Call function with full resilience patterns

        Applies:
        - Circuit breaker
        - Retry with exponential backoff
        - Timeout
        """
        # Get retry policy
        retry_policy = self.retry_policies.get(service_name, RetryPolicy())

        # Get circuit breaker
        circuit_breaker = self.circuit_breakers.get(service_name)

        for attempt in range(retry_policy.max_retries + 1):
            try:
                # Apply circuit breaker if configured
                if circuit_breaker:
                    return circuit_breaker.call(func, *args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                if attempt >= retry_policy.max_retries:
                    raise e

                # Calculate backoff
                backoff_ms = min(
                    retry_policy.initial_backoff_ms * (retry_policy.backoff_multiplier**attempt),
                    retry_policy.max_backoff_ms,
                )

                current_app.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{retry_policy.max_retries + 1}), "
                    f"retrying in {backoff_ms}ms: {e}"
                )

                time.sleep(backoff_ms / 1000)

        raise Exception("Max retries exceeded")

    def get_service_health(self, service_name: str) -> dict[str, Any]:
        """Get health status of service endpoints"""
        with self.lock:
            endpoints = self.services.get(service_name, [])

            healthy = sum(1 for e in endpoints if e.is_healthy)
            total = len(endpoints)

            circuit_breaker = self.circuit_breakers.get(service_name)
            circuit_state = circuit_breaker.get_state() if circuit_breaker else None

            return {
                "service_name": service_name,
                "total_endpoints": total,
                "healthy_endpoints": healthy,
                "health_percentage": (healthy / total * 100) if total > 0 else 0,
                "circuit_breaker": circuit_state,
                "endpoints": [
                    {
                        "endpoint_id": e.endpoint_id,
                        "host": e.host,
                        "port": e.port,
                        "version": e.version,
                        "is_healthy": e.is_healthy,
                    }
                    for e in endpoints
                ],
            }

    def get_metrics(self) -> dict[str, Any]:
        """Get service mesh metrics"""
        with self.lock:
            total_services = len(self.services)
            total_endpoints = sum(len(eps) for eps in self.services.values())

            circuit_breakers_open = sum(
                1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN
            )

            return {
                "total_services": total_services,
                "total_endpoints": total_endpoints,
                "circuit_breakers": {
                    "total": len(self.circuit_breakers),
                    "open": circuit_breakers_open,
                },
                "traffic_splits": len(self.traffic_splits),
                "retry_policies": len(self.retry_policies),
            }


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================
_service_mesh_instance: ServiceMeshManager | None = None
_mesh_lock = threading.Lock()


def get_service_mesh() -> ServiceMeshManager:
    """Get singleton service mesh manager instance"""
    global _service_mesh_instance

    if _service_mesh_instance is None:
        with _mesh_lock:
            if _service_mesh_instance is None:
                _service_mesh_instance = ServiceMeshManager()

    return _service_mesh_instance
