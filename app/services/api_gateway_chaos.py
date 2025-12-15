import logging
import random
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class FaultType(Enum):
    """Types of faults to inject"""
    LATENCY = 'latency'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    PARTIAL_FAILURE = 'partial_failure'
    NETWORK_PARTITION = 'network_partition'
    RESOURCE_EXHAUSTION = 'resource_exhaustion'


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


@dataclass
class ChaosExperiment:
    """Chaos experiment configuration"""
    experiment_id: str
    name: str
    description: str
    fault_type: FaultType
    target_service: str
    fault_rate: float
    duration_seconds: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    timeout_seconds: int = 60
    half_open_requests: int = 3


@dataclass
class CircuitBreakerState:
    """Circuit breaker state"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: datetime | None = None
    opened_at: datetime | None = None
    success_count: int = 0


class ChaosEngineeringService:
    """
    خدمة هندسة الفوضى - Chaos engineering service

    Features:
    - Controlled fault injection
    - Circuit breaker pattern
    - Resilience testing
    - Automated recovery testing
    """

    def __init__(self):
        self.active_experiments: dict[str, ChaosExperiment] = {}
        self.experiment_history: deque = deque(maxlen=1000)
        self.lock = threading.RLock()

    def start_experiment(self, experiment: ChaosExperiment) ->bool:
        """Start a chaos experiment"""
        with self.lock:
            if experiment.experiment_id in self.active_experiments:
                return False
            experiment.started_at = datetime.now(UTC)
            self.active_experiments[experiment.experiment_id] = experiment
            logging.getLogger(__name__).info(
                f'Started chaos experiment: {experiment.name} ({experiment.fault_type.value})'
                )
            return True

    def stop_experiment(self, experiment_id: str) ->bool:
        """Stop a chaos experiment"""
        with self.lock:
            if experiment_id not in self.active_experiments:
                return False
            experiment = self.active_experiments[experiment_id]
            experiment.ended_at = datetime.now(UTC)
            self.experiment_history.append(experiment)
            del self.active_experiments[experiment_id]
            logging.getLogger(__name__).info(
                f'Stopped chaos experiment: {experiment.name}')
            return True

    def _apply_fault(self, experiment: ChaosExperiment, request_context:
        dict[str, Any]) ->dict[str, Any]:
        """Apply specific fault type"""
        fault_data = {'experiment_id': experiment.experiment_id,
            'fault_type': experiment.fault_type.value, 'timestamp':
            datetime.now(UTC).isoformat()}
        if experiment.fault_type == FaultType.LATENCY:
            delay_ms = random.randint(100, 5000)
            time.sleep(delay_ms / 1000)
            fault_data['delay_ms'] = delay_ms
        elif experiment.fault_type == FaultType.ERROR:
            fault_data['error'] = 'Chaos experiment induced error'
            fault_data['error_code'] = 'CHAOS_ERROR'
        elif experiment.fault_type == FaultType.TIMEOUT:
            time.sleep(30)
            fault_data['timeout'] = True
        experiment.metrics['faults_injected'] = experiment.metrics.get(
            'faults_injected', 0) + 1
        return fault_data

    def get_active_experiments(self) ->list[ChaosExperiment]:
        """Get all active experiments"""
        with self.lock:
            return list(self.active_experiments.values())

    def get_experiment_results(self, experiment_id: str) ->(dict[str, Any] |
        None):
        """Get results of a completed experiment"""
        with self.lock:
            for experiment in self.experiment_history:
                if experiment.experiment_id == experiment_id:
                    return {'experiment_id': experiment.experiment_id,
                        'name': experiment.name, 'fault_type': experiment.
                        fault_type.value, 'started_at': experiment.
                        started_at.isoformat() if experiment.started_at else
                        None, 'ended_at': experiment.ended_at.isoformat() if
                        experiment.ended_at else None, 'metrics':
                        experiment.metrics}
            return None


class CircuitBreakerService:
    """
    خدمة قاطع الدائرة - Circuit breaker service

    Implements the circuit breaker pattern to prevent cascading failures
    """

    def __init__(self, config: (CircuitBreakerConfig | None)=None):
        self.config = config or CircuitBreakerConfig()
        self.circuit_states: dict[str, CircuitBreakerState] = defaultdict(
            CircuitBreakerState)
        self.lock = threading.RLock()

    def call(self, service_id: str, operation: Callable[[], Any]) ->tuple[
        bool, Any, str | None]:
        """
        Execute operation through circuit breaker

        Returns:
            (success, result, error_message) tuple
        """
        with self.lock:
            state = self.circuit_states[service_id]
            if state.state == CircuitState.OPEN:
                if state.opened_at:
                    elapsed = (datetime.now(UTC) - state.opened_at
                        ).total_seconds()
                    if elapsed >= self.config.timeout_seconds:
                        state.state = CircuitState.HALF_OPEN
                        state.success_count = 0
                        logging.getLogger(__name__).info(
                            f'Circuit breaker {service_id}: OPEN -> HALF_OPEN')
                    else:
                        return False, None, 'Circuit breaker is OPEN'
                else:
                    return False, None, 'Circuit breaker is OPEN'
            try:
                result = operation()
                if state.state == CircuitState.HALF_OPEN:
                    state.success_count += 1
                    if state.success_count >= self.config.half_open_requests:
                        state.state = CircuitState.CLOSED
                        state.failure_count = 0
                        logging.getLogger(__name__).info(
                            f'Circuit breaker {service_id}: HALF_OPEN -> CLOSED'
                            )
                else:
                    state.failure_count = 0
                return True, result, None
            except Exception as e:
                state.failure_count += 1
                state.last_failure_time = datetime.now(UTC)
                if state.failure_count >= self.config.failure_threshold:
                    state.state = CircuitState.OPEN
                    state.opened_at = datetime.now(UTC)
                    logging.getLogger(__name__).warning(
                        f'Circuit breaker {service_id}: {state.state.value} -> OPEN (failures: {state.failure_count})'
                        )
                return False, None, str(e)

    def get_state(self, service_id: str) ->CircuitState:
        """Get circuit state for service"""
        with self.lock:
            return self.circuit_states[service_id].state

    def reset(self, service_id: str):
        """Manually reset circuit breaker"""
        with self.lock:
            state = self.circuit_states[service_id]
            state.state = CircuitState.CLOSED
            state.failure_count = 0
            state.success_count = 0
            logging.getLogger(__name__).info(
                f'Circuit breaker {service_id}: manually reset to CLOSED')

    def get_all_states(self) ->dict[str, dict[str, Any]]:
        """Get states of all circuit breakers"""
        with self.lock:
            return {service_id: {'state': state.state.value,
                'failure_count': state.failure_count, 'last_failure': state
                .last_failure_time.isoformat() if state.last_failure_time else
                None} for service_id, state in self.circuit_states.items()}


_chaos_service_instance: ChaosEngineeringService | None = None
_circuit_breaker_instance: CircuitBreakerService | None = None
_service_lock = threading.Lock()


def get_chaos_service() ->ChaosEngineeringService:
    """Get singleton chaos engineering service"""
    global _chaos_service_instance
    if _chaos_service_instance is None:
        with _service_lock:
            if _chaos_service_instance is None:
                _chaos_service_instance = ChaosEngineeringService()
    return _chaos_service_instance


def get_circuit_breaker() ->CircuitBreakerService:
    """Get singleton circuit breaker service"""
    global _circuit_breaker_instance
    if _circuit_breaker_instance is None:
        with _service_lock:
            if _circuit_breaker_instance is None:
                _circuit_breaker_instance = CircuitBreakerService()
    return _circuit_breaker_instance


@dataclass
class BulkheadConfig:
    """Bulkhead configuration for resource isolation"""
    max_concurrent: int = 10
    max_queue: int = 100
    timeout_seconds: int = 30


@dataclass
class BulkheadStats:
    """Bulkhead statistics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    current_concurrent: int = 0
    current_queued: int = 0


class BulkheadService:
    """
    خدمة الحواجز المانعة - Bulkheads Service

    Implements the bulkheads pattern for resource isolation.
    Prevents cascading failures by limiting concurrent operations per service.

    Features:
    - Per-service resource pools
    - Queue management with limits
    - Timeout handling
    - Real-time statistics
    """

    def __init__(self):
        self.bulkheads: dict[str, BulkheadConfig] = {}
        self.stats: dict[str, BulkheadStats] = defaultdict(BulkheadStats)
        self.semaphores: dict[str, threading.Semaphore] = {}
        self.lock = threading.RLock()
        self._initialize_bulkheads()

    def _initialize_bulkheads(self):
        """Initialize default bulkheads for critical services"""
        self.register_bulkhead('database', BulkheadConfig(max_concurrent=20,
            max_queue=50, timeout_seconds=30))
        self.register_bulkhead('llm', BulkheadConfig(max_concurrent=10,
            max_queue=100, timeout_seconds=60))
        self.register_bulkhead('external_api', BulkheadConfig(
            max_concurrent=15, max_queue=50, timeout_seconds=30))
        self.register_bulkhead('file_operations', BulkheadConfig(
            max_concurrent=5, max_queue=20, timeout_seconds=20))

    def register_bulkhead(self, service_id: str, config: BulkheadConfig):
        """Register a new bulkhead for a service"""
        with self.lock:
            self.bulkheads[service_id] = config
            self.semaphores[service_id] = threading.Semaphore(config.
                max_concurrent)
            if service_id not in self.stats:
                self.stats[service_id] = BulkheadStats()

    def call(self, service_id: str, operation: Callable[[], Any], timeout:
        (int | None)=None) ->tuple[bool, Any, str | None]:
        """
        Execute operation within bulkhead constraints

        Returns:
            (success, result, error_message)
        """
        if service_id not in self.bulkheads:
            try:
                result = operation()
                return True, result, None
            except Exception as e:
                return False, None, str(e)
        config = self.bulkheads[service_id]
        stats = self.stats[service_id]
        semaphore = self.semaphores[service_id]
        timeout = timeout or config.timeout_seconds
        with self.lock:
            stats.total_calls += 1
            if stats.current_queued >= config.max_queue:
                stats.rejected_calls += 1
                return (False, None,
                    f'Bulkhead queue full for service: {service_id}')
            stats.current_queued += 1
        acquired = semaphore.acquire(timeout=timeout)
        with self.lock:
            stats.current_queued -= 1
        if not acquired:
            with self.lock:
                stats.rejected_calls += 1
            return False, None, f'Bulkhead timeout for service: {service_id}'
        try:
            with self.lock:
                stats.current_concurrent += 1
            result = operation()
            with self.lock:
                stats.successful_calls += 1
            return True, result, None
        except Exception as e:
            with self.lock:
                stats.failed_calls += 1
            return False, None, str(e)
        finally:
            with self.lock:
                stats.current_concurrent -= 1
            semaphore.release()

    def get_stats(self, service_id: (str | None)=None) ->dict[str, Any]:
        """Get bulkhead statistics"""
        with self.lock:
            if service_id:
                if service_id not in self.stats:
                    return {}
                stats = self.stats[service_id]
                config = self.bulkheads.get(service_id)
                return {'service_id': service_id, 'config': {
                    'max_concurrent': config.max_concurrent if config else
                    None, 'max_queue': config.max_queue if config else None,
                    'timeout_seconds': config.timeout_seconds if config else
                    None}, 'stats': {'total_calls': stats.total_calls,
                    'successful_calls': stats.successful_calls,
                    'failed_calls': stats.failed_calls, 'rejected_calls':
                    stats.rejected_calls, 'current_concurrent': stats.
                    current_concurrent, 'current_queued': stats.
                    current_queued, 'success_rate': stats.successful_calls /
                    stats.total_calls * 100 if stats.total_calls > 0 else 0,
                    'rejection_rate': stats.rejected_calls / stats.
                    total_calls * 100 if stats.total_calls > 0 else 0}}
            else:
                return {service_id: self.get_stats(service_id) for
                    service_id in self.bulkheads}


_bulkhead_instance: BulkheadService | None = None


def get_bulkhead_service() ->BulkheadService:
    """Get singleton bulkhead service instance"""
    global _bulkhead_instance
    if _bulkhead_instance is None:
        with _service_lock:
            if _bulkhead_instance is None:
                _bulkhead_instance = BulkheadService()
    return _bulkhead_instance
