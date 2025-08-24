# app/overmind/planning/schemas.py
# ======================================================================================
#  GENESIS PROTOCOL v2.1 – Strategic Orchestration Contract (Mission Planning DAG)
# ======================================================================================
#  Purpose:
#    Define the immutable CONTRACT for a validated, metric-rich Mission Plan. This is
#    a self-validating schema providing graph integrity (uniqueness, dependency,
#    acyclicity), risk awareness (criticality, risk), structural validation,
#    complexity metrics, topological order emission, and policy guardrails.
#
#  Key Features:
#    * Enums: TaskType, Criticality, RiskLevel
#    * Priority model (0 = highest urgency). Range-bounded for sanity.
#    * High-risk gating (must set allow_high_risk=True)
#    * Configurable structural limits (MAX_TASKS, MAX_DEPTH, MAX_OUT_DEGREE)
#    * Comprehensive graph validation: uniqueness, dependency integrity, cycle detection
#    * Automatic topological sort + graph metric computation (stats)
#    * Heuristic warning generation for non-fatal plan issues
#
#  EXTENSION POINTS
#    - TOOL_REGISTRY: inject object implementing has() and validate()
#
#  v2.1 refines names, adds tags, improved warnings & stats, consistent naming.
#
#  DISCLAIMER
#    رغم الخطاب الحماسي، هذا نموذج برمجي منضبط—not a warp drive :)
# ======================================================================================

from __future__ import annotations
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# --------------------------------------------------------------------------------------
# CONFIG LIMITS (يمكن تعديلها من إعدادات خارجية لاحقاً)
# --------------------------------------------------------------------------------------
MAX_TASKS: int = 800
MAX_DESCRIPTION_LEN: int = 600
MAX_METADATA_KEYS: int = 30
MAX_TOOL_ARGS_KEYS: int = 40
MAX_SERIALIZED_TOOL_ARGS_BYTES: int = 24_000    # ~24 KB (بعد JSON dump)
MAX_DEPTH: int = 60
MAX_OUT_DEGREE: int = 80
PRIORITY_MIN: int = 0
PRIORITY_MAX: int = 1000

# --------------------------------------------------------------------------------------
# ENUMS
# --------------------------------------------------------------------------------------
class TaskType(str, Enum):
    TOOL = "TOOL"
    VERIFY = "VERIFY"
    GATE = "GATE"
    TRANSFORM = "TRANSFORM"
    AGGREGATE = "AGGREGATE"

class Criticality(str, Enum):
    BLOCKING = "BLOCKING"
    SOFT = "SOFT"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

# --------------------------------------------------------------------------------------
# VALIDATION ISSUE & ERROR
# --------------------------------------------------------------------------------------
class PlanValidationIssue(BaseModel):
    code: str
    message: str
    task_id: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None

class PlanValidationError(ValueError):
    def __init__(self, issues: List[PlanValidationIssue]):
        self.issues = issues
        super().__init__(f"Plan validation failed with {len(issues)} issues.")

    def to_dict(self) -> Dict[str, Any]:
        return {"issues": [i.model_dump() for i in self.issues]}

# --------------------------------------------------------------------------------------
# TOOL REGISTRY INTERFACE (اختياري)
# --------------------------------------------------------------------------------------
class ToolRegistryInterface:
    """
    External component (plug-in).
    Expected methods:
        has(tool_name: str) -> bool
        validate(tool_name: str, args: dict) -> dict (returns normalized args or raises)
    """
    def has(self, tool_name: str) -> bool:  # pragma: no cover
        return False
    def validate(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return args
TOOL_REGISTRY: Optional[ToolRegistryInterface] = None

# --------------------------------------------------------------------------------------
# TASK MODEL
# --------------------------------------------------------------------------------------
class PlannedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="Unique identifier inside the plan (e.g., BUILD_INDEX, T42).", pattern=r'^[A-Z0-9_]+$')
    description: str = Field(..., description="Human + machine friendly purpose.", min_length=3, max_length=MAX_DESCRIPTION_LEN)
    task_type: TaskType = Field(default=TaskType.TOOL)
    tool_name: Optional[str] = Field(None, description="Required if task_type=TOOL/TRANSFORM/AGGREGATE uses a tool.")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the referenced tool (validated if registry present).")
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite task_ids.")
    priority: int = Field(100, ge=PRIORITY_MIN, le=PRIORITY_MAX, description="Lower = higher scheduling priority (bounded).")
    criticality: Criticality = Field(default=Criticality.BLOCKING, description="BLOCKING tasks gate downstream progress; SOFT tasks are optional.")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Declared risk classification.")
    tags: List[str] = Field(default_factory=list, description="Free-form classification labels.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary structured information (cost, domain hints, etc.).")
    allow_high_risk: bool = Field(False, description="Must be True if risk_level=HIGH.")

    @field_validator("tool_name")
    def enforce_tool_name_if_needed(cls, v, info):
        ttype = info.data.get("task_type")
        if ttype in {TaskType.TOOL, TaskType.TRANSFORM, TaskType.AGGREGATE} and not v:
            raise ValueError(f"tool_name is required for task_type={ttype}")
        return v

    @field_validator("dependencies")
    def prevent_self_dependency(cls, v, info):
        tid = info.data.get("task_id")
        if tid and tid in v:
            raise ValueError(f"Task '{tid}' cannot depend on itself.")
        return v

    @field_validator("metadata")
    def metadata_limit(cls, v):
        if len(v) > MAX_METADATA_KEYS:
            raise ValueError(f"metadata key count {len(v)} exceeds {MAX_METADATA_KEYS}.")
        return v

    @field_validator("tool_args")
    def tool_args_limits_and_registry(cls, v, info):
        if len(v) > MAX_TOOL_ARGS_KEYS:
            raise ValueError(f"tool_args key count {len(v)} exceeds {MAX_TOOL_ARGS_KEYS}.")
        import json
        size = len(json.dumps(v, ensure_ascii=False))
        if size > MAX_SERIALIZED_TOOL_ARGS_BYTES:
            raise ValueError(f"tool_args serialized size {size} > {MAX_SERIALIZED_TOOL_ARGS_BYTES} bytes.")
        tool_name = info.data.get("tool_name")
        if tool_name and TOOL_REGISTRY and TOOL_REGISTRY.has(tool_name):
            try:
                return TOOL_REGISTRY.validate(tool_name, v)
            except Exception as ex:
                raise ValueError(f"tool_args validation failed for tool '{tool_name}': {ex}")
        return v

    @field_validator("risk_level")
    def risk_gate(cls, v, info):
        if v == RiskLevel.HIGH and not info.data.get("allow_high_risk"):
            raise ValueError("HIGH risk task declared without allow_high_risk=True.")
        return v

# --------------------------------------------------------------------------------------
# PLAN MODEL
# --------------------------------------------------------------------------------------
class MissionPlanSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(..., min_length=3, description="High-level mission objective.")
    tasks: List[PlannedTask] = Field(..., description="List of tasks forming a DAG.")
    topological_order: Optional[List[str]] = Field(default=None, description="Computed valid execution order (if validation passes).")
    stats: Optional[Dict[str, Any]] = Field(default=None, description="Graph structural & risk metrics.")
    warnings: Optional[List[str]] = Field(default=None, description="Non-fatal heuristic warnings.")

    _adjacency: Dict[str, List[str]] = {}
    _indegree: Dict[str, int] = {}
    _depth_map: Dict[str, int] = {}

    @model_validator(mode="after")
    def full_graph_validation(self):
        issues: List[PlanValidationIssue] = []
        warnings: List[str] = []

        if not self.tasks:
            issues.append(PlanValidationIssue(code="EMPTY_PLAN", message="Plan has no tasks."))
            raise PlanValidationError(issues)
        if len(self.tasks) > MAX_TASKS:
            issues.append(PlanValidationIssue(code="TOO_MANY_TASKS", message=f"Task count {len(self.tasks)} exceeds MAX_TASKS={MAX_TASKS}"))
            raise PlanValidationError(issues)

        id_map: Dict[str, PlannedTask] = {t.task_id: t for t in self.tasks}
        if len(id_map) != len(self.tasks):
            issues.append(PlanValidationIssue(code="DUPLICATE_ID", message="Duplicate task_id found in plan."))
            raise PlanValidationError(issues)

        adj: Dict[str, List[str]] = {tid: [] for tid in id_map}
        indegree: Dict[str, int] = {tid: 0 for tid in id_map}
        for t in self.tasks:
            for dep in t.dependencies:
                if dep not in id_map:
                    issues.append(PlanValidationIssue(code="INVALID_DEPENDENCY", message=f"Task '{t.task_id}' depends on unknown task '{dep}'.", task_id=t.task_id))
                else:
                    adj[dep].append(t.task_id)
                    indegree[t.task_id] += 1
        if issues:
            raise PlanValidationError(issues)

        for parent, children in adj.items():
            if len(children) > MAX_OUT_DEGREE:
                issues.append(PlanValidationIssue(code="EXCESS_OUT_DEGREE", message=f"Task '{parent}' fan-out {len(children)} > MAX_OUT_DEGREE={MAX_OUT_DEGREE}", task_id=parent))
        if issues:
            raise PlanValidationError(issues)

        import collections
        queue = collections.deque([tid for tid, deg in indegree.items() if deg == 0])
        if not queue:
            issues.append(PlanValidationIssue(code="NO_ROOTS", message="No root tasks (all have indegree > 0) – implies cycle."))
            raise PlanValidationError(issues)

        topo: List[str] = []
        depth: Dict[str, int] = {tid: 0 for tid in id_map}
        remaining_indegree = indegree.copy()

        while queue:
            node = queue.popleft()
            topo.append(node)
            for nxt in adj[node]:
                remaining_indegree[nxt] -= 1
                depth[nxt] = max(depth[nxt], depth[node] + 1)
                if remaining_indegree[nxt] == 0:
                    queue.append(nxt)

        if len(topo) != len(id_map):
            cyclic_nodes = [tid for tid, d in remaining_indegree.items() if d > 0]
            issues.append(PlanValidationIssue(code="CYCLE_DETECTED", message="Cycle(s) detected in task graph.", detail={"nodes": cyclic_nodes}))
            raise PlanValidationError(issues)

        longest_path = max(depth.values()) if depth else 0
        if longest_path > MAX_DEPTH:
            issues.append(PlanValidationIssue(code="DEPTH_EXCEEDED", message=f"Computed depth {longest_path} > MAX_DEPTH={MAX_DEPTH}"))
            raise PlanValidationError(issues)

        roots = [tid for tid, deg in indegree.items() if deg == 0]
        if len(roots) / len(id_map) > 0.5 and len(id_map) > 10:
            warnings.append("HIGH_ROOT_COUNT: More than 50% of tasks are roots; consider consolidation or staging.")

        for tid, task in id_map.items():
            if not task.dependencies and not adj[tid] and len(id_map) > 1:
                warnings.append(f"ORPHAN_TASK: Task '{tid}' is isolated (no parents, no children).")

        priorities = [t.priority for t in self.tasks]
        if len(set(priorities)) == 1 and len(priorities) > 5:
            warnings.append("UNIFORM_PRIORITY: All tasks share identical priority; may reduce scheduler discrimination.")

        high_risk_tasks = [t.task_id for t in self.tasks if t.risk_level == RiskLevel.HIGH]
        if high_risk_tasks and not any(t.allow_high_risk for t in self.tasks if t.task_id in high_risk_tasks):
            warnings.append(f"HIGH_RISK_PRESENT: {len(high_risk_tasks)} high-risk tasks present without explicit `allow_high_risk` context.")

        out_degrees = [len(v) for v in adj.values()]
        stats = {
            "tasks": len(id_map),
            "roots": len(roots),
            "longest_path": longest_path,
            "avg_out_degree": round(sum(out_degrees) / len(out_degrees), 3) if out_degrees else 0,
            "max_out_degree": max(out_degrees) if out_degrees else 0,
            "high_risk_tasks": len(high_risk_tasks),
        }

        self.topological_order = topo
        self.stats = stats
        self.warnings = warnings or None
        self._adjacency = adj
        self._indegree = {k: sum(1 for t in self.tasks if k in t.dependencies) for k in id_map}
        self._depth_map = depth
        return self

    def get_task(self, task_id: str) -> Optional[PlannedTask]:
        return next((t for t in self.tasks if t.task_id == task_id), None)
    
    def parents_of(self, task_id: str) -> List[str]:
        t = self.get_task(task_id)
        return t.dependencies[:] if t else []
    
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

# --------------------------------------------------------------------------------------
# PUBLIC HELPER
# --------------------------------------------------------------------------------------
def validate_plan(payload: Dict[str, Any]) -> MissionPlanSchema:
    """
    Validate and return a MissionPlanSchema instance.
    Raises PlanValidationError on violations.
    """
    return MissionPlanSchema.model_validate(payload)