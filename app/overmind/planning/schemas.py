# app/overmind/planning/schemas.py
# """
========================================================================================
  PLANNING SCHEMAS CORE v4.0  (Unified / Single Source of Truth)
========================================================================================
الغرض PURPOSE:
    هذا الملف هو المصدر الوحيد (Single Authority) لجميع نماذج التخطيط المستخدمة
    عبر النظام (BasePlanner / LLM Planner / Factory / Public Facade).
    الهدف الأساسي الآن: إزالة الإزدواج (Duplicate Class Definitions) الذي كان
    يتسبب في فشل isinstance بسبب تعريفات fallback متعددة في ملفات أخرى.

أهم الإصلاحات / KEY FIXES vs النسخ السابقة:
    1. إضافة PlanningContext هنا (كان غائباً → سبب فشل الاستيراد → تفعيل fallbacks).
    2. تعريف موحّد لـ MissionPlanSchema / PlannedTask / PlanWarning / PlanValidationIssue /
       PlanGenerationResult في مكان واحد فقط.
    3. واجهة register_policy_hook + تنفيذ policy hooks بعد التحقق البنيوي.
    4. دعم تحذيرات وهيكلة متقدمة مع الحفاظ على التوافق (objective, tasks).
    5. عدم استعمال أي تعريف بديل في ملفات أخرى (يجب إزالة fallbacks هناك أو تركها
       لأنها لن تُفَعَّل الآن طالما هذا الملف يُستورد بنجاح).

ملاحظات تصميم:
    - جميع النماذج (ما عدا الإعدادات) مبنية على Pydantic BaseModel لتسهيل التحقق.
    - تم ضبط model_config(extra="forbid") لتفادي تسلل حقول غير متوقعة.
    - الأداء: التحقق البنيوي والرسومي (DAG) يجري مرة واحدة عند البناء.
    - قابل للتوسعة عبر Policy Hooks المضافة بـ register_policy_hook.

بيئة / ENV OVERRIDES (اختيارية):
    PLAN_MAX_TASKS, PLAN_MAX_DESCRIPTION_LEN, PLAN_MAX_METADATA_KEYS,
    PLAN_MAX_TOOL_ARGS_KEYS, PLAN_MAX_TOOL_ARGS_BYTES, PLAN_MAX_DEPTH,
    PLAN_MAX_OUT_DEGREE, PLAN_PRIORITY_MIN, PLAN_PRIORITY_MAX

========================================================================================
"""

from __future__ import annotations

import json
import hashlib
import os
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import (
    List, Dict, Any, Optional, Callable, Iterable, Set
)

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

__schema_version__ = "4.0.0"

# ======================================================================================
# SETTINGS (Environment Tunable)
# ======================================================================================

@dataclass
class PlanSettings:
    MAX_TASKS: int = int(os.environ.get("PLAN_MAX_TASKS", 800))
    MAX_DESCRIPTION_LEN: int = int(os.environ.get("PLAN_MAX_DESCRIPTION_LEN", 600))
    MAX_METADATA_KEYS: int = int(os.environ.get("PLAN_MAX_METADATA_KEYS", 30))
    MAX_TOOL_ARGS_KEYS: int = int(os.environ.get("PLAN_MAX_TOOL_ARGS_KEYS", 40))
    MAX_SERIALIZED_TOOL_ARGS_BYTES: int = int(os.environ.get("PLAN_MAX_TOOL_ARGS_BYTES", 24_000))
    MAX_DEPTH: int = int(os.environ.get("PLAN_MAX_DEPTH", 60))
    MAX_OUT_DEGREE: int = int(os.environ.get("PLAN_MAX_OUT_DEGREE", 80))
    PRIORITY_MIN: int = int(os.environ.get("PLAN_PRIORITY_MIN", 0))
    PRIORITY_MAX: int = int(os.environ.get("PLAN_PRIORITY_MAX", 1000))

SETTINGS = PlanSettings()

# ======================================================================================
# ENUMS
# ======================================================================================

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

# ======================================================================================
# VALIDATION ISSUE / WARNING / ERROR
# ======================================================================================

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
    """
    Raised when structural / semantic validation of a plan fails aggregating issues.
    """
    def __init__(self, issues: List[PlanValidationIssue]):
        self.issues = issues
        super().__init__(f"Plan validation failed with {len(issues)} issues.")
    def to_dict(self) -> Dict[str, Any]:
        return {"issues": [i.model_dump() for i in self.issues]}

# ======================================================================================
# TOOL REGISTRY (اختياري)
# ======================================================================================

class ToolRegistryInterface:
    """
    Expected external interface (optional):
        has(tool_name: str) -> bool
        validate(tool_name: str, args: dict) -> dict (may mutate / normalize)
    """
    def has(self, tool_name: str) -> bool:  # pragma: no cover
        return False
    def validate(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return args

TOOL_REGISTRY: Optional[ToolRegistryInterface] = None

# ======================================================================================
# POLICY HOOKS
# ======================================================================================

PolicyHook = Callable[['MissionPlanSchema'], None]
_POLICY_HOOKS: List[PolicyHook] = []

def register_policy_hook(hook: PolicyHook) -> None:
    """Register an external policy hook executed after base validation."""
    _POLICY_HOOKS.append(hook)

# ======================================================================================
# TASK MODEL
# ======================================================================================

class PlannedTask(BaseModel):
    """
    Represents a single atomic node in the mission plan DAG.
    """
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(
        ...,
        pattern=r'^[A-Za-z0-9_\-]+$',
        min_length=1,
        max_length=64,
        description="Unique identifier inside the plan."
    )
    description: str = Field(
        ...,
        min_length=3,
        max_length=SETTINGS.MAX_DESCRIPTION_LEN,
        description="Human + machine understandable task purpose."
    )
    task_type: TaskType = Field(default=TaskType.TOOL)
    tool_name: Optional[str] = Field(
        None,
        description="Required if task_type in (TOOL, TRANSFORM, AGGREGATE)."
    )
    tool_args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the underlying tool."
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Prerequisite task IDs."
    )
    priority: int = Field(
        100,
        ge=SETTINGS.PRIORITY_MIN,
        le=SETTINGS.PRIORITY_MAX,
        description="Lower number = higher scheduling priority."
    )
    criticality: Criticality = Field(
        default=Criticality.BLOCKING,
        description="BLOCKING gates downstream tasks; SOFT is non-blocking."
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Risk classification for governance / heuristics."
    )
    allow_high_risk: bool = Field(
        False,
        description="Must be True if risk_level=HIGH."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Free-form labels."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary structured info (cost, domain hints, etc.)."
    )
    gate_condition: Optional[str] = Field(
        None,
        description="Expression for GATE tasks; must evaluate to truthy for pass."
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
    def _tool_args_limited_and_validated(cls, v, info):
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
                raise ValueError(f"tool_args validation failed for '{tool_name}': {ex}")
        return v

    @field_validator("risk_level")
    def _risk_gate(cls, v, info):
        if v == RiskLevel.HIGH and not info.data.get("allow_high_risk"):
            raise ValueError("HIGH risk task declared without allow_high_risk=True.")
        return v

    @field_validator("gate_condition")
    def _gate_condition_only_for_gate(cls, v, info):
        if v and info.data.get("task_type") != TaskType.GATE:
            raise ValueError("gate_condition only allowed for task_type=GATE.")
        return v

# ======================================================================================
# PLANNING CONTEXT (مطلوب لمنع fallbacks)
# ======================================================================================

class PlanningContext(BaseModel):
    """
    Carries optional contextual enrichment into planners (user prefs, past failures).
    """
    user_id: Optional[str] = None
    past_failures: List[str] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

# ======================================================================================
# MISSION PLAN MODEL
# ======================================================================================

class MissionPlanSchema(BaseModel):
    """
    Validated mission plan DAG (objective + tasks + computed metadata).
    """
    model_config = ConfigDict(extra="forbid")

    # Identity
    plan_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this plan instance."
    )
    revision: int = Field(
        default=1,
        ge=1,
        description="Revision number (increment upon modifications)."
    )
    objective: str = Field(
        ...,
        min_length=3,
        description="High-level mission objective."
    )
    tasks: List[PlannedTask] = Field(
        ...,
        description="List of atomic tasks forming a DAG."
    )

    # Derived
    topological_order: Optional[List[str]] = Field(default=None)
    stats: Optional[Dict[str, Any]] = Field(default=None)
    warnings: Optional[List[PlanWarning]] = Field(default=None)
    content_hash: Optional[str] = Field(default=None)

    # Internal (non-serialized) structures
    _adjacency: Dict[str, List[str]] = {}
    _indegree: Dict[str, int] = {}
    _depth_map: Dict[str, int] = {}

    @model_validator(mode="after")
    def _full_graph_validation(self):
        issues: List[PlanValidationIssue] = []
        warnings: List[PlanWarning] = []

        if not self.tasks:
            issues.append(PlanValidationIssue(code="EMPTY_PLAN", message="Plan has no tasks."))
            raise PlanValidationError(issues)

        if len(self.tasks) > SETTINGS.MAX_TASKS:
            issues.append(
                PlanValidationIssue(
                    code="TOO_MANY_TASKS",
                    message=f"Task count {len(self.tasks)} > MAX_TASKS={SETTINGS.MAX_TASKS}"
                )
            )
            raise PlanValidationError(issues)

        # Unique IDs
        id_map: Dict[str, PlannedTask] = {t.task_id: t for t in self.tasks}
        if len(id_map) != len(self.tasks):
            issues.append(PlanValidationIssue(code="DUPLICATE_ID", message="Duplicate task_id found."))
            raise PlanValidationError(issues)

        # Build adjacency / indegree
        adj: Dict[str, List[str]] = {tid: [] for tid in id_map}
        indegree: Dict[str, int] = {tid: 0 for tid in id_map}
        for t in self.tasks:
            for dep in t.dependencies:
                if dep not in id_map:
                    issues.append(
                        PlanValidationIssue(
                            code="INVALID_DEPENDENCY",
                            message=f"Task '{t.task_id}' depends on unknown '{dep}'.",
                            task_id=t.task_id
                        )
                    )
                else:
                    adj[dep].append(t.task_id)
                    indegree[t.task_id] += 1
        if issues:
            raise PlanValidationError(issues)

        # Fan-out constraint
        for parent, children in adj.items():
            if len(children) > SETTINGS.MAX_OUT_DEGREE:
                issues.append(
                    PlanValidationIssue(
                        code="EXCESS_OUT_DEGREE",
                        message=f"Task '{parent}' fan-out {len(children)} > {SETTINGS.MAX_OUT_DEGREE}",
                        task_id=parent
                    )
                )
        if issues:
            raise PlanValidationError(issues)

        # Topological sort (Kahn)
        import collections
        queue = collections.deque([tid for tid, deg in indegree.items() if deg == 0])
        if not queue:
            issues.append(
                PlanValidationIssue(
                    code="NO_ROOTS",
                    message="No root tasks (indegree==0); implies cycle."
                )
            )
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
            issues.append(
                PlanValidationIssue(
                    code="CYCLE_DETECTED",
                    message="Cycle(s) detected in dependency graph.",
                    detail={"nodes": cyclic_nodes}
                )
            )
            raise PlanValidationError(issues)

        longest_path = max(depth_map.values()) if depth_map else 0
        if longest_path > SETTINGS.MAX_DEPTH:
            issues.append(
                PlanValidationIssue(
                    code="DEPTH_EXCEEDED",
                    message=f"Depth {longest_path} > MAX_DEPTH={SETTINGS.MAX_DEPTH}"
                )
            )
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
        if high_risk:
            if len(high_risk) / len(self.tasks) > 0.3:
                warnings.append(PlanWarning(
                    code="HIGH_RISK_DENSITY",
                    message=f"High-risk tasks ratio {len(high_risk)}/{len(self.tasks)} > 30%.",
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
        stats = {
            "tasks": len(id_map),
            "roots": len(roots),
            "longest_path": longest_path,
            "avg_out_degree": round(sum(out_degrees)/len(out_degrees), 3) if out_degrees else 0,
            "max_out_degree": max(out_degrees) if out_degrees else 0,
            "risk_counts": risk_counts,
            "risk_score": risk_score,
            "orphan_tasks": [w.task_id for w in warnings if w.code == "ORPHAN_TASK"],
        }

        # Content hash (objective + normalized tasks)
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

        # Assign computed
        self.topological_order = topo
        self.stats = stats
        self.warnings = warnings or None
        self._adjacency = adj
        self._indegree = indegree
        self._depth_map = depth_map

        # Execute policy hooks
        for hook in _POLICY_HOOKS:
            hook(self)

        return self

    # ----------------------------
    # Utility / Export helpers
    # ----------------------------
    def _add_warning(
        self,
        code: str,
        message: str,
        severity: WarningSeverity = WarningSeverity.INFO,
        task_id: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None
    ):
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
            "warnings": [w.model_dump() for w in self.warnings] if self.warnings else []
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

# ======================================================================================
# PLAN GENERATION RESULT (Optional wrapper)
# ======================================================================================

class PlanGenerationResult(BaseModel):
    plan: MissionPlanSchema
    warnings: List[PlanWarning] = Field(default_factory=list)
    validation_issues: List[PlanValidationIssue] = Field(default_factory=list)

# ======================================================================================
# PUBLIC HELPERS
# ======================================================================================

def validate_plan(payload: Dict[str, Any]) -> MissionPlanSchema:
    """
    Validate and return a MissionPlanSchema instance (raises PlanValidationError if invalid).
    """
    return MissionPlanSchema.model_validate(payload)

# ======================================================================================
# SAMPLE POLICY HOOK (Optional – can be disabled if undesired)
# ======================================================================================

def _sample_policy_high_risk_limit(plan: MissionPlanSchema):
    """
    Policy:
      - Hard fail if HIGH risk tasks > 100
      - Warning if HIGH risk tasks > 50
    """
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

# Register sample policy (يمكن تعطيله بإزالة هذا السطر)
register_policy_hook(_sample_policy_high_risk_limit)

# ======================================================================================
# __all__
# ======================================================================================

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
    "PlannedTask",
    "PlanningContext",
    "MissionPlanSchema",
    "PlanGenerationResult",
    "validate_plan",
]

# ======================================================================================
# END OF FILE
# ======================================================================================