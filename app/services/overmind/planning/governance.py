# app/overmind/planning/governance.py
"""
Governance and Configuration for Planners.
Handles environment variables, allow/block lists, and configuration constants.
"""

import os
import re

from ._configs import DriftDetectionConfig, SelfTestConfig, StructuralScoringConfig

# Regex for planner name validation
NAME_PATTERN = re.compile(r"^[a-z0-9_][a-z0-9_\-]{2,63}$")

# Environment Variables
ENV = os.getenv("OVERMIND_ENV", "dev").strip().lower()
ALLOW_LIST = {x.strip().lower() for x in os.getenv("PLANNERS_ALLOW", "").split(",") if x.strip()}
BLOCK_LIST = {x.strip().lower() for x in os.getenv("PLANNERS_BLOCK", "").split(",") if x.strip()}

# Tuning Constants
DECAY_HALF_LIFE = float(os.getenv("PLANNER_DECAY_HALF_LIFE", "900"))
MIN_RELIABILITY = float(os.getenv("PLANNER_MIN_RELIABILITY", "0.05"))
FALLBACK_DEFAULT_TIMEOUT = float(os.getenv("PLANNER_DEFAULT_TIMEOUT", "40"))

# Feature Flags
STRUCT_ENABLE = os.getenv("PLANNER_STRUCT_SCORE_ENABLE", "1") == "1"

# Config Objects
STRUCT_CONFIG = StructuralScoringConfig(
    grade_bonuses={
        "A": float(os.getenv("PLANNER_STRUCT_GRADE_BONUS_A", "0.05") or 0.05),
        "B": float(os.getenv("PLANNER_STRUCT_GRADE_BONUS_B", "0.02") or 0.02),
        "C": float(os.getenv("PLANNER_STRUCT_GRADE_BONUS_C", "0.0") or 0.0),
    },
    struct_weight=float(os.getenv("PLANNER_STRUCT_SCORE_WEIGHT", "0.07") or 0.07),
    reliability_nudge=float(os.getenv("PLANNER_STRUCT_RELIABILITY_NUDGE", "0.01") or 0.01),
)

DRIFT_CONFIG = DriftDetectionConfig(
    task_ratio_threshold=float(os.getenv("PLANNER_STRUCT_DRIFT_TASK_RATIO", "0.30") or 0.30),
    grade_drop_threshold=int(os.getenv("PLANNER_STRUCT_DRIFT_GRADE_DROP", "2") or 2),
)

SELF_TEST_CONFIG = SelfTestConfig(
    timeout_seconds=float(os.getenv("PLANNER_SELF_TEST_TIMEOUT", "5")),
    disable_quarantine=os.getenv("PLANNER_DISABLE_QUARANTINE", "0") == "1",
)


def is_planner_allowed(name: str) -> bool:
    """Checks if a planner name is allowed by current policy."""
    key = name.strip().lower()
    if not NAME_PATTERN.match(key):
        return False
    if key in BLOCK_LIST:
        return False
    return not (ALLOW_LIST and key not in ALLOW_LIST)
