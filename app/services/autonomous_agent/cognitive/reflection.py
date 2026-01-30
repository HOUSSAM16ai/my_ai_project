import dspy

from app.core.logging import get_logger

logger = get_logger(__name__)


class ReflectorSignature(dspy.Signature):
    """
    Performs a rigorous academic critique of the autonomous agent's output.
    Checks for completeness, accuracy, and adherence to the original goal.
    """

    goal: str = dspy.InputField(desc="The original objective.")
    execution_history: str = dspy.InputField(desc="Summary of steps taken.")
    final_outcome: str = dspy.InputField(desc="The produced result or answer.")

    analysis: str = dspy.OutputField(desc="Deep analysis of the result's quality.")
    score: float = dspy.OutputField(desc="A float score between 0.0 and 10.0.")
    verdict: str = dspy.OutputField(desc="Final decision: 'APPROVED' or 'REJECTED'.")


class ReflectorModule(dspy.Module):
    """
    DSPy Module for self-reflection and quality control.
    """

    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(ReflectorSignature)

    def forward(self, goal: str, execution_history: str, final_outcome: str):
        return self.prog(
            goal=goal, execution_history=execution_history, final_outcome=final_outcome
        )


def reflect_on_work(goal: str, history: list, outcome: str) -> tuple[float, str, str]:
    """
    Executes the reflection process.
    Returns: (score, critique, verdict)
    """
    history_str = "\n".join([f"Step {s.id}: {s.description} ({s.status})" for s in history])

    try:
        reflector = ReflectorModule()
        pred = reflector(goal=goal, execution_history=history_str, final_outcome=outcome)

        # Normalize verdict
        verdict = pred.verdict.upper().strip()
        verdict = "APPROVED" if "APPROVED" in verdict else "REJECTED"

        # Parse score
        try:
            score = float(pred.score)
        except (ValueError, TypeError):
            score = 0.0

        return score, pred.analysis, verdict

    except Exception as e:
        logger.error(f"Reflection failed: {e}")
        return 0.0, f"Reflection system error: {e}", "REJECTED"
