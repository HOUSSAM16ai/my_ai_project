# app/services/api_gateway_chaos.py
# ======================================================================================
# ==        API GATEWAY CHAOS ENGINEERING (v1.0 - RESILIENCE EDITION)              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   هندسة الفوضى واختبار المتانة - Chaos engineering and resilience testing
#   ✨ المميزات:
#   - Fault injection (latency, errors, timeouts)
#   - Circuit breaker pattern implementation
#   - Resilience testing and validation
#   - Automated disaster recovery
#   - Chaos experiments management

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import random
import time
import threading
from collections import defaultdict, deque
from flask import current_app


# ======================================================================================
# ENUMERATIONS
# ======================================================================================

class FaultType(Enum):
    """Types of faults to inject"""
    LATENCY = "latency"
    ERROR = "error"
    TIMEOUT = "timeout"
    PARTIAL_FAILURE = "partial_failure"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================

@dataclass
class ChaosExperiment:
    """Chaos experiment configuration"""
    experiment_id: str
    name: str
    description: str
    fault_type: FaultType
    target_service: str
    fault_rate: float  # 0.0 to 1.0
    duration_seconds: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


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
    last_failure_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    success_count: int = 0


# ======================================================================================
# CHAOS ENGINEERING SERVICE
# ======================================================================================

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
        self.active_experiments: Dict[str, ChaosExperiment] = {}
        self.experiment_history: deque = deque(maxlen=1000)
        self.lock = threading.RLock()
    
    def start_experiment(self, experiment: ChaosExperiment) -> bool:
        """Start a chaos experiment"""
        with self.lock:
            if experiment.experiment_id in self.active_experiments:
                return False
            
            experiment.started_at = datetime.now(timezone.utc)
            self.active_experiments[experiment.experiment_id] = experiment
            
            current_app.logger.info(
                f"Started chaos experiment: {experiment.name} ({experiment.fault_type.value})"
            )
            return True
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a chaos experiment"""
        with self.lock:
            if experiment_id not in self.active_experiments:
                return False
            
            experiment = self.active_experiments[experiment_id]
            experiment.ended_at = datetime.now(timezone.utc)
            
            # Move to history
            self.experiment_history.append(experiment)
            del self.active_experiments[experiment_id]
            
            current_app.logger.info(f"Stopped chaos experiment: {experiment.name}")
            return True
    
    def inject_fault(
        self,
        service_id: str,
        request_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Inject fault if experiment is active
        
        Returns:
            Fault data if injected, None otherwise
        """
        with self.lock:
            for experiment in self.active_experiments.values():
                if experiment.target_service != service_id:
                    continue
                
                # Check if experiment is still active
                if experiment.started_at:
                    elapsed = (datetime.now(timezone.utc) - experiment.started_at).total_seconds()
                    if elapsed > experiment.duration_seconds:
                        self.stop_experiment(experiment.experiment_id)
                        continue
                
                # Probabilistic fault injection
                if random.random() < experiment.fault_rate:
                    return self._apply_fault(experiment, request_context)
        
        return None
    
    def _apply_fault(
        self,
        experiment: ChaosExperiment,
        request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply specific fault type"""
        fault_data = {
            'experiment_id': experiment.experiment_id,
            'fault_type': experiment.fault_type.value,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if experiment.fault_type == FaultType.LATENCY:
            # Inject latency
            delay_ms = random.randint(100, 5000)
            time.sleep(delay_ms / 1000)
            fault_data['delay_ms'] = delay_ms
        
        elif experiment.fault_type == FaultType.ERROR:
            # Inject error
            fault_data['error'] = 'Chaos experiment induced error'
            fault_data['error_code'] = 'CHAOS_ERROR'
        
        elif experiment.fault_type == FaultType.TIMEOUT:
            # Simulate timeout
            time.sleep(30)  # Long delay
            fault_data['timeout'] = True
        
        # Update experiment metrics
        experiment.metrics['faults_injected'] = experiment.metrics.get('faults_injected', 0) + 1
        
        return fault_data
    
    def get_active_experiments(self) -> List[ChaosExperiment]:
        """Get all active experiments"""
        with self.lock:
            return list(self.active_experiments.values())
    
    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get results of a completed experiment"""
        with self.lock:
            # Check in history
            for experiment in self.experiment_history:
                if experiment.experiment_id == experiment_id:
                    return {
                        'experiment_id': experiment.experiment_id,
                        'name': experiment.name,
                        'fault_type': experiment.fault_type.value,
                        'started_at': experiment.started_at.isoformat() if experiment.started_at else None,
                        'ended_at': experiment.ended_at.isoformat() if experiment.ended_at else None,
                        'metrics': experiment.metrics
                    }
            
            return None


# ======================================================================================
# CIRCUIT BREAKER SERVICE
# ======================================================================================

class CircuitBreakerService:
    """
    خدمة قاطع الدائرة - Circuit breaker service
    
    Implements the circuit breaker pattern to prevent cascading failures
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.circuit_states: Dict[str, CircuitBreakerState] = defaultdict(CircuitBreakerState)
        self.lock = threading.RLock()
    
    def call(
        self,
        service_id: str,
        operation: Callable[[], Any]
    ) -> tuple[bool, Any, Optional[str]]:
        """
        Execute operation through circuit breaker
        
        Returns:
            (success, result, error_message) tuple
        """
        with self.lock:
            state = self.circuit_states[service_id]
            
            # Check circuit state
            if state.state == CircuitState.OPEN:
                # Check if timeout has passed
                if state.opened_at:
                    elapsed = (datetime.now(timezone.utc) - state.opened_at).total_seconds()
                    if elapsed >= self.config.timeout_seconds:
                        # Move to half-open
                        state.state = CircuitState.HALF_OPEN
                        state.success_count = 0
                        current_app.logger.info(f"Circuit breaker {service_id}: OPEN -> HALF_OPEN")
                    else:
                        return False, None, "Circuit breaker is OPEN"
                else:
                    return False, None, "Circuit breaker is OPEN"
            
            # Execute operation
            try:
                result = operation()
                
                # Record success
                if state.state == CircuitState.HALF_OPEN:
                    state.success_count += 1
                    if state.success_count >= self.config.half_open_requests:
                        # Close circuit
                        state.state = CircuitState.CLOSED
                        state.failure_count = 0
                        current_app.logger.info(f"Circuit breaker {service_id}: HALF_OPEN -> CLOSED")
                else:
                    # Reset failure count on success
                    state.failure_count = 0
                
                return True, result, None
            
            except Exception as e:
                # Record failure
                state.failure_count += 1
                state.last_failure_time = datetime.now(timezone.utc)
                
                # Check if threshold exceeded
                if state.failure_count >= self.config.failure_threshold:
                    state.state = CircuitState.OPEN
                    state.opened_at = datetime.now(timezone.utc)
                    current_app.logger.warning(
                        f"Circuit breaker {service_id}: {state.state.value} -> OPEN "
                        f"(failures: {state.failure_count})"
                    )
                
                return False, None, str(e)
    
    def get_state(self, service_id: str) -> CircuitState:
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
            current_app.logger.info(f"Circuit breaker {service_id}: manually reset to CLOSED")
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        with self.lock:
            return {
                service_id: {
                    'state': state.state.value,
                    'failure_count': state.failure_count,
                    'last_failure': state.last_failure_time.isoformat() if state.last_failure_time else None
                }
                for service_id, state in self.circuit_states.items()
            }


# ======================================================================================
# SINGLETON INSTANCES
# ======================================================================================

_chaos_service_instance: Optional[ChaosEngineeringService] = None
_circuit_breaker_instance: Optional[CircuitBreakerService] = None
_service_lock = threading.Lock()


def get_chaos_service() -> ChaosEngineeringService:
    """Get singleton chaos engineering service"""
    global _chaos_service_instance
    
    if _chaos_service_instance is None:
        with _service_lock:
            if _chaos_service_instance is None:
                _chaos_service_instance = ChaosEngineeringService()
    
    return _chaos_service_instance


def get_circuit_breaker() -> CircuitBreakerService:
    """Get singleton circuit breaker service"""
    global _circuit_breaker_instance
    
    if _circuit_breaker_instance is None:
        with _service_lock:
            if _circuit_breaker_instance is None:
                _circuit_breaker_instance = CircuitBreakerService()
    
    return _circuit_breaker_instance
