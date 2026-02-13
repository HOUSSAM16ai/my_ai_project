from typing import Any

from pydantic import BaseModel, Field

# ==============================================================================
# Canonical Intermediate Representations (IR)
# ==============================================================================

class WorkflowPlan(BaseModel):
    """
    Represents a request to execute a complex workflow or plan.
    Target: LangGraph / Planning Gateway
    """
    goal: str = Field(..., description="The primary objective of the workflow")
    context: dict[str, Any] = Field(default_factory=dict, description="Contextual data for execution")
    workflow_id: str | None = Field(None, description="Optional ID for resume/track")


class RetrievalQuery(BaseModel):
    """
    Represents a request for semantic information retrieval.
    Target: LlamaIndex / Research Gateway
    """
    query: str = Field(..., description="The search query text")
    top_k: int = Field(default=5, ge=1, description="Number of results to retrieve")
    filters: dict[str, Any] | None = Field(None, description="Metadata filters (year, subject, etc.)")


class PromptProgram(BaseModel):
    """
    Represents a request for prompt optimization or query refinement.
    Target: DSPy / Research Gateway
    """
    program_name: str = Field(..., description="Name of the DSPy program/module")
    input_text: str = Field(..., description="Primary input text (e.g., query to refine)")
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration overrides")
    api_key: str | None = Field(None, description="Optional API key override")


class ScoringSpec(BaseModel):
    """
    Represents a request to re-rank or score documents.
    Target: Reranker / Research Gateway
    """
    query: str = Field(..., description="The reference query")
    documents: list[str] = Field(..., description="List of document texts to score")
    top_n: int = Field(default=5, ge=1, description="Number of top results to return")


class AgentAction(BaseModel):
    """
    Represents a request for an agent to perform a specific action.
    Target: Kagent
    """
    action_name: str = Field(..., description="Name of the action to execute")
    capability: str = Field(..., description="Required capability (e.g., 'filesystem', 'browser')")
    payload: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
