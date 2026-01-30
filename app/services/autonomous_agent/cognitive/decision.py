import dspy
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ActionRefinerSignature(dspy.Signature):
    """
    Translates a high-level plan step into a concrete tool execution command.
    Selects the best tool from the available list and constructs the arguments.
    """

    goal: str = dspy.InputField(desc="The overall goal.")
    step_description: str = dspy.InputField(desc="The current step to execute.")
    available_tools: str = dspy.InputField(desc="List of available tools and their schemas.")

    thought: str = dspy.OutputField(desc="Reasoning for tool selection.")
    tool_name: str = dspy.OutputField(desc="The exact name of the tool to call.")
    tool_args: str = dspy.OutputField(desc="The arguments for the tool in JSON format.")


class ActionRefinerModule(dspy.Module):
    """
    DSPy Module for operational decision making.
    """
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(ActionRefinerSignature)

    def forward(self, goal: str, step_description: str, available_tools: str):
        return self.prog(
            goal=goal,
            step_description=step_description,
            available_tools=available_tools
        )


def decide_action(goal: str, step: str, tools_desc: str) -> tuple[str, str]:
    """
    Decides which tool to use.
    Returns: (tool_name, tool_args_json_string)
    """
    try:
        refiner = ActionRefinerModule()
        pred = refiner(
            goal=goal,
            step_description=step,
            available_tools=tools_desc
        )
        return pred.tool_name, pred.tool_args
    except Exception as e:
        logger.error(f"Action refinement failed: {e}")
        return "error", "{}"
