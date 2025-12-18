"""
Drift detection logic extracted from base_planner for reduced complexity.
Detects structural changes in plan quality over time.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any
from ._configs import DriftDetectionConfig
_LAST_STRUCT: dict[str, dict[str, Any]] = {}


@dataclass
class DriftResult:
    """Result of drift detection analysis."""
    drift_detected: bool
    task_count_changed: bool = False
    grade_dropped: bool = False
    prev_task_count: int | None = None
    current_task_count: int | None = None
    prev_grade: str | None = None
    current_grade: str | None = None


def detect_structural_drift(planner_name: str, plan: Any, current_grade: (
    str | None), config: DriftDetectionConfig) ->bool:
    """
    Detect structural drift by comparing current plan with previous snapshot.

    Args:
        planner_name: Name of the planner (lowercase)
        plan: MissionPlanSchema object
        current_grade: Current structural quality grade
        config: Drift detection configuration

    Returns:
        True if drift detected, False otherwise
    """
    planner_key = planner_name.lower()
    prev = _LAST_STRUCT.get(planner_key)
    task_count = len(getattr(plan, 'tasks', []) or [])
    drift_flag = False
    if prev:
        prev_tasks = prev.get('tasks', task_count)
        if prev_tasks > 0:
            ratio_change = abs(task_count - prev_tasks) / prev_tasks
            if ratio_change >= config.task_ratio_threshold:
                drift_flag = True
        prev_grade = prev.get('grade')
        if prev_grade and current_grade:
            prev_order = config.grade_order.get(prev_grade, 2)
            current_order = config.grade_order.get(current_grade, 2)
            if prev_order - current_order >= config.grade_drop_threshold:
                drift_flag = True
    _LAST_STRUCT[planner_key] = {'tasks': task_count, 'grade':
        current_grade, 'ts': time.time()}
    return drift_flag
