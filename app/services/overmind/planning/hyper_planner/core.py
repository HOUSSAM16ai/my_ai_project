from __future__ import annotations

import logging
import os
import time
from typing import ClassVar

from ..base_planner import BasePlanner, PlannerError
from ..schemas import MissionPlanSchema, PlannedTask, PlanningContext
from . import config, planning_logic, scan_logic, utils
from .steps.base import PlanningStep
from .steps.generation_step import GenerationStep
from .steps.index_step import DeepIndexStep
from .steps.reporting_step import ReportingStep
from .steps.scan_step import ScanRepoStep
from .steps.semantic_step import SemanticAnalysisStep
from .steps.structure_step import StructureStep

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("ultra_hyper_planner")
_lvl = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
_LOG.setLevel(getattr(logging, _lvl, logging.INFO) if _lvl else logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)


# --------------------------------------------------------------------------------------
# Planner
# --------------------------------------------------------------------------------------
class PeerNode:
    """Represents a peer planner in the cluster."""

    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight


class UltraHyperPlanner(BasePlanner):
    name = "ultra_hyper_semantic_planner"
    version = "9.0.0-atomic-modular"
    production_ready = True
    capabilities: ClassVar[set[str]] = {
        "semantic",
        "chunked",
        "multi-file",
        "arabic",
        "adaptive",
        "struct_index",
        "architecture",
        "telemetry",
        "global_scan",
        "clustering",
        "failover",
    }
    tags: ClassVar[set[str]] = {"ultra", "hyper", "planner", "index", "semantic", "cluster"}

    def __init__(self):
        super().__init__()
        self.peers = [PeerNode("backup_planner_alpha", 0.8), PeerNode("backup_planner_beta", 0.7)]
        # Define the pipeline sequence
        self.pipeline: list[PlanningStep] = [
            ScanRepoStep(),
            DeepIndexStep(),
            SemanticAnalysisStep(),
            StructureStep(),
            GenerationStep(),
            ReportingStep(),
        ]

    # ------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: PlanningContext | None = None,
        max_tasks: int | None = None,
    ) -> MissionPlanSchema:
        try:
            return self._core_planning_logic(objective, context, max_tasks)
        except Exception as e:
            _LOG.error(f"Primary planner failed: {e}. Attempting fallback...")
            return self._fallback_logic(objective)

    def _fallback_logic(self, objective: str) -> MissionPlanSchema:
        """Failover to a peer node logic simulation."""
        best_peer = max(self.peers, key=lambda p: p.weight)
        _LOG.info(f"Failing over to {best_peer.name}")

        tasks = [
            PlannedTask(
                task_id="f01",
                description=f"Fallback execution by {best_peer.name}: Understand Objective",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": f"Emergency Mode: {objective}"},
                dependencies=[],
            )
        ]

        return MissionPlanSchema(
            objective=objective,
            tasks=tasks,
            meta={"cluster_mode": True, "active_node": best_peer.name, "failover": True},
        )

    def _core_planning_logic(
        self,
        objective: str,
        context: PlanningContext | None = None,
        max_tasks: int | None = None,
    ) -> MissionPlanSchema:
        start = time.perf_counter()
        if not planning_logic.validate_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        # Initialize Context
        lang = utils._detect_lang(objective)
        files = planning_logic.resolve_target_files(objective)
        req_lines = utils.extract_requested_lines(objective)
        total_chunks, per_chunk, adaptive_chunking = planning_logic.calculate_chunking(files, req_lines)
        use_stream = planning_logic.determine_streaming_strategy(total_chunks, planning_logic.can_stream())

        planning_context = {
            "objective": objective,
            "lang": lang,
            "files": files,
            "req_lines": req_lines,
            "total_chunks": total_chunks,
            "per_chunk": per_chunk,
            "adaptive_chunking": adaptive_chunking,
            "use_stream": use_stream,
            # Accumulators
            "tasks": [],
            "analysis_dependency_ids": [],
            "index_deps": [],
            "struct_meta": {},
            "final_writes": [],
            # Step Outputs
            "struct_semantic_task_id": None,
            "global_code_summary_task_id": None,
            "role_task_id": None,
            "section_task_id": None,
            "struct_placeholder_ref": None,
            "context_source": "none",
        }

        tasks: list[PlannedTask] = []
        idx = 1

        # Execute Pipeline
        for step in self.pipeline:
            idx = step.execute(tasks, idx, planning_context)

        # Post-Processing: Pruning & Finalization
        tasks_pruned = []
        idx, tasks_pruned = planning_logic.prune_tasks_if_needed(tasks, idx, planning_context["final_writes"])

        # Metadata Construction
        container_files = scan_logic._container_files_present()
        meta = planning_logic.build_plan_metadata(
            planning_context,
            tasks,
            tasks_pruned,
            len(tasks),
            container_files,
            planning_logic.can_stream(),
        )

        plan = MissionPlanSchema(objective=objective, tasks=tasks, meta=meta)
        planning_logic.validate_plan(tasks, files, objective, self.name)

        elapsed = (time.perf_counter() - start) * 1000
        _LOG.info(
            "[HyperPlanner v9] tasks=%d pruned=%d streaming=%s ctx=%s ms=%.1f",
            len(tasks),
            len(tasks_pruned),
            use_stream,
            planning_context["context_source"],
            elapsed,
        )
        return plan
