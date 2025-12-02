# app/overmind/planning/_configs.py
"""
Centralized configuration dataclasses for Overmind planning modules.
All magic values and thresholds externalized for easy tuning.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StructuralScoringConfig:
    """Configuration for structural quality scoring."""

    # Grade to numeric component mapping
    grade_components: dict[str, float] = field(
        default_factory=lambda: {"A": 1.0, "B": 0.7, "C": 0.4}
    )
    default_grade_component: float = 0.5

    # Grade bonuses (additive)
    grade_bonuses: dict[str, float] = field(
        default_factory=lambda: {"A": 0.05, "B": 0.02, "C": 0.0}
    )

    # Structural score weight in final selection
    struct_weight: float = 0.07

    # Reliability nudge for grade A outputs
    reliability_nudge: float = 0.01


@dataclass(frozen=True)
class DriftDetectionConfig:
    """Configuration for structural drift detection."""

    # Relative task count change threshold (0.30 = 30%)
    task_ratio_threshold: float = 0.30

    # Grade drop severity threshold (A=3, B=2, C=1)
    grade_drop_threshold: int = 2

    # Grade numeric ordering for comparison
    grade_order: dict[str, int] = field(default_factory=lambda: {"A": 3, "B": 2, "C": 1})


@dataclass(frozen=True)
class SelfTestConfig:
    """Configuration for planner self-test execution."""

    timeout_seconds: float = 5.0
    disable_quarantine: bool = False
