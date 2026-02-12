from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

# --- Reasoning Agent Models ---


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


# --- Planning Agent Models ---


class Plan(BaseModel):
    """
    A generated plan structure.
    """

    id: UUID = Field(default_factory=uuid4)
    goal: str
    steps: list[str] = Field(default_factory=list)


# --- Research Agent Models ---


class SearchFilters(BaseModel):
    """
    Metadata filters for content search.
    """

    level: str | None = None
    subject: str | None = None
    branch: str | None = None
    set_name: str | None = None
    year: int | None = None
    type: str | None = None
    lang: str | None = None


class SearchRequest(BaseModel):
    """
    Unified search request object.
    """

    q: str | None = None
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: int = 10
    debug_mode: bool = False


class SearchResult(BaseModel):
    """
    Standardized search result.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    title: str
    type: str | None = None
    level: str | None = None
    subject: str | None = None
    branch: str | None = None
    set_name: str | None = Field(None, alias="set")
    year: int | None = None
    lang: str | None = None
    content: str | None = None

    # Extra metadata
    score: float | None = None
    strategy: str | None = None
