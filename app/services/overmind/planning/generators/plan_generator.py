# app/overmind/planning/generators/plan_generator.py
"""Plan generator orchestrator with CC ≤ 5."""

from dataclasses import dataclass
from typing import Any

from .context_enricher import ContextEnricher
from .dependency_builder import DependencyBuilder
from .objective_analyzer import ObjectiveAnalyzer
from .plan_optimizer import PlanOptimizer
from .task_decomposer import TaskDecomposer


@dataclass
class GeneratedPlan:
    """Generated plan result."""

    objective: str
    tasks: list[Any]
    graph: Any
    metadata: dict[str, Any]


class PlanGenerator:
    """
    Orchestrates plan generation. CC=5

    Replaces the monolithic generate_plan function (CC=40).
    """

    def __init__(self):
        self.objective_analyzer = ObjectiveAnalyzer()
        self.context_enricher = ContextEnricher()
        self.task_decomposer = TaskDecomposer()
        self.dependency_builder = DependencyBuilder()
        self.plan_optimizer = PlanOptimizer()

    def generate(self, objective: str, context: dict) -> GeneratedPlan:
        """
        Generate plan from objective and context. CC=5

        This replaces the original generate_plan function which had CC=40.
        """
        # Step 1: Analyze objective
        analyzed = self.objective_analyzer.analyze(objective)

        # Step 2: Enrich context
        enriched = self.context_enricher.enrich(context)

        # Step 3: Decompose into tasks
        tasks = self.task_decomposer.decompose(analyzed, enriched)

        # Step 4: Build dependency graph
        graph = self.dependency_builder.build(tasks)

        # Step 5: Optimize plan
        optimized_tasks = self.plan_optimizer.optimize(tasks, graph)

        # Step 6: Create result
        return GeneratedPlan(
            objective=objective,
            tasks=optimized_tasks,
            graph=graph,
            metadata={
                "complexity": analyzed.complexity.value,
                "estimated_tasks": analyzed.estimated_tasks,
                "keywords": analyzed.keywords,
            },
        )
