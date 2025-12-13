"""
API schemas with validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator


class ChatRequest(BaseModel):
    """Chat request schema."""

    question: str = Field(..., min_length=1, max_length=10000)
    conversation_id: int | None = None
    user_id: int | None = Field(
        default=None, gt=0, description="Optional: Overridden by authenticated user ID if present"
    )
    stream: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("question")
    def validate_question(cls, v):
        """Validate question is not empty."""
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response schema."""

    answer: str
    conversation_id: int
    intent: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    code: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    uptime: float
    services: dict[str, str] = Field(default_factory=dict)


class ToolExecutionRequest(BaseModel):
    """Tool execution request."""

    tool_name: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    user_id: int = Field(..., gt=0)


class ToolExecutionResponse(BaseModel):
    """Tool execution response."""

    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float
    metadata: dict[str, Any] = Field(default_factory=dict)
