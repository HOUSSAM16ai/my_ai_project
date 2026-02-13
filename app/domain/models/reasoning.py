"""
Reasoning Domain Models.
------------------------
Defines the data structures for reasoning and thought processes.
These models act as an Anti-Corruption Layer (ACL) for the Reasoning Agent.
"""

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """
    Result of a self-reflection/evaluation step.
    """

    score: float = Field(..., description="Quality score between 0.0 and 1.0")
    reasoning: str = Field(..., description="Justification for the score")
    is_valid: bool = Field(..., description="Is this path factually and logically sound?")


class ReasoningNode(BaseModel):
    """
    Represents a single step or thought in the reasoning tree.
    """

    id: str = Field(..., description="Unique ID of the node")
    parent_id: str | None = Field(None, description="ID of the parent node")
    content: str = Field(..., description="The thought, hypothesis, or partial solution")
    step_type: str = Field(
        ..., description="Type: 'decomposition', 'hypothesis', 'solution', 'critique'"
    )

    # R-MCTS Attributes
    visits: int = Field(0, description="Number of times this node has been visited")
    value: float = Field(0.0, description="Accumulated value/score")
    evaluation: EvaluationResult | None = Field(None, description="Self-reflection result")

    children: list["ReasoningNode"] = Field(default_factory=list)


class SearchTree(BaseModel):
    """
    The full reasoning tree structure.
    """

    root: ReasoningNode
    total_steps: int = 0
