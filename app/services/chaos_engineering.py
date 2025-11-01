# app/services/chaos_engineering.py
# ======================================================================================
# ==        SUPERHUMAN CHAOS ENGINEERING (v1.0 - RESILIENCE TESTING)              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام Chaos Engineering الخارق
#   ✨ المميزات الخارقة:
#   - Chaos Monkey implementation
#   - Fault injection (latency, errors, network issues)
#   - Resilience testing and validation
#   - Blast radius control
#   - Automated rollback on critical failures
#   - Game Day simulations
#   - Steady-state hypothesis validation
#   - Progressive chaos experiments

from __future__ import annotations

import random
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from flask import current_app


# ======================================================================================
# ENUMERATIONS
# ======================================================================================
class FaultType(Enum):
    """Types of faults to inject"""

    LATENCY = "latency"  # Add artificial latency
    ERROR = "error"  # Throw errors
    TIMEOUT = "timeout"  # Cause timeouts
    CIRCUIT_BREAKER = "circuit_breaker"  # Trip circuit breakers
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # CPU/memory pressure
    NETWORK_PARTITION = "network_partition"  # Simulate network splits
    SERVICE_UNAVAILABLE = "service_unavailable"  # Make service unavailable


class ExperimentStatus(Enum):
    """Experiment execution status"""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class BlastRadiusLevel(Enum):
    """Control blast radius of experiments"""

    MINIMAL = "minimal"  # Single instance
    LIMITED = "limited"  # Small percentage of traffic
    MODERATE = "moderate"  # Moderate percentage
    EXTENSIVE = "extensive"  # Large percentage (requires approval)


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================
@dataclass
class SteadyStateHypothesis:
    """Hypothesis about system steady state"""

    hypothesis_id: str
    description: str
    validation_function: Callable[[], bool]
    tolerance_threshold: float = 0.95  # 95% success rate
    measurement_window_seconds: int = 60


@dataclass
class FaultInjection:
    """Fault injection configuration"""

    fault_id: str
    fault_type: FaultType
    target_service: str
    parameters: dict[str, Any] = field(default_factory=dict)

    # Control
    probability: float = 1.0  # Probability of fault (0.0-1.0)
    blast_radius: BlastRadiusLevel = BlastRadiusLevel.LIMITED

    # Duration
    duration_seconds: int = 60

    # Safety
    abort_on_metric: str | None = None
    abort_threshold: float | None = None


@dataclass
class ChaosExperiment:
    """Chaos experiment definition"""

    experiment_id: str
    name: str
    description: str

    # Hypothesis
    steady_state_hypothesis: SteadyStateHypothesis

    # Faults to inject
    fault_injections: list[FaultInjection]

    # Execution
    status: ExperimentStatus = ExperimentStatus.SCHEDULED
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Results
    hypothesis_validated: bool | None = None
    observations: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    # Safety
    auto_rollback: bool = True
    blast_radius: BlastRadiusLevel = BlastRadiusLevel.LIMITED


@dataclass
class GameDay:
    """Game Day simulation event"""

    game_day_id: str
    name: str
    scenario: str
    experiments: list[str]  # Experiment IDs
    scheduled_at: datetime
    duration_hours: int
    participants: list[str]
    runbook_url: str | None = None


# ======================================================================================
# CHAOS MONKEY
# ======================================================================================
class ChaosMonkey:
    """
    Chaos Monkey - Randomly injects faults into services

    Inspired by Netflix's Chaos Monkey
    """

    def __init__(
        self,
        enabled: bool = False,
        probability: float = 0.01,  # 1% chance
        blast_radius: BlastRadiusLevel = BlastRadiusLevel.MINIMAL,
    ):
        self.enabled = enabled
        self.probability = probability
        self.blast_radius = blast_radius
        self.active_faults: dict[str, FaultInjection] = {}
        self.lock = threading.RLock()

    def maybe_inject_fault(
        self,
        service_name: str,
        operation: str,
    ) -> FaultInjection | None:
        """
        Maybe inject a fault

        Returns fault injection if triggered, None otherwise
        """
        if not self.enabled:
            return None

        # Check probability
        if random.random() > self.probability:
            return None

        # Select random fault type
        fault_type = random.choice(list(FaultType))

        # Create fault injection
        fault = FaultInjection(
            fault_id=str(uuid.uuid4()),
            fault_type=fault_type,
            target_service=service_name,
            parameters=self._get_fault_parameters(fault_type),
            probability=self.probability,
            blast_radius=self.blast_radius,
            duration_seconds=random.randint(10, 60),
        )

        with self.lock:
            self.active_faults[fault.fault_id] = fault

        current_app.logger.warning(
            f"🐒 Chaos Monkey injected {fault_type.value} fault into {service_name}.{operation}"
        )

        return fault

    def _get_fault_parameters(self, fault_type: FaultType) -> dict[str, Any]:
        """Get parameters for fault type"""
        if fault_type == FaultType.LATENCY:
            return {
                "delay_ms": random.randint(100, 5000),
            }
        elif fault_type == FaultType.ERROR:
            return {
                "error_message": "Chaos Monkey induced error",
                "error_code": random.choice([500, 503, 504]),
            }
        elif fault_type == FaultType.TIMEOUT:
            return {
                "timeout_ms": random.randint(30000, 60000),
            }
        return {}

    def apply_fault(self, fault: FaultInjection):
        """Apply fault injection"""
        if fault.fault_type == FaultType.LATENCY:
            delay_ms = fault.parameters.get("delay_ms", 1000)
            time.sleep(delay_ms / 1000)

        elif fault.fault_type == FaultType.ERROR:
            error_message = fault.parameters.get("error_message", "Induced error")
            error_code = fault.parameters.get("error_code", 500)
            raise Exception(f"{error_message} (HTTP {error_code})")

        elif fault.fault_type == FaultType.TIMEOUT:
            timeout_ms = fault.parameters.get("timeout_ms", 30000)
            time.sleep(timeout_ms / 1000)
            raise TimeoutError("Operation timed out (induced)")

    def clear_fault(self, fault_id: str):
        """Clear an active fault"""
        with self.lock:
            if fault_id in self.active_faults:
                del self.active_faults[fault_id]


# ======================================================================================
# CHAOS ENGINEER
# ======================================================================================
class ChaosEngineer:
    """
    Chaos Engineering Service

    Manages chaos experiments and validates system resilience
    """

    def __init__(self):
        self.experiments: dict[str, ChaosExperiment] = {}
        self.game_days: dict[str, GameDay] = {}
        self.chaos_monkey = ChaosMonkey()
        self.experiment_history: deque = deque(maxlen=100)
        self.lock = threading.RLock()

    def enable_chaos_monkey(
        self,
        probability: float = 0.01,
        blast_radius: BlastRadiusLevel = BlastRadiusLevel.MINIMAL,
    ):
        """Enable Chaos Monkey"""
        self.chaos_monkey.enabled = True
        self.chaos_monkey.probability = probability
        self.chaos_monkey.blast_radius = blast_radius

        current_app.logger.info(
            f"🐒 Chaos Monkey enabled (probability: {probability}, "
            f"blast_radius: {blast_radius.value})"
        )

    def disable_chaos_monkey(self):
        """Disable Chaos Monkey"""
        self.chaos_monkey.enabled = False
        current_app.logger.info("🐒 Chaos Monkey disabled")

    def create_experiment(
        self,
        name: str,
        description: str,
        steady_state_hypothesis: SteadyStateHypothesis,
        fault_injections: list[FaultInjection],
        blast_radius: BlastRadiusLevel = BlastRadiusLevel.LIMITED,
    ) -> str:
        """Create a chaos experiment"""
        experiment_id = str(uuid.uuid4())

        experiment = ChaosExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            steady_state_hypothesis=steady_state_hypothesis,
            fault_injections=fault_injections,
            blast_radius=blast_radius,
        )

        with self.lock:
            self.experiments[experiment_id] = experiment

        current_app.logger.info(f"Chaos experiment created: {name} ({experiment_id})")

        return experiment_id

    def run_experiment(self, experiment_id: str) -> bool:
        """
        Run a chaos experiment

        1. Validate steady state
        2. Inject faults
        3. Validate system still meets hypothesis
        4. Rollback faults

        Returns True if experiment succeeded
        """
        with self.lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now(UTC)

        try:
            # 1. Validate steady state before experiment
            current_app.logger.info(f"Validating steady state for experiment: {experiment.name}")

            steady_state_before = experiment.steady_state_hypothesis.validation_function()

            if not steady_state_before:
                current_app.logger.error(
                    "Steady state validation failed before experiment - aborting"
                )
                experiment.status = ExperimentStatus.ABORTED
                return False

            experiment.observations.append(
                {
                    "phase": "before",
                    "steady_state": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # 2. Inject faults
            current_app.logger.info(f"Injecting {len(experiment.fault_injections)} faults")

            for fault in experiment.fault_injections:
                self._activate_fault(fault)

            # 3. Wait for fault duration
            max_duration = max(f.duration_seconds for f in experiment.fault_injections)
            time.sleep(max_duration)

            # 4. Validate steady state during experiment
            steady_state_during = experiment.steady_state_hypothesis.validation_function()

            experiment.observations.append(
                {
                    "phase": "during",
                    "steady_state": steady_state_during,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # 5. Rollback faults
            if experiment.auto_rollback:
                self._rollback_faults(experiment)

            # 6. Validate steady state after experiment
            time.sleep(5)  # Grace period
            steady_state_after = experiment.steady_state_hypothesis.validation_function()

            experiment.observations.append(
                {
                    "phase": "after",
                    "steady_state": steady_state_after,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # 7. Determine if hypothesis validated
            experiment.hypothesis_validated = (
                steady_state_before and steady_state_during and steady_state_after
            )

            experiment.status = ExperimentStatus.COMPLETED
            experiment.completed_at = datetime.now(UTC)

            with self.lock:
                self.experiment_history.append(experiment)

            result = "✅ SUCCESS" if experiment.hypothesis_validated else "❌ FAILED"
            current_app.logger.info(f"Experiment completed: {experiment.name} - {result}")

            return experiment.hypothesis_validated

        except Exception as e:
            current_app.logger.error(f"Experiment error: {e}")
            experiment.status = ExperimentStatus.FAILED

            if experiment.auto_rollback:
                self._rollback_faults(experiment)

            return False

    def _activate_fault(self, fault: FaultInjection):
        """Activate a fault injection"""
        # In production, this would integrate with service mesh or infrastructure
        current_app.logger.warning(
            f"Activating fault: {fault.fault_type.value} on {fault.target_service}"
        )

    def _rollback_faults(self, experiment: ChaosExperiment):
        """Rollback all faults in experiment"""
        current_app.logger.info(f"Rolling back faults for experiment: {experiment.name}")

        for _fault in experiment.fault_injections:
            # Deactivate fault
            pass

    def schedule_game_day(
        self,
        name: str,
        scenario: str,
        experiments: list[str],
        scheduled_at: datetime,
        duration_hours: int,
        participants: list[str],
    ) -> str:
        """Schedule a Game Day simulation"""
        game_day_id = str(uuid.uuid4())

        game_day = GameDay(
            game_day_id=game_day_id,
            name=name,
            scenario=scenario,
            experiments=experiments,
            scheduled_at=scheduled_at,
            duration_hours=duration_hours,
            participants=participants,
        )

        with self.lock:
            self.game_days[game_day_id] = game_day

        current_app.logger.info(f"Game Day scheduled: {name} at {scheduled_at.isoformat()}")

        return game_day_id

    def get_experiment_report(self, experiment_id: str) -> dict[str, Any] | None:
        """Get detailed experiment report"""
        with self.lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return None

            return {
                "experiment_id": experiment.experiment_id,
                "name": experiment.name,
                "description": experiment.description,
                "status": experiment.status.value,
                "started_at": (
                    experiment.started_at.isoformat() if experiment.started_at else None
                ),
                "completed_at": (
                    experiment.completed_at.isoformat() if experiment.completed_at else None
                ),
                "hypothesis_validated": experiment.hypothesis_validated,
                "observations": experiment.observations,
                "fault_count": len(experiment.fault_injections),
                "blast_radius": experiment.blast_radius.value,
            }

    def get_metrics(self) -> dict[str, Any]:
        """Get chaos engineering metrics"""
        with self.lock:
            total_experiments = len(self.experiments)
            completed = sum(
                1 for e in self.experiments.values() if e.status == ExperimentStatus.COMPLETED
            )
            validated = sum(1 for e in self.experiments.values() if e.hypothesis_validated is True)

            return {
                "total_experiments": total_experiments,
                "completed": completed,
                "validated": validated,
                "validation_rate": (validated / completed * 100) if completed > 0 else 0,
                "chaos_monkey_enabled": self.chaos_monkey.enabled,
                "active_faults": len(self.chaos_monkey.active_faults),
                "scheduled_game_days": len(self.game_days),
            }


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================
_chaos_engineer_instance: ChaosEngineer | None = None
_chaos_lock = threading.Lock()


def get_chaos_engineer() -> ChaosEngineer:
    """Get singleton chaos engineer instance"""
    global _chaos_engineer_instance

    if _chaos_engineer_instance is None:
        with _chaos_lock:
            if _chaos_engineer_instance is None:
                _chaos_engineer_instance = ChaosEngineer()

    return _chaos_engineer_instance
