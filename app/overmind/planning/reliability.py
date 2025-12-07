# app/overmind/planning/reliability.py
"""
Reliability tracking system for Planners.
Implements exponential decay with Laplace smoothing to track success/failure rates over time.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

@dataclass
class ReliabilityState:
    """
    Tracks the reliability of a planner instance.
    Uses exponential decay to weight recent events more heavily.
    """
    success_weight: float = 0.0
    failure_weight: float = 0.0
    last_update_ts: float = field(default_factory=time.time)
    total_invocations: int = 0
    total_failures: int = 0
    total_duration_ms: float = 0.0
    last_success_ts: float | None = None
    registration_time: float = field(default_factory=time.time)
    last_error: str | None = None

    quarantined: bool = False
    self_test_passed: bool | None = None
    production_ready: bool = False
    tier: str = "experimental"
    risk_rating: str = "medium"

    def decay(self, half_life: float, now: float | None = None):
        """Apply exponential decay to weights based on time elapsed."""
        now = now or time.time()
        dt = now - self.last_update_ts
        if dt <= 0 or half_life <= 0:
            self.last_update_ts = now
            return

        factor = 0.5 ** (dt / half_life)
        self.success_weight *= factor
        self.failure_weight *= factor
        self.last_update_ts = now

    def update(self, success: bool, duration_seconds: float, half_life: float):
        """Update state with a new execution result."""
        self.decay(half_life)
        if success:
            self.success_weight += 1.0
            self.last_success_ts = time.time()
        else:
            self.failure_weight += 1.0
            self.total_failures += 1
        self.total_invocations += 1
        self.total_duration_ms += duration_seconds * 1000.0

    def reliability_score(self) -> float:
        """
        Calculate score using Laplace smoothing: (S + 1) / (S + F + 2).
        Returns value between 0.0 and 1.0.
        """
        num = self.success_weight + 1.0
        den = self.success_weight + self.failure_weight + 2.0
        score = num / den if den > 0 else 0.5
        return max(0.0, min(1.0, score))

    @property
    def avg_duration_ms(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return self.total_duration_ms / self.total_invocations
