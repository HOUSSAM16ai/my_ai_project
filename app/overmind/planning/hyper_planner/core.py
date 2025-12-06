from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any, ClassVar

from ..base_planner import BasePlanner, PlannerError, PlanValidationError
from ..schemas import MissionPlanSchema, PlannedTask, PlanningContext
from . import config, scan_logic, utils
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
        if not self._valid_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        # Initialize Context
        lang = utils._detect_lang(objective)
        files = self._resolve_target_files(objective)
        req_lines = utils.extract_requested_lines(objective)
        total_chunks, per_chunk, adaptive_chunking = self._calculate_chunking(files, req_lines)
        use_stream = self._determine_streaming_strategy(total_chunks)

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
        idx, tasks_pruned = self._prune_if_needed(tasks, idx, planning_context["final_writes"])

        # Metadata Construction
        container_files = scan_logic._container_files_present()
        meta = self._build_meta(
            planning_context,
            tasks,
            tasks_pruned,
            len(tasks),
            container_files,
        )

        plan = MissionPlanSchema(objective=objective, tasks=tasks, meta=meta)
        self._validate(plan, files)

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

    # --- Helpers ---

    def _calculate_chunking(self, files: list[str], req_lines: int) -> tuple[int, int, bool]:
        total_chunks, per_chunk = utils.compute_chunk_plan(req_lines)
        adaptive_chunking = False
        est_per_file_stream = total_chunks * 2 + (2 if total_chunks > 1 else 1)
        est_tasks_core = 25
        projected = est_tasks_core + len(files) * est_per_file_stream

        if projected > config.GLOBAL_TASK_CAP and total_chunks > 1:
            reduction_factor = projected / float(config.GLOBAL_TASK_CAP)
            new_total = max(1, int(total_chunks / math.ceil(reduction_factor)))
            if new_total < total_chunks:
                total_chunks = new_total
                per_chunk = max(
                    80, math.ceil((req_lines or config.CHUNK_SIZE_HINT * 2) / max(1, total_chunks))
                )
                adaptive_chunking = True
        return total_chunks, per_chunk, adaptive_chunking

    def _determine_streaming_strategy(self, total_chunks: int) -> bool:
        streaming_possible = self._can_stream()
        return (
            streaming_possible and config.STREAM_ENABLE and total_chunks >= config.STREAM_MIN_CHUNKS
        )

    def _prune_if_needed(
        self, tasks: list[PlannedTask], idx: int, final_writes: list[str]
    ) -> tuple[int, list[str]]:
        if len(tasks) <= config.GLOBAL_TASK_CAP:
            return idx, []
        pruned = []
        group_map = {
            "semantic": lambda t: "Semantic structural JSON" in t.description,
            "global_summary": lambda t: "Global code semantic summary" in t.description,
            "deep_arch_report": lambda t: "deep architecture report" in t.description.lower(),
        }
        for group in config.OPTIONAL_GROUPS:
            if len(tasks) <= config.GLOBAL_TASK_CAP:
                break
            matcher = group_map.get(group)
            if not matcher:
                continue
            removable = [t for t in tasks if matcher(t)]
            if not removable:
                continue
            for rt in removable:
                if rt.task_id in final_writes:
                    continue
                tasks.remove(rt)
                pruned.append(rt.task_id)
                if len(tasks) <= config.GLOBAL_TASK_CAP:
                    break
        return idx, pruned

    def _build_meta(
        self,
        ctx: dict,
        tasks: list,
        tasks_pruned: list,
        planned_count: int,
        container_files: bool,
    ) -> dict:
        struct_meta = ctx.get("struct_meta", {})
        return {
            "language": ctx["lang"],
            "files": ctx["files"],
            "requested_lines": ctx["req_lines"],
            "total_chunks": ctx["total_chunks"],
            "per_chunk": ctx["per_chunk"],
            "streaming": ctx["use_stream"],
            "append_mode": self._append_allowed(),
            "role_task": ctx["role_task_id"],
            "section_task": ctx["section_task_id"],
            # index telemetry
            "files_scanned": struct_meta.get("files_scanned"),
            "hotspot_count": struct_meta.get("hotspot_count"),
            "duplicate_groups": struct_meta.get("duplicate_groups"),
            "index_version": struct_meta.get("index_version"),
            "struct_index_attached": struct_meta.get("attached", False),
            "struct_index_json_task": struct_meta.get("json_task"),
            "struct_index_md_task": struct_meta.get("md_task"),
            "struct_semantic_task": struct_meta.get("struct_semantic_task"),
            "global_code_summary_task": ctx["global_code_summary_task_id"],
            "struct_context_injected": struct_meta.get("struct_context_injected"),
            "struct_context_source": ctx["context_source"],
            # new telemetry
            "tasks_pruned": tasks_pruned,
            "adaptive_chunking": ctx["adaptive_chunking"],
            "task_budget": {"cap": config.GLOBAL_TASK_CAP, "planned": planned_count},
            "container_files_detected": container_files,
        }

    # ----------------------------------------------------------------------------------
    # Utilities (Kept for compatibility or reduced usage)
    # ----------------------------------------------------------------------------------
    def _read_from_file(self, file_path: str) -> Any:
        # Used by base_planner if needed, but logic moved largely to steps
        if not os.path.exists(file_path):
            return None

        with open(file_path, encoding="utf-8") as f:
            if file_path.endswith((".yaml", ".yml")):
                from app.core.yaml_utils import load_yaml_safely

                try:
                    return load_yaml_safely(f.read())
                except Exception as e:
                    _LOG.warning(f"Failed to load YAML safely from {file_path}: {e}")
                    return None
            if file_path.endswith(".json"):
                try:
                    return json.load(f)
                except Exception:
                    return None
            return f.read()

    def _resolve_target_files(self, objective: str) -> list[str]:
        raw = utils.extract_filenames(objective)
        normalized = []
        for f in raw:
            nf = utils._normalize_filename(f)
            if "." not in nf:
                nf = utils._ensure_ext(nf)
            if nf.lower() not in [x.lower() for x in normalized]:
                normalized.append(nf)
        return normalized[: config.MAX_FILES]

    def _can_stream(self) -> bool:
        mode = config.ALLOW_APPEND_MODE
        if mode == "0":
            return False
        if mode == "1":
            return True
        allowed_env = os.getenv("PLANNER_ALLOWED_TOOLS", "")
        if allowed_env:
            allowed = {t.strip() for t in allowed_env.split(",") if t.strip()}
            return "append_file" in allowed
        return True

    def _append_allowed(self) -> bool:
        return self._can_stream()

    def _validate(self, plan: MissionPlanSchema, files: list[str]):
        if len(plan.tasks) > config.GLOBAL_TASK_CAP:
            raise PlanValidationError("excessive_tasks", self.name, plan.objective)
        ids = {t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise PlanValidationError(
                        f"dangling_dependency:{t.task_id}->{d}", self.name, plan.objective
                    )
        if config.STRICT_WRITE_ENF:
            for f in files:
                if not any(
                    (tt.tool_name in (config.TOOL_WRITE, config.TOOL_APPEND))
                    and (tt.tool_args or {}).get("path", "").lower() == f.lower()
                    for tt in plan.tasks
                ):
                    raise PlanValidationError(f"missing_file_write:{f}", self.name, plan.objective)

    def _valid_objective(self, objective: str) -> bool:
        if not objective or len(objective.strip()) < 5:
            return False
        return not objective.strip().isdigit()
