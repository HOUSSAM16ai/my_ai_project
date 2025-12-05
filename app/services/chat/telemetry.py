from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChatTelemetry:
    """Telemetry data for chat operations."""

    intent_detection_time_ms: float = 0.0
    tool_execution_time_ms: float = 0.0
    total_response_time_ms: float = 0.0
    tokens_used: int = 0
    response_quality_grade: str = "A"  # A, B, C
    tool_name: str | None = None
    success: bool = True
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_detection_time_ms": self.intent_detection_time_ms,
            "tool_execution_time_ms": self.tool_execution_time_ms,
            "total_response_time_ms": self.total_response_time_ms,
            "tokens_used": self.tokens_used,
            "response_quality_grade": self.response_quality_grade,
            "tool_name": self.tool_name,
            "success": self.success,
            "error_type": self.error_type,
        }
