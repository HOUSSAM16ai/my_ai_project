# app/overmind/planning/schemas.py
# -*- coding: utf-8 -*-
# =============================================================================
# OVERMIND / MAESTRO – PLANNING SCHEMAS CORE
# Ultra Sovereign Structural Edition
# Version: 4.2.0  •  Codename: "PLAN-OMEGA / STRUCT-METRICS / DUAL-HASH / QUALITY-GRADE"
# =============================================================================
# DESIGN GOALS
#   - Single Source of Truth for mission planning data structures.
#   - Strong validation (graph topology, fan-out, depth, risk gating, tool args).
#   - Structural Intelligence Channels:
#        * PlanMeta extended with structural metrics (hotspot_density, layer_diversity, entropy, duplicates).
#        * Dual hashing (content_hash + structural_hash) for semantic vs structural change tracking.
#        * Structural quality grading heuristic (A / B / C).
#   - Policy Hooks for custom governance (risk caps, structural sanity).
#   - Backward compatible (all new fields optional; no breaking removal).
#
# NEW IN 4.2.0 (vs 4.0.1):
#   + Extended PlanMeta (hotspots_count, duplicate_groups, layers_detected, hotspot_density,
#     layer_diversity, structural_entropy, avg_task_fanout, structural_quality_grade, structural_hash).
#   + structural_hash: stable signature over (deps, priority, risk, hotspot, layer).
#   + PLAN_MAX_META_BYTES (env) enforcement (optional) to avoid oversized meta payloads.
#   + Policy hook _policy_structural_sanity (hotspot density / diversity / entropy warnings).
#   + Structural quality grade heuristic (auto if not supplied).
#   + Risk amplification readiness via risk_score + structural signals (extensible).
#
# ENV (tunable):
#    PLAN_MAX_TASKS (default 800)
#    PLAN_MAX_DESCRIPTION_LEN (default 600)
#    PLAN_MAX_METADATA_KEYS (default 30)
#    PLAN_MAX_TOOL_ARGS_KEYS (default 40)
#    PLAN_MAX_TOOL_ARGS_BYTES (default 24000)
#    PLAN_MAX_DEPTH (default 60)
#    PLAN_MAX_OUT_DEGREE (default 80)
#    PLAN_PRIORITY_MIN (default 0)
#    PLAN_PRIORITY_MAX (default 1000)
#    PLAN_MAX_META_BYTES (default 64000)  # New: serialized size limit for meta (PlanMeta) if present
#
# SAFETY:
#   - All validations raise PlanValidationError (aggregate issues).
#   - Optional TOOL_REGISTRY interface for tool args schema adaptation.
#   - All added structural metrics optional; absence is safe.
#
# NOTE:
#   - Keep triple-quoted docstrings minimal; critical logic uses explicit comments for CI robustness.
# =============================================================================

from __future__ import annotations

import json
import hashlib
import os
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import (
    List, Dict, Any, Optional, Callable
)

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

__schema_version__ = "4.2.0"

# =============================================================================
# SETTINGS
# =============================================================================

@dataclass
class PlanSettings:
    MAX_TASKS: int = int(os.environ.get("PLAN_MAX_TASKS", 800))
    MAX_DESCRIPTION_LEN: int = int(os.environ.get("PLAN_MAX_DESCRIPTION_LEN", 600))
    MAX_METADATA_KEYS: int = int(os.environ.get("PLAN_MAX_METADATA_KEYS", 30))
    MAX_TOOL_ARGS_KEYS: int = int(os.environ.get("PLAN_MAX_TOOL_ARGS_KEYS", 40))
    MAX_SERIALIZED_TOOL_ARGS_BYTES: int = int(os.environ.get("PLAN_MAX_TOOL_ARGS_BYTES", 24000))
    MAX_DEPTH: int = int(os.environ.get("PLAN_MAX_DEPTH", 60))
    MAX_OUT_DEGREE: int = int(os.environ.get("PLAN_MAX_OUT_DEGREE", 80))
    PRIORITY_MIN: int = int(os.environ.get("PLAN_PRIORITY_MIN", 0))
    PRIORITY_MAX: int = int(os.environ.get("PLAN_PRIORITY_MAX", 1000))
    MAX_META_BYTES: int = int(os.environ.get("PLAN_MAX_META_BYTES", 64000))

SETTINGS = PlanSettings()

# =============================================================================
# ENUMS
# =============================================================================

class TaskType(str, Enum):
    TOOL = "TOOL"
    TRANSFORM = "TRANSFORM"
    AGGREGATE = "AGGREGATE"
    VERIFY = "VERIFY"
    GATE = "GATE"

class Criticality(str, Enum):
    BLOCKING = "BLOCKING"
    SOFT = "SOFT"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class WarningSeverity(str, Enum):
    INFO = "INFO"
    ADVISORY = "ADVISORY"
    RISK = "RISK"
    PERFORMANCE = "PERFORMANCE"
    STRUCTURE = "STRUCTURE"

# =============================================================================
# VALIDATION DATA STRUCTURES
# =============================================================================

class PlanValidationIssue(BaseModel):
    code: str
    message: str
    task_id: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None

class PlanWarning(BaseModel):
    code: str
    message: str
    severity: WarningSeverity = WarningSeverity.INFO
    task_id: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None

class PlanValidationError(ValueError):
    def __init__(self, issues: List[PlanValidationIssue]):
        self.issues = issues
        super().__init__(f"Plan validation failed with {len(issues)} issues.")
    def to_dict(self) -> Dict[str, Any]:
        return {"issues": [i.model_dump() for i in self.issues]}

# =============================================================================
# TOOL REGISTRY (OPTIONAL EXTERNAL INJECTION)
# =============================================================================

class ToolRegistryInterface:
    def has(self, tool_name: str) -> bool:  # pragma: no cover
        return False
    def validate(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return args

TOOL_REGISTRY: Optional[ToolRegistryInterface] = None

# =============================================================================
# POLICY HOOKS
# =============================================================================

PolicyHook = Callable[['MissionPlanSchema'], None]
_POLICY_HOOKS: List[PolicyHook] = []

def register_policy_hook(hook: PolicyHook) -> None:
    _POLICY_HOOKS.append(hook)

# =============================================================================
# PLAN META (Structural Expansion)
# =============================================================================

class PlanMeta(BaseModel):
    """
    Flexible telemetry / semantic channel. All fields optional.
    - Base semantics: language, streaming flags, counts.
    - Structural metrics: hotspot density, layer diversity, duplication cluster signals.
    - structural_quality_grade: assigned automatically if not provided (A|B|C).
    - structural_hash: optional override (auto calculated separately in plan if missing).
    New fields are additive; consumers should treat unknown keys as optional hints.
    """
    language: Optional[str] = None
    section_task: Optional[str] = None
    files_scanned: Optional[int] = None
    streaming: Optional[bool] = None
    chunk_count: Optional[int] = None
    roles_inferred: Optional[int] = None
    artifacts_expected: Optional[int] = None

    # Extended structural telemetry:
    hotspots_count: Optional[int] = None
    duplicate_groups: Optional[int] = None
    layers_detected: Optional[int] = None
    hotspot_density: Optional[float] = None
    layer_diversity: Optional[float] = None
    structural_entropy: Optional[float] = None
    avg_task_fanout: Optional[float] = None
    structural_quality_grade: Optional[str] = None
    structural_hash: Optional[str] = None

    model_config = ConfigDict(extra="allow")

# =============================================================================
# TASK MODEL
# =============================================================================

class PlannedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., pattern=r'^[A-Za-z0-9_\-]+$', min_length=1, max_length=64)
    description: str = Field(..., min_length=3, max_length=SETTINGS.MAX_DESCRIPTION_LEN)
    task_type: TaskType = Field(default=TaskType.TOOL)
    tool_name: Optional[str] = Field(
        None,
        description="Required if task_type in (TOOL, TRANSFORM, AGGREGATE)."
    )
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    priority: int = Field(
        100,
        ge=SETTINGS.PRIORITY_MIN,
        le=SETTINGS.PRIORITY_MAX,
        description="Lower value means higher scheduling priority."
    )
    criticality: Criticality = Field(default=Criticality.BLOCKING)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    allow_high_risk: bool = Field(False, description="Must be True if risk_level=HIGH.")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    gate_condition: Optional[str] = Field(
        None,
        description="Expression required for GATE tasks (evaluated by policy layer)."
    )

    @field_validator("tool_name")
    def _tool_required_if_needed(cls, v, info):
        ttype = info.data.get("task_type")
        if ttype in {TaskType.TOOL, TaskType.TRANSFORM, TaskType.AGGREGATE} and not v:
            raise ValueError(f"tool_name is required for task_type={ttype}")
        return v

    @field_validator("dependencies")
    def _no_self_dependency(cls, v, info):
        tid = info.data.get("task_id")
        if tid and tid in v:
            raise ValueError(f"Task '{tid}' cannot depend on itself.")
        return v

    @field_validator("metadata")
    def _metadata_limit(cls, v):
        if len(v) > SETTINGS.MAX_METADATA_KEYS:
            raise ValueError(f"metadata key count {len(v)} exceeds {SETTINGS.MAX_METADATA_KEYS}.")
        return v

    @field_validator("tool_args")
    def _tool_args_limits_and_registry(cls, v, info):
        if len(v) > SETTINGS.MAX_TOOL_ARGS_KEYS:
            raise ValueError(f"tool_args key count {len(v)} exceeds {SETTINGS.MAX_TOOL_ARGS_KEYS}.")
        size = len(json.dumps(v, ensure_ascii=False))
        if size > SETTINGS.MAX_SERIALIZED_TOOL_ARGS_BYTES:
            raise ValueError(
                f"tool_args serialized size {size} > {SETTINGS.MAX_SERIALIZED_TOOL_ARGS_BYTES} bytes."
            )
        tool_name = info.data.get("tool_name")
        if tool_name and TOOL_REGISTRY and TOOL_REGISTRY.has(tool_name):
            try:
                return TOOL_REGISTRY.validate(tool_name, v)
            except Exception as ex:
                raise ValueError(f"tool_args validation failed for tool '{tool_name}': {ex}")
        return v

    @field_validator("risk_level")
    def _risk_gate(cls, v, info):
        if v == RiskLevel.HIGH and not info.data.get("allow_high_risk"):
            raise ValueError("HIGH risk task declared without allow_high_risk=True.")
        return v

    @field_validator("gate_condition")
    def _gate_condition_only_for_gate(cls, v, info):
        if v and info.data.get("task_type") != TaskType.GATE:
            raise ValueError("gate_condition only allowed when task_type=GATE.")
        return v

# =============================================================================
# PLANNING CONTEXT (Optional, may be passed to planners)
# =============================================================================

class PlanningContext(BaseModel):
    user_id: Optional[str] = None
    past_failures: List[str] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

# =============================================================================
# MISSION PLAN MODEL
# =============================================================================

class MissionPlanSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    revision: int = Field(default=1, ge=1)
    objective: str = Field(..., min_length=3)
    tasks: List[PlannedTask] = Field(...)

    meta: Optional[PlanMeta] = Field(
        default=None,
        description="Dynamic telemetry / semantic guidance produced by planner (extended structural metrics)."
    )

    topological_order: Optional[List[str]] = Field(default=None)
    stats: Optional[Dict[str, Any]] = Field(default=None)
    warnings: Optional[List[PlanWarning]] = Field(default=None)
    content_hash: Optional[str] = Field(default=None)
    structural_hash: Optional[str] = Field(default=None)

    # internal
    _adjacency: Dict[str, List[str]] = {}
    _indegree: Dict[str, int] = {}
    _depth_map: Dict[str, int] = {}

    @model_validator(mode="after")
    def _full_graph_validation(self):
        issues: List[PlanValidationIssue] = []
        warnings: List[PlanWarning] = []

        # Basic tasks existence
        if not self.tasks:
            issues.append(PlanValidationIssue(code="EMPTY_PLAN", message="Plan has no tasks."))
            raise PlanValidationError(issues)

        if len(self.tasks) > SETTINGS.MAX_TASKS:
            issues.append(PlanValidationIssue(
                code="TOO_MANY_TASKS",
                message=f"Task count {len(self.tasks)} exceeds MAX_TASKS={SETTINGS.MAX_TASKS}"
            ))
            raise PlanValidationError(issues)

        # Unique task IDs
        id_map = {t.task_id: t for t in self.tasks}
        if len(id_map) != len(self.tasks):
            issues.append(PlanValidationIssue(code="DUPLICATE_ID", message="Duplicate task_id detected."))
            raise PlanValidationError(issues)

        # Build adjacency / indegree
        adj: Dict[str, List[str]] = {tid: [] for tid in id_map}
        indegree: Dict[str, int] = {tid: 0 for tid in id_map}
        for t in self.tasks:
            for dep in t.dependencies:
                if dep not in id_map:
                    issues.append(PlanValidationIssue(
                        code="INVALID_DEPENDENCY",
                        message=f"Task '{t.task_id}' depends on unknown '{dep}'.",
                        task_id=t.task_id
                    ))
                else:
                    adj[dep].append(t.task_id)
                    indegree[t.task_id] += 1
        if issues:
            raise PlanValidationError(issues)

        # Fan-out limit
        for parent, children in adj.items():
            if len(children) > SETTINGS.MAX_OUT_DEGREE:
                issues.append(PlanValidationIssue(
                    code="EXCESS_OUT_DEGREE",
                    message=f"Task '{parent}' fan-out {len(children)} > MAX_OUT_DEGREE={SETTINGS.MAX_OUT_DEGREE}",
                    task_id=parent
                ))
        if issues:
            raise PlanValidationError(issues)

        # Topological sort
        import collections
        queue = collections.deque([tid for tid, deg in indegree.items() if deg == 0])
        if not queue:
            issues.append(PlanValidationIssue(code="NO_ROOTS", message="No root tasks (possible cycle)."))
            raise PlanValidationError(issues)

        topo: List[str] = []
        depth_map: Dict[str, int] = {tid: 0 for tid in id_map}
        remaining = indegree.copy()

        while queue:
            node = queue.popleft()
            topo.append(node)
            for nxt in adj[node]:
                remaining[nxt] -= 1
                depth_map[nxt] = max(depth_map[nxt], depth_map[node] + 1)
                if remaining[nxt] == 0:
                    queue.append(nxt)

        if len(topo) != len(id_map):
            cyclic_nodes = [tid for tid, d in remaining.items() if d > 0]
            issues.append(PlanValidationIssue(
                code="CYCLE_DETECTED",
                message="Dependency cycle detected.",
                detail={"nodes": cyclic_nodes}
            ))
            raise PlanValidationError(issues)

        longest_path = max(depth_map.values()) if depth_map else 0
        if longest_path > SETTINGS.MAX_DEPTH:
            issues.append(PlanValidationIssue(
                code="DEPTH_EXCEEDED",
                message=f"Depth {longest_path} > MAX_DEPTH={SETTINGS.MAX_DEPTH}"
            ))
            raise PlanValidationError(issues)

        # Heuristic Warnings
        roots = [tid for tid, deg in indegree.items() if deg == 0]
        if len(roots) / len(id_map) > 0.5 and len(id_map) > 10:
            warnings.append(PlanWarning(
                code="HIGH_ROOT_COUNT",
                message="More than 50% of tasks are roots.",
                severity=WarningSeverity.STRUCTURE
            ))
        for tid in id_map:
            if indegree[tid] == 0 and not adj[tid] and len(id_map) > 1:
                warnings.append(PlanWarning(
                    code="ORPHAN_TASK",
                    message=f"Task '{tid}' is isolated.",
                    severity=WarningSeverity.STRUCTURE,
                    task_id=tid
                ))
        priorities = [t.priority for t in self.tasks]
        if len(priorities) > 5 and len(set(priorities)) == 1:
            warnings.append(PlanWarning(
                code="UNIFORM_PRIORITY",
                message="All tasks share identical priority.",
                severity=WarningSeverity.PERFORMANCE
            ))
        high_risk = [t.task_id for t in self.tasks if t.risk_level == RiskLevel.HIGH]
        if high_risk and len(high_risk) / len(self.tasks) > 0.3:
            warnings.append(PlanWarning(
                code="HIGH_RISK_DENSITY",
                message=f"High-risk tasks ratio {len(high_risk)}/{len(self.tasks)} > 0.3.",
                severity=WarningSeverity.RISK
            ))
        for t in self.tasks:
            if t.task_type == TaskType.GATE and not t.gate_condition:
                warnings.append(PlanWarning(
                    code="GATE_WITHOUT_CONDITION",
                    message=f"GATE task '{t.task_id}' missing gate_condition.",
                    severity=WarningSeverity.ADVISORY,
                    task_id=t.task_id
                ))

        # Stats construction
        risk_counts = {
            "LOW": sum(1 for t in self.tasks if t.risk_level == RiskLevel.LOW),
            "MEDIUM": sum(1 for t in self.tasks if t.risk_level == RiskLevel.MEDIUM),
            "HIGH": len(high_risk)
        }
        risk_score = (
            risk_counts["LOW"] * 1 +
            risk_counts["MEDIUM"] * 3 +
            risk_counts["HIGH"] * 7
        )
        out_degrees = [len(v) for v in adj.values()]
        avg_fanout = round(sum(out_degrees)/len(out_degrees), 4) if out_degrees else 0.0

        stats = {
            "tasks": len(id_map),
            "roots": len(roots),
            "longest_path": longest_path,
            "avg_out_degree": avg_fanout,
            "max_out_degree": max(out_degrees) if out_degrees else 0,
            "risk_counts": risk_counts,
            "risk_score": risk_score,
            "orphan_tasks": [w.task_id for w in warnings if w.code == "ORPHAN_TASK"],
        }

        # Enforce meta size limit (if meta present & limit > 0)
        if self.meta:
            meta_json = json.dumps(self.meta.model_dump(mode="json"), ensure_ascii=False)
            if SETTINGS.MAX_META_BYTES > 0 and len(meta_json.encode("utf-8")) > SETTINGS.MAX_META_BYTES:
                warnings.append(PlanWarning(
                    code="META_TRUNCATION_RISK",
                    message=f"PlanMeta size exceeds {SETTINGS.MAX_META_BYTES} bytes (consider pruning).",
                    severity=WarningSeverity.PERFORMANCE
                ))

        # Full content hash (semantic)
        hash_payload = {
            "objective": self.objective,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "task_type": t.task_type,
                    "tool_name": t.tool_name,
                    "tool_args": t.tool_args,
                    "dependencies": t.dependencies,
                    "priority": t.priority,
                    "criticality": t.criticality,
                    "risk_level": t.risk_level,
                    "allow_high_risk": t.allow_high_risk,
                    "tags": sorted(t.tags),
                    "metadata": t.metadata,
                    "gate_condition": t.gate_condition
                }
                for t in sorted(self.tasks, key=lambda x: x.task_id)
            ]
        }
        self.content_hash = hashlib.sha256(
            json.dumps(hash_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # Structural hash (topology + structural hints)
        structural_vector = [
            {
              "task_id": t.task_id,
              "deps": sorted(t.dependencies),
              "priority": t.priority,
              "risk": t.risk_level,
              "hotspot": bool(t.metadata.get("hotspot")),
              "layer": t.metadata.get("layer")
            }
            for t in sorted(self.tasks, key=lambda x: x.task_id)
        ]
        self.structural_hash = hashlib.sha256(
            json.dumps(structural_vector, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # Inject derived avg_task_fanout if meta present and missing
        if self.meta:
            if self.meta.avg_task_fanout is None:
                self.meta.avg_task_fanout = avg_fanout

            # Structural quality grade (heuristic) if absent
            try:
                if self.meta.structural_quality_grade is None:
                    hg = self.meta.hotspot_density or 0.0
                    ld = self.meta.layer_diversity or 0.0
                    rp = risk_score
                    grade_score = (ld * 0.5) + (1 - abs(hg - 0.25)) * 0.3 + (1 / (1 + rp)) * 0.2
                    if grade_score >= 0.75:
                        grade = "A"
                    elif grade_score >= 0.5:
                        grade = "B"
                    else:
                        grade = "C"
                    self.meta.structural_quality_grade = grade
            except Exception:
                pass

            # Fill meta.structural_hash if not supplied
            if self.meta.structural_hash is None:
                self.meta.structural_hash = self.structural_hash

        # Assign computed structures
        self.topological_order = topo
        self.stats = stats
        self.warnings = warnings or None
        self._adjacency = adj
        self._indegree = indegree
        self._depth_map = depth_map

        # Policy hooks
        for hook in _POLICY_HOOKS:
            hook(self)

        return self

    # Utility / export helpers
    def _add_warning(self, code: str, message: str,
                     severity: WarningSeverity = WarningSeverity.INFO,
                     task_id: Optional[str] = None,
                     detail: Optional[Dict[str, Any]] = None):
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(PlanWarning(
            code=code, message=message, severity=severity, task_id=task_id, detail=detail
        ))

    def get_task(self, task_id: str) -> Optional[PlannedTask]:
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def parents_of(self, task_id: str) -> List[str]:
        t = self.get_task(task_id)
        return list(t.dependencies) if t else []

    def children_of(self, task_id: str) -> List[str]:
        return self._adjacency.get(task_id, [])

    def indegree(self, task_id: str) -> int:
        return self._indegree.get(task_id, 0)

    def depth_of(self, task_id: str) -> int:
        return self._depth_map.get(task_id, 0)

    def roots(self) -> List[str]:
        return [tid for tid, deg in self._indegree.items() if deg == 0]

    def leaves(self) -> List[str]:
        return [tid for tid, children in self._adjacency.items() if not children]

    def to_mermaid(self) -> str:
        lines = ["flowchart TD"]
        for parent, children in self._adjacency.items():
            if not children:
                lines.append(f"    {parent}[{parent}]")
            for child in children:
                lines.append(f"    {parent}[{parent}] --> {child}[{child}]")
        return "\n".join(lines)

    def to_d3_json(self) -> Dict[str, Any]:
        return {
            "nodes": [{"id": t.task_id, "depth": self.depth_of(t.task_id)} for t in self.tasks],
            "links": [
                {"source": dep, "target": t.task_id}
                for t in self.tasks
                for dep in t.dependencies
            ],
            "objective": self.objective,
            "stats": self.stats,
            "warnings": [w.model_dump() for w in self.warnings] if self.warnings else [],
            "meta": self.meta.model_dump() if self.meta else None
        }

    def to_networkx(self):
        try:
            import networkx as nx  # type: ignore
        except ImportError:  # pragma: no cover
            return None
        g = nx.DiGraph()
        for t in self.tasks:
            g.add_node(t.task_id, priority=t.priority, risk=t.risk_level, criticality=t.criticality)
        for t in self.tasks:
            for dep in t.dependencies:
                g.add_edge(dep, t.task_id)
        return g

# =============================================================================
# OPTIONAL RESULT WRAPPER
# =============================================================================

class PlanGenerationResult(BaseModel):
    plan: MissionPlanSchema
    warnings: List[PlanWarning] = Field(default_factory=list)
    validation_issues: List[PlanValidationIssue] = Field(default_factory=list)

# =============================================================================
# PUBLIC HELPERS
# =============================================================================

def validate_plan(payload: Dict[str, Any]) -> MissionPlanSchema:
    return MissionPlanSchema.model_validate(payload)

# =============================================================================
# POLICY HOOKS (Samples / Governance)
# =============================================================================

def _sample_policy_high_risk_limit(plan: MissionPlanSchema):
    high_count = plan.stats.get("risk_counts", {}).get("HIGH", 0) if plan.stats else 0
    if high_count > 100:
        raise PlanValidationError([
            PlanValidationIssue(
                code="POLICY_HIGH_RISK_CAP",
                message=f"High-risk tasks {high_count} exceed cap (100)."
            )
        ])
    if high_count > 50:
        plan._add_warning(
            code="POLICY_HIGH_RISK_DENSE",
            message=f"High-risk tasks {high_count} exceed advisory threshold (50).",
            severity=WarningSeverity.RISK
        )

register_policy_hook(_sample_policy_high_risk_limit)

def _policy_structural_sanity(plan: MissionPlanSchema):
    meta = plan.meta
    if not meta:
        return
    # Hotspot density upper bound
    if meta.hotspot_density is not None and meta.hotspot_density > 0.55:
        plan._add_warning(
            code="HOTSPOT_DENSITY_HIGH",
            message=f"Hotspot density {meta.hotspot_density:.2f} > 0.55 (narrow structural focus).",
            severity=WarningSeverity.RISK
        )
    # Layer diversity low
    if meta.layer_diversity is not None and meta.layer_diversity < 0.15:
        plan._add_warning(
            code="LAYER_DIVERSITY_LOW",
            message=f"Layer diversity {meta.layer_diversity:.2f} < 0.15 (possible imbalance).",
            severity=WarningSeverity.STRUCTURE
        )
    # Structural entropy low
    if meta.structural_entropy is not None and meta.structural_entropy < 0.35:
        plan._add_warning(
            code="STRUCTURAL_ENTROPY_LOW",
            message=f"Structural entropy {meta.structural_entropy:.2f} < 0.35 (over-concentration risk).",
            severity=WarningSeverity.PERFORMANCE
        )

register_policy_hook(_policy_structural_sanity)

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "__schema_version__",
    "PlanSettings",
    "SETTINGS",
    "TaskType",
    "Criticality",
    "RiskLevel",
    "WarningSeverity",
    "PlanValidationIssue",
    "PlanWarning",
    "PlanValidationError",
    "ToolRegistryInterface",
    "TOOL_REGISTRY",
    "register_policy_hook",
    "PolicyHook",
    "PlanMeta",
    "PlannedTask",
    "PlanningContext",
    "MissionPlanSchema",
    "PlanGenerationResult",
    "validate_plan",
]