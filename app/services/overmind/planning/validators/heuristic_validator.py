# app/overmind/planning/validators/heuristic_validator.py
"""
Heuristic validator for plan warnings.

Generates warnings based on heuristics (not hard errors).
Complexity: CC ≤ 3 per method
"""

from typing import Any

from .graph_builder import GraphData


class HeuristicValidator:
    """Generates heuristic warnings for plan quality."""

    def generate_warnings(self, plan: Any, graph_data: GraphData) -> list[Any]:
        """
        Generate heuristic warnings.

        Complexity: CC=2
        """
        warnings = []

        warnings.extend(self._check_root_density(graph_data))
        warnings.extend(self._check_orphan_tasks(graph_data))
        warnings.extend(self._check_priority_uniformity(plan))
        warnings.extend(self._check_risk_density(plan))
        warnings.extend(self._check_gate_conditions(plan))

        return warnings

    def _check_root_density(self, graph_data: GraphData) -> list[Any]:
        """
        Check if too many tasks are roots.

        Complexity: CC=3
        """
        from ..schemas import PlanWarning, WarningSeverity

        warnings = []

        roots = graph_data.roots
        task_count = graph_data.task_count

        if task_count > 10 and len(roots) / task_count > 0.5:
            warnings.append(
                PlanWarning(
                    code="HIGH_ROOT_COUNT",
                    message="More than 50% of tasks are roots",
                    severity=WarningSeverity.STRUCTURE,
                )
            )

        return warnings

    def _check_orphan_tasks(self, graph_data: GraphData) -> list[Any]:
        """
        Check for isolated tasks.

        Complexity: CC=3
        """
        from ..schemas import PlanWarning, WarningSeverity

        warnings = []

        if graph_data.task_count <= 1:
            return warnings

        for tid in graph_data.id_map:
            is_root = graph_data.indegree[tid] == 0
            has_no_children = not graph_data.adjacency[tid]

            if is_root and has_no_children:
                warnings.append(
                    PlanWarning(
                        code="ORPHAN_TASK",
                        message=f"Task '{tid}' is isolated",
                        severity=WarningSeverity.STRUCTURE,
                        task_id=tid,
                    )
                )

        return warnings

    def _check_priority_uniformity(self, plan: Any) -> list[Any]:
        """
        Check if all tasks have same priority.

        Complexity: CC=3
        """
        from ..schemas import PlanWarning, WarningSeverity

        warnings = []

        priorities = [t.priority for t in plan.tasks]

        if len(priorities) > 5 and len(set(priorities)) == 1:
            warnings.append(
                PlanWarning(
                    code="UNIFORM_PRIORITY",
                    message="All tasks share identical priority",
                    severity=WarningSeverity.PERFORMANCE,
                )
            )

        return warnings

    def _check_risk_density(self, plan: Any) -> list[Any]:
        """
        Check if too many tasks are high-risk.

        Complexity: CC=3
        """
        from ..schemas import PlanWarning, RiskLevel, WarningSeverity

        warnings = []

        high_risk = [t for t in plan.tasks if t.risk_level == RiskLevel.HIGH]

        if high_risk and len(high_risk) / len(plan.tasks) > 0.3:
            warnings.append(
                PlanWarning(
                    code="HIGH_RISK_DENSITY",
                    message=f"High-risk tasks ratio {len(high_risk)}/{len(plan.tasks)} > 0.3",
                    severity=WarningSeverity.RISK,
                )
            )

        return warnings

    def _check_gate_conditions(self, plan: Any) -> list[Any]:
        """
        Check if GATE tasks have conditions.

        Complexity: CC=3
        """
        from ..schemas import PlanWarning, TaskType, WarningSeverity

        warnings = []

        for task in plan.tasks:
            if task.task_type == TaskType.GATE and not task.gate_condition:
                warnings.append(
                    PlanWarning(
                        code="GATE_WITHOUT_CONDITION",
                        message=f"GATE task '{task.task_id}' missing gate_condition",
                        severity=WarningSeverity.ADVISORY,
                        task_id=task.task_id,
                    )
                )

        return warnings
