# app/overmind/planning/validators/orchestrator.py
"""
Validation orchestrator - replaces monolithic _full_graph_validation.

This orchestrator coordinates all validators using the Strategy Pattern.
Each validator is focused and has CC ≤ 5.

Complexity: CC=5 (orchestration only)
"""

from typing import Any

from .basic_validator import BasicConstraintsValidator
from .depth_validator import DepthValidator
from .fanout_validator import FanoutValidator
from .graph_builder import GraphDataBuilder
from .hash_computer import HashComputer
from .heuristic_validator import HeuristicValidator
from .stats_computer import StatsComputer
from .topology_validator import TopologyValidator


class ValidationOrchestrator:
    """
    Orchestrates plan validation using modular validators.

    This replaces the monolithic _full_graph_validation method with
    a clean, testable, and maintainable architecture.
    """

    def __init__(self, settings: Any):
        self.settings = settings

        self.basic_validator = BasicConstraintsValidator(settings)
        self.topology_validator = TopologyValidator()
        self.depth_validator = DepthValidator(settings)
        self.fanout_validator = FanoutValidator(settings)
        self.heuristic_validator = HeuristicValidator()
        self.stats_computer = StatsComputer()
        self.hash_computer = HashComputer()

    def validate(self, plan: Any) -> dict[str, Any]:
        """
        Orchestrate full plan validation.

        Complexity: CC=5

        Returns:
            dict with issues, warnings, stats, and graph data
        """
        from ..schemas import PlanValidationError

        issues = []
        warnings = []

        # Step 1: Validate basic constraints
        basic_issues = self.basic_validator.validate(plan)
        issues.extend(basic_issues)

        if issues:
            raise PlanValidationError(issues)

        # Step 2: Build graph structure
        graph_data, graph_issues = self._build_graph(plan)
        issues.extend(graph_issues)

        if issues:
            raise PlanValidationError(issues)

        # Step 3: Validate topology
        topo_issues, topo_metadata = self.topology_validator.validate(graph_data)
        issues.extend(topo_issues)

        if issues:
            raise PlanValidationError(issues)

        depth_map = topo_metadata.get("depth_map", {})
        topo_order = topo_metadata.get("topo_order", [])

        # Step 4: Validate depth
        depth_issues = self.depth_validator.validate(depth_map)
        issues.extend(depth_issues)

        # Step 5: Validate fan-out
        fanout_issues = self.fanout_validator.validate(graph_data)
        issues.extend(fanout_issues)

        if issues:
            raise PlanValidationError(issues)

        # Step 6: Generate heuristic warnings
        heuristic_warnings = self.heuristic_validator.generate_warnings(plan, graph_data)
        warnings.extend(heuristic_warnings)

        # Step 7: Compute statistics
        stats = self.stats_computer.compute(plan, graph_data, depth_map)

        # Step 8: Compute hashes
        plan.content_hash = self.hash_computer.compute_content_hash(plan)
        plan.structural_hash = self.hash_computer.compute_structural_hash(plan)

        # Step 9: Update meta if present
        self._update_plan_meta(plan, stats)

        # Return all data needed by caller
        return {
            "issues": issues,
            "warnings": warnings,
            "stats": stats,
            "topo_order": topo_order,
            "adjacency": graph_data.adjacency,
            "indegree": graph_data.indegree,
            "depth_map": depth_map,
        }

    def _build_graph(self, plan: Any) -> tuple[Any, list[Any]]:
        """
        Build graph data structure.

        Complexity: CC=1
        """
        builder = GraphDataBuilder(plan.tasks)
        graph_data, issues = builder.build_id_map().build_adjacency().build_indegree().build()
        return graph_data, issues

    def _update_plan_meta(self, plan: Any, stats: dict[str, Any]) -> None:
        """
        Update plan meta with computed statistics.

        Complexity: CC=2
        """
        if (
            plan.meta
            and hasattr(plan.meta, "avg_task_fanout")
            and plan.meta.avg_task_fanout is None
        ):
            plan.meta.avg_task_fanout = stats.get("avg_out_degree", 0.0)
