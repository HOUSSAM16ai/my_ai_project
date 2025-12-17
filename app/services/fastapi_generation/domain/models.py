"""
Domain Models - FastAPI Generation Service
==========================================
Pure business entities and value objects.
No external dependencies.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StepState:
    """Represents the state of a single orchestration step."""

    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float | None = None

    def finish(self) -> None:
        """Mark step as finished and calculate duration."""
        if self.duration_ms is None:
            self.duration_ms = round(time.perf_counter() * 1000 - self.started_ms, 2)


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""

    model_name: str
    max_steps: int


@dataclass
class OrchestratorTelemetry:
    """Telemetry data for orchestration execution."""

    steps_taken: int = 0
    tools_invoked: int = 0
    distinct_tools: int = 0
    finalization_reason: str | None = None
    error: str | None = None
    stagnation: bool = False
    tool_call_limit_hit: bool = False
    repeat_pattern_triggered: bool = False
    hotspot_hint_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert telemetry to dictionary."""
        return asdict(self)


@dataclass
class GenerationRequest:
    """Request for code generation."""

    prompt: str
    conversation_id: str | None = None
    model: str | None = None
    temperature: float = 0.3
    max_tokens: int = 4000
    max_retries: int = 1


@dataclass
class GenerationResponse:
    """Response from code generation."""

    status: str  # "success" or "error"
    answer: str
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionRequest:
    """Request for text completion."""

    system_prompt: str
    user_prompt: str
    temperature: float = 0.3
    max_tokens: int = 800
    max_retries: int = 1
    fail_hard: bool = False
    model: str | None = None


@dataclass
class StructuredJsonRequest:
    """Request for structured JSON generation."""

    system_prompt: str
    user_prompt: str
    format_schema: dict[str, Any]
    temperature: float = 0.2
    max_retries: int = 1
    fail_hard: bool = False
    model: str | None = None


__all__ = [
    "StepState",
    "OrchestratorConfig",
    "OrchestratorTelemetry",
    "GenerationRequest",
    "GenerationResponse",
    "CompletionRequest",
    "StructuredJsonRequest",
]
