import dspy

from app.core.logging import get_logger
from app.services.autonomous_agent.domain.models import PlanStep

logger = get_logger(__name__)


class PlannerSignature(dspy.Signature):
    """
    Analyzes the goal and context to create a step-by-step execution plan.
    The plan should be logical, sequential, and exhaustive.
    """

    goal: str = dspy.InputField(desc="The primary objective.")
    context: str = dspy.InputField(desc="Relevant background information or constraints.")

    rationale: str = dspy.OutputField(desc="The reasoning behind the chosen strategy.")
    steps: list[str] = dspy.OutputField(desc="A list of clear, actionable steps to execute the plan.")


class PlannerModule(dspy.Module):
    """
    DSPy Module for strategic planning.
    """
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(PlannerSignature)

    def forward(self, goal: str, context: str):
        return self.prog(goal=goal, context=context)


def generate_plan(goal: str, context: dict) -> list[PlanStep]:
    """
    Generates a structured plan using the DSPy cognitive engine.
    """
    context_str = str(context)

    # In a real microservice, we might instantiate dspy.LM here or rely on global config.
    # Assuming dspy.settings.lm is configured globally or we wrap this in a context in the node.

    try:
        planner = PlannerModule()
        # Ensure we are in a dspy context if needed, but usually the node handles the LM context
        # or it's set globally. For safety, we rely on the caller to set the LM,
        # or we could attempt to set a default one if missing (like in query_refiner).

        # Note: query_refiner creates a new LM per request. We might want to adopt that pattern
        # if the global one isn't guaranteed. However, for "Unit of Work", we'll assume
        # the node configures the environment.

        pred = planner(goal=goal, context=context_str)

        plan_steps = []
        for i, step_desc in enumerate(pred.steps):
            # rudimentary parsing: check if tool is implied (e.g., "[Search] ...")
            # For now, we keep it simple.
            plan_steps.append(
                PlanStep(
                    id=i + 1,
                    description=step_desc,
                    status="pending"
                )
            )

        logger.info(f"Generated plan with {len(plan_steps)} steps.")
        return plan_steps

    except Exception as e:
        logger.error(f"Planning failed: {e}")
        # Fallback plan
        return [PlanStep(id=1, description=f"Attempt to solve: {goal}", status="pending")]
