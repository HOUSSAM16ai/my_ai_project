# 🚀 خطة إعادة الهيكلة الخارقة للدوال الضخمة

## 📊 التشخيص الدقيق

### الدوال الكارثية المكتشفة:

| الدالة | CC | LOC | الملف | الدرجة |
|--------|-----|-----|-------|--------|
| `_full_graph_validation` | 44 | 230 | `schemas.py` | F |
| `execute_task` | 43 | 220 | `generation_service.py` | F |
| `answer_question` | 41 | 434 | `admin_ai_service.py` | F |
| `generate_plan` | 40 | 260 | `llm_planner.py` | E |
| `_execute_task_with_retry_topological` | 39 | 135 | `master_agent_service.py` | E |

---

## 🎯 الاستراتيجية الخارقة: ATOMIC DECOMPOSITION

### المبادئ الأساسية:

```
┌─────────────────────────────────────────────────┐
│  🧬 ATOMIC DECOMPOSITION PATTERN                │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. دالة واحدة = مسؤولية واحدة (SRP)           │
│  2. CC ≤ 5 لكل دالة                            │
│  3. LOC ≤ 50 لكل دالة                          │
│  4. عمق التداخل ≤ 2                            │
│  5. معاملات ≤ 4                                │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔬 التقنيات المتقدمة

### 1️⃣ **Extract Method Pattern** (استخراج الدوال)

```python
# ❌ قبل: CC=44
def _full_graph_validation(self):
    # 230 سطر من الكود المعقد
    pass

# ✅ بعد: CC≤5 لكل دالة
def _full_graph_validation(self):
    """Orchestrator - ينسق فقط"""
    issues, warnings = [], []
    
    self._validate_basic_constraints(issues)
    self._validate_task_uniqueness(issues)
    graph_data = self._build_graph_structure(issues)
    self._validate_topology(graph_data, issues, warnings)
    self._validate_depth_and_fanout(graph_data, issues)
    self._generate_heuristic_warnings(graph_data, warnings)
    stats = self._compute_statistics(graph_data)
    self._compute_hashes(stats)
    
    return issues, warnings, stats
```

### 2️⃣ **Strategy Pattern** (نمط الاستراتيجية)

```python
# للتحقق من الصحة المختلفة
class ValidationStrategy(Protocol):
    def validate(self, plan: Plan) -> list[Issue]:
        ...

class BasicConstraintsValidator:
    def validate(self, plan: Plan) -> list[Issue]:
        # CC=3
        pass

class TopologyValidator:
    def validate(self, plan: Plan) -> list[Issue]:
        # CC=4
        pass

class GraphValidator:
    def __init__(self):
        self.validators = [
            BasicConstraintsValidator(),
            TopologyValidator(),
            DepthValidator(),
            FanoutValidator(),
        ]
    
    def validate_all(self, plan: Plan) -> list[Issue]:
        # CC=2
        issues = []
        for validator in self.validators:
            issues.extend(validator.validate(plan))
        return issues
```

### 3️⃣ **Pipeline Pattern** (نمط خط الأنابيب)

```python
from typing import Callable, TypeVar

T = TypeVar('T')

class ValidationPipeline:
    """Pipeline pattern for sequential validation"""
    
    def __init__(self):
        self.steps: list[Callable] = []
    
    def add_step(self, step: Callable) -> 'ValidationPipeline':
        self.steps.append(step)
        return self
    
    def execute(self, data: T) -> T:
        # CC=2
        for step in self.steps:
            data = step(data)
        return data

# الاستخدام
pipeline = (
    ValidationPipeline()
    .add_step(validate_basic)
    .add_step(validate_topology)
    .add_step(validate_depth)
    .add_step(compute_stats)
)
result = pipeline.execute(plan)
```

### 4️⃣ **Builder Pattern** (نمط البناء)

```python
class GraphDataBuilder:
    """Builds graph data structures incrementally"""
    
    def __init__(self, tasks: list[Task]):
        self.tasks = tasks
        self.adjacency: dict[str, list[str]] = {}
        self.indegree: dict[str, int] = {}
        self.id_map: dict[str, Task] = {}
    
    def build_id_map(self) -> 'GraphDataBuilder':
        # CC=2
        self.id_map = {t.task_id: t for t in self.tasks}
        return self
    
    def build_adjacency(self) -> 'GraphDataBuilder':
        # CC=3
        self.adjacency = {tid: [] for tid in self.id_map}
        for task in self.tasks:
            for dep in task.dependencies:
                if dep in self.id_map:
                    self.adjacency[dep].append(task.task_id)
        return self
    
    def build_indegree(self) -> 'GraphDataBuilder':
        # CC=3
        self.indegree = {tid: 0 for tid in self.id_map}
        for task in self.tasks:
            for dep in task.dependencies:
                if dep in self.id_map:
                    self.indegree[task.task_id] += 1
        return self
    
    def build(self) -> GraphData:
        # CC=1
        return GraphData(
            adjacency=self.adjacency,
            indegree=self.indegree,
            id_map=self.id_map,
        )

# الاستخدام
graph_data = (
    GraphDataBuilder(tasks)
    .build_id_map()
    .build_adjacency()
    .build_indegree()
    .build()
)
```

### 5️⃣ **Command Pattern** (نمط الأوامر)

```python
class ValidationCommand(Protocol):
    def execute(self) -> ValidationResult:
        ...

class ValidateBasicConstraints(ValidationCommand):
    def __init__(self, plan: Plan):
        self.plan = plan
    
    def execute(self) -> ValidationResult:
        # CC=4
        issues = []
        if not self.plan.tasks:
            issues.append(Issue("EMPTY_PLAN"))
        if len(self.plan.tasks) > MAX_TASKS:
            issues.append(Issue("TOO_MANY_TASKS"))
        return ValidationResult(issues=issues)

class ValidateTopology(ValidationCommand):
    def __init__(self, graph_data: GraphData):
        self.graph_data = graph_data
    
    def execute(self) -> ValidationResult:
        # CC=5
        return self._run_topological_sort()

class ValidationExecutor:
    def __init__(self):
        self.commands: list[ValidationCommand] = []
    
    def add_command(self, cmd: ValidationCommand):
        self.commands.append(cmd)
    
    def execute_all(self) -> list[ValidationResult]:
        # CC=2
        return [cmd.execute() for cmd in self.commands]
```

---

## 🏗️ خطة التنفيذ التفصيلية

### المرحلة 1: تفكيك `_full_graph_validation`

```
_full_graph_validation (CC=44, LOC=230)
    ↓
    ├─ _validate_basic_constraints (CC=4, LOC=25)
    ├─ _validate_task_uniqueness (CC=3, LOC=15)
    ├─ _build_graph_structure (CC=5, LOC=40)
    │   ├─ _build_adjacency_list (CC=3, LOC=15)
    │   ├─ _build_indegree_map (CC=3, LOC=15)
    │   └─ _validate_dependencies (CC=4, LOC=20)
    ├─ _validate_topology (CC=5, LOC=50)
    │   ├─ _find_roots (CC=2, LOC=10)
    │   ├─ _topological_sort (CC=4, LOC=30)
    │   └─ _detect_cycles (CC=3, LOC=20)
    ├─ _validate_depth_and_fanout (CC=4, LOC=30)
    │   ├─ _compute_depth_map (CC=3, LOC=20)
    │   └─ _validate_fanout (CC=3, LOC=15)
    ├─ _generate_heuristic_warnings (CC=5, LOC=45)
    │   ├─ _check_root_density (CC=2, LOC=10)
    │   ├─ _check_orphan_tasks (CC=3, LOC=15)
    │   ├─ _check_priority_uniformity (CC=3, LOC=12)
    │   └─ _check_risk_density (CC=3, LOC=15)
    ├─ _compute_statistics (CC=4, LOC=35)
    │   ├─ _compute_risk_score (CC=3, LOC=15)
    │   └─ _compute_fanout_stats (CC=2, LOC=12)
    └─ _compute_hashes (CC=3, LOC=30)
        ├─ _compute_content_hash (CC=2, LOC=15)
        └─ _compute_structural_hash (CC=2, LOC=15)
```

### المرحلة 2: إنشاء Data Classes

```python
from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass
class GraphData:
    """Immutable graph structure"""
    adjacency: dict[str, list[str]]
    indegree: dict[str, int]
    id_map: dict[str, Task]
    
    @property
    def roots(self) -> list[str]:
        return [tid for tid, deg in self.indegree.items() if deg == 0]
    
    @property
    def task_count(self) -> int:
        return len(self.id_map)

@dataclass
class ValidationContext:
    """Context for validation operations"""
    plan: Plan
    graph_data: GraphData
    issues: list[Issue]
    warnings: list[Warning]
    settings: PlanSettings

@dataclass
class ValidationResult:
    """Result of validation"""
    issues: list[Issue]
    warnings: list[Warning]
    stats: dict[str, Any]
    is_valid: bool
```

### المرحلة 3: إنشاء Validators منفصلة

```python
# app/overmind/planning/validators/__init__.py
from .basic_validator import BasicConstraintsValidator
from .topology_validator import TopologyValidator
from .depth_validator import DepthValidator
from .fanout_validator import FanoutValidator
from .heuristic_validator import HeuristicValidator

__all__ = [
    "BasicConstraintsValidator",
    "TopologyValidator",
    "DepthValidator",
    "FanoutValidator",
    "HeuristicValidator",
]
```

```python
# app/overmind/planning/validators/basic_validator.py
class BasicConstraintsValidator:
    """Validates basic plan constraints"""
    
    def __init__(self, settings: PlanSettings):
        self.settings = settings
    
    def validate(self, plan: Plan) -> list[Issue]:
        """CC=4"""
        issues = []
        
        if not plan.tasks:
            issues.append(Issue("EMPTY_PLAN", "Plan has no tasks"))
        
        if len(plan.tasks) > self.settings.MAX_TASKS:
            issues.append(
                Issue(
                    "TOO_MANY_TASKS",
                    f"Task count {len(plan.tasks)} exceeds {self.settings.MAX_TASKS}"
                )
            )
        
        return issues
```

```python
# app/overmind/planning/validators/topology_validator.py
from collections import deque

class TopologyValidator:
    """Validates graph topology"""
    
    def validate(self, graph_data: GraphData) -> tuple[list[Issue], dict]:
        """CC=5"""
        issues = []
        
        roots = self._find_roots(graph_data)
        if not roots:
            issues.append(Issue("NO_ROOTS", "No root tasks found"))
            return issues, {}
        
        topo_order, depth_map = self._topological_sort(graph_data, roots)
        
        if len(topo_order) != graph_data.task_count:
            cyclic = self._find_cyclic_nodes(graph_data, topo_order)
            issues.append(
                Issue("CYCLE_DETECTED", "Dependency cycle", detail={"nodes": cyclic})
            )
        
        return issues, {"topo_order": topo_order, "depth_map": depth_map}
    
    def _find_roots(self, graph_data: GraphData) -> list[str]:
        """CC=2"""
        return [tid for tid, deg in graph_data.indegree.items() if deg == 0]
    
    def _topological_sort(
        self, graph_data: GraphData, roots: list[str]
    ) -> tuple[list[str], dict[str, int]]:
        """CC=4"""
        queue = deque(roots)
        topo_order = []
        depth_map = {tid: 0 for tid in graph_data.id_map}
        remaining = graph_data.indegree.copy()
        
        while queue:
            node = queue.popleft()
            topo_order.append(node)
            
            for child in graph_data.adjacency[node]:
                remaining[child] -= 1
                depth_map[child] = max(depth_map[child], depth_map[node] + 1)
                
                if remaining[child] == 0:
                    queue.append(child)
        
        return topo_order, depth_map
    
    def _find_cyclic_nodes(
        self, graph_data: GraphData, topo_order: list[str]
    ) -> list[str]:
        """CC=2"""
        processed = set(topo_order)
        return [tid for tid in graph_data.id_map if tid not in processed]
```

---

## 🎨 الأنماط المعمارية المتقدمة

### 1. **Hexagonal Architecture** (المعمارية السداسية)

```
┌─────────────────────────────────────────┐
│           Application Core              │
│  ┌───────────────────────────────────┐  │
│  │   Domain Models (Plan, Task)      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Use Cases (ValidatePlan)        │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ↑                    ↑
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │ Ports   │          │ Ports   │
    └────┬────┘          └────┬────┘
         │                    │
         ↓                    ↓
┌─────────────────┐  ┌─────────────────┐
│    Adapters     │  │    Adapters     │
│  (Validators)   │  │  (Repositories) │
└─────────────────┘  └─────────────────┘
```

### 2. **CQRS Pattern** (فصل القراءة والكتابة)

```python
# Commands (Write)
class ValidatePlanCommand:
    def __init__(self, plan: Plan):
        self.plan = plan

class ValidatePlanHandler:
    def handle(self, command: ValidatePlanCommand) -> ValidationResult:
        # CC=3
        pass

# Queries (Read)
class GetPlanStatisticsQuery:
    def __init__(self, plan_id: str):
        self.plan_id = plan_id

class GetPlanStatisticsHandler:
    def handle(self, query: GetPlanStatisticsQuery) -> PlanStatistics:
        # CC=2
        pass
```

### 3. **Event-Driven Architecture** (المعمارية الموجهة بالأحداث)

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DomainEvent:
    event_id: str
    timestamp: datetime
    event_type: str

@dataclass
class PlanValidated(DomainEvent):
    plan_id: str
    is_valid: bool
    issues_count: int

@dataclass
class CycleDetected(DomainEvent):
    plan_id: str
    cyclic_nodes: list[str]

class EventBus:
    def __init__(self):
        self.handlers: dict[str, list[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        # CC=2
        for handler in self.handlers.get(event.event_type, []):
            handler(event)
```

---

## 📐 معايير الجودة المستهدفة

```
┌──────────────────────────────────────────────┐
│  🎯 معايير الجودة بعد إعادة الهيكلة        │
├──────────────────────────────────────────────┤
│                                              │
│  ✅ Cyclomatic Complexity ≤ 5               │
│  ✅ Lines of Code ≤ 50                      │
│  ✅ Nesting Depth ≤ 2                       │
│  ✅ Parameters ≤ 4                          │
│  ✅ Test Coverage ≥ 95%                     │
│  ✅ Maintainability Index ≥ 85              │
│  ✅ Code Duplication < 3%                   │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🚀 خطة التنفيذ الزمنية

### الأسبوع 1: التحضير
- ✅ تحليل الدوال الحالية
- ✅ تصميم المعمارية الجديدة
- ✅ إنشاء Data Classes
- ✅ كتابة الاختبارات للدوال الحالية

### الأسبوع 2: التفكيك
- 🔄 تفكيك `_full_graph_validation`
- 🔄 تفكيك `execute_task`
- 🔄 تفكيك `answer_question`

### الأسبوع 3: التحسين
- 🔄 تطبيق Strategy Pattern
- 🔄 تطبيق Pipeline Pattern
- 🔄 تطبيق Builder Pattern

### الأسبوع 4: الاختبار والتوثيق
- 🔄 كتابة اختبارات شاملة
- 🔄 قياس التحسينات
- 🔄 توثيق الأنماط الجديدة

---

## 📊 النتائج المتوقعة

```
┌────────────────────────────────────────────────────┐
│           قبل → بعد إعادة الهيكلة                 │
├────────────────────────────────────────────────────┤
│                                                    │
│  Cyclomatic Complexity:  44 → 5  (↓ 88%)         │
│  Lines of Code:          230 → 50 (↓ 78%)        │
│  Test Coverage:          ~30% → 95% (↑ 217%)     │
│  Maintainability:        F → A (↑ 500%)          │
│  Bug Density:            High → Low (↓ 90%)      │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 🎓 المراجع والمصادر

1. **Clean Code** - Robert C. Martin
2. **Refactoring** - Martin Fowler
3. **Design Patterns** - Gang of Four
4. **Domain-Driven Design** - Eric Evans
5. **Building Microservices** - Sam Newman

---

## ✅ Checklist للتنفيذ

- [ ] تحليل الدالة المستهدفة
- [ ] تحديد المسؤوليات المنفصلة
- [ ] إنشاء Data Classes
- [ ] استخراج الدوال الصغيرة
- [ ] تطبيق الأنماط المعمارية
- [ ] كتابة الاختبارات
- [ ] قياس التحسينات
- [ ] توثيق التغييرات
- [ ] مراجعة الكود
- [ ] الدمج في الفرع الرئيسي

---

**تم إنشاء هذه الخطة بواسطة:** Ona AI Agent  
**التاريخ:** 2025-12-06  
**الإصدار:** 1.0.0
