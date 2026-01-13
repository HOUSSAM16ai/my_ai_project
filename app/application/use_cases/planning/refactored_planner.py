"""Refactored planner using clean architecture."""

from dataclasses import dataclass

from app.core.protocols import PlannerProtocol as PlannerInterface
from app.infrastructure.patterns import EventBus, get_event_bus


@dataclass
class Task:
    """Task entity."""

    task_id: str
    description: str
    tool_name: str
    tool_args: dict[str, object]
    dependencies: list[str]


@dataclass
class Plan:
    """Plan entity."""

    plan_id: str
    objective: str
    tasks: list[Task]
    metadata: dict[str, object]


class PlanValidator:
    """Validates plans."""

    def validate(self, plan: Plan) -> tuple[bool, list[str]]:
        """Validate plan structure and dependencies."""
        errors = []

        if not plan.objective:
            errors.append("Objective is required")

        if not plan.tasks:
            errors.append("Plan must have at least one task")

        task_ids = {task.task_id for task in plan.tasks}
        for task in plan.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task {task.task_id} has invalid dependency: {dep}")

        return len(errors) == 0, errors


class PlanOptimizer:
    """Optimizes plan execution order."""

    def optimize(self, plan: Plan) -> Plan:
        """Optimize task order based on dependencies."""
        sorted_tasks = self._topological_sort(plan.tasks)
        return Plan(
            plan_id=plan.plan_id,
            objective=plan.objective,
            tasks=sorted_tasks,
            metadata={**plan.metadata, "optimized": True},
        )

    def _topological_sort(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks topologically."""
        task_map = {task.task_id: task for task in tasks}
        visited = set()
        result = []

        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            visited.add(task_id)

            task = task_map[task_id]
            for dep in task.dependencies:
                if dep in task_map:
                    visit(dep)

            result.append(task)

        for task in tasks:
            visit(task.task_id)

        return result


class ContextAnalyzer:
    """Analyzes planning context."""

    def analyze(self, objective: str, context: dict[str, object] | None) -> dict[str, object]:
        """Analyze context and extract insights."""
        analysis = {
            "objective_length": len(objective),
            "complexity": self._estimate_complexity(objective),
            "language": self._detect_language(objective),
            "requires_multi_step": len(objective.split()) > 10,
        }

        if context:
            analysis["has_context"] = True
            analysis["context_keys"] = list(context.keys())

        return analysis

    def _estimate_complexity(self, objective: str) -> str:
        """Estimate objective complexity."""
        word_count = len(objective.split())
        if word_count < 5:
            return "simple"
        if word_count < 15:
            return "medium"
        return "complex"

    def _detect_language(self, text: str) -> str:
        """Detect text language."""
        arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
        if arabic_chars > len(text) * 0.3:
            return "arabic"
        return "english"


class TaskGenerator:
    """Generates tasks for plans."""

    def generate_tasks(
        self, objective: str, analysis: dict[str, object], max_tasks: int | None = None
    ) -> list[Task]:
        """Generate tasks based on objective and analysis."""
        tasks = []
        complexity = analysis.get("complexity", "medium")

        if complexity == "simple":
            tasks = self._generate_simple_tasks(objective)
        elif complexity == "medium":
            tasks = self._generate_medium_tasks(objective)
        else:
            tasks = self._generate_complex_tasks(objective)

        if max_tasks and len(tasks) > max_tasks:
            tasks = tasks[:max_tasks]

        return tasks

    def _generate_simple_tasks(self, objective: str) -> list[Task]:
        """Generate tasks for simple objectives."""
        return [
            Task(
                task_id="task_1",
                description=f"Execute: {objective}",
                tool_name="execute",
                tool_args={"objective": objective},
                dependencies=[],
            )
        ]

    def _generate_medium_tasks(self, objective: str) -> list[Task]:
        """Generate tasks for medium objectives."""
        return [
            Task(
                task_id="task_1",
                description="Analyze objective",
                tool_name="analyze",
                tool_args={"objective": objective},
                dependencies=[],
            ),
            Task(
                task_id="task_2",
                description="Execute plan",
                tool_name="execute",
                tool_args={"objective": objective},
                dependencies=["task_1"],
            ),
            Task(
                task_id="task_3",
                description="Verify results",
                tool_name="verify",
                tool_args={},
                dependencies=["task_2"],
            ),
        ]

    def _generate_complex_tasks(self, objective: str) -> list[Task]:
        """
        إنشاء مهام للأهداف المعقدة
        Generate tasks for complex objectives.

        Creates a 5-stage pipeline: analysis → decomposition → execution → integration → validation
        """
        tasks = []
        tasks.append(self._create_analysis_task(objective))
        tasks.append(self._create_decomposition_task())
        tasks.append(self._create_execution_task())
        tasks.append(self._create_integration_task())
        tasks.append(self._create_validation_task())
        return tasks

    def _create_analysis_task(self, objective: str) -> Task:
        """
        إنشاء مهمة التحليل العميق
        Create deep analysis task.
        """
        return Task(
            task_id="task_1",
            description="Deep analysis",
            tool_name="deep_analyze",
            tool_args={"objective": objective},
            dependencies=[],
        )

    def _create_decomposition_task(self) -> Task:
        """
        إنشاء مهمة تفكيك الهدف
        Create objective breakdown task.
        """
        return Task(
            task_id="task_2",
            description="Break down objective",
            tool_name="decompose",
            tool_args={},
            dependencies=["task_1"],
        )

    def _create_execution_task(self) -> Task:
        """
        إنشاء مهمة التنفيذ المتوازي
        Create parallel execution task.
        """
        return Task(
            task_id="task_3",
            description="Execute sub-tasks",
            tool_name="execute_parallel",
            tool_args={},
            dependencies=["task_2"],
        )

    def _create_integration_task(self) -> Task:
        """
        إنشاء مهمة دمج النتائج
        Create results integration task.
        """
        return Task(
            task_id="task_4",
            description="Integrate results",
            tool_name="integrate",
            tool_args={},
            dependencies=["task_3"],
        )

    def _create_validation_task(self) -> Task:
        """
        إنشاء مهمة التحقق والتحقيق
        Create verification and validation task.
        """
        return Task(
            task_id="task_5",
            description="Verify and validate",
            tool_name="verify",
            tool_args={},
            dependencies=["task_4"],
        )


class RefactoredPlanner(PlannerInterface):
    """Clean, maintainable planner implementation."""

    # TODO: Reduce parameters (6 params) - Use config object
    def __init__(
        self,
        event_bus: EventBus | None = None,
        validator: PlanValidator | None = None,
        optimizer: PlanOptimizer | None = None,
        context_analyzer: ContextAnalyzer | None = None,
        task_generator: TaskGenerator | None = None,
    ):
        self.event_bus = event_bus or get_event_bus()
        self.validator = validator or PlanValidator()
        self.optimizer = optimizer or PlanOptimizer()
        self.context_analyzer = context_analyzer or ContextAnalyzer()
        self.task_generator = task_generator or TaskGenerator()

    def generate_plan(
        self,
        objective: str,
        context: dict[str, object] | None = None,
        max_tasks: int | None = None,
    ) -> dict[str, object]:
        """Generate plan using clean architecture."""
        from uuid import uuid4

        analysis = self.context_analyzer.analyze(objective, context)

        tasks = self.task_generator.generate_tasks(objective, analysis, max_tasks)

        plan = Plan(
            plan_id=str(uuid4()),
            objective=objective,
            tasks=tasks,
            metadata={"analysis": analysis, "context": context or {}},
        )

        plan = self.optimizer.optimize(plan)

        is_valid, errors = self.validator.validate(plan)
        if not is_valid:
            raise ValueError(f"Invalid plan: {errors}")

        self._publish_event("plan_generated", plan)

        return self._to_dict(plan)

    def validate_plan(self, plan: dict[str, object]) -> bool:
        """Validate plan dictionary."""
        try:
            plan_obj = self._from_dict(plan)
            is_valid, _ = self.validator.validate(plan_obj)
            return is_valid
        except Exception:
            return False

    def get_capabilities(self) -> set[str]:
        """Get planner capabilities."""
        return {
            "semantic",
            "multi-step",
            "optimization",
            "validation",
            "event-driven",
            "clean-architecture",
        }

    def _publish_event(self, event_type: str, plan: Plan):
        """Publish planning event."""
        from app.infrastructure.patterns import Event

        event = Event(
            event_type=event_type,
            data={
                "plan_id": plan.plan_id,
                "objective": plan.objective,
                "task_count": len(plan.tasks),
            },
        )
        self.event_bus.publish(event)

    def _to_dict(self, plan: Plan) -> dict[str, object]:
        """Convert plan to dictionary."""
        return {
            "plan_id": plan.plan_id,
            "objective": plan.objective,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "description": task.description,
                    "tool_name": task.tool_name,
                    "tool_args": task.tool_args,
                    "dependencies": task.dependencies,
                }
                for task in plan.tasks
            ],
            "metadata": plan.metadata,
        }

    def _from_dict(self, data: dict[str, object]) -> Plan:
        """Convert dictionary to plan."""
        tasks = [
            Task(
                task_id=t["task_id"],
                description=t["description"],
                tool_name=t["tool_name"],
                tool_args=t["tool_args"],
                dependencies=t["dependencies"],
            )
            for t in data["tasks"]
        ]

        return Plan(
            plan_id=data["plan_id"],
            objective=data["objective"],
            tasks=tasks,
            metadata=data.get("metadata", {}),
        )
