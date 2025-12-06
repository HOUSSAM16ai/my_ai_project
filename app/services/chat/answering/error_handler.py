# app/services/chat/answering/error_handler.py
"""Error handler with CC ≤ 3."""

from dataclasses import dataclass


@dataclass
class Answer:
    """Answer result."""

    status: str
    content: str
    tokens_used: int = 0
    model_used: str = "unknown"
    error_type: str = ""


class ErrorHandler:
    """Handles errors in answering. CC ≤ 3"""

    def handle(self, error: Exception) -> Answer:
        """Handle error and return answer. CC=3"""
        error_type = type(error).__name__

        if "timeout" in str(error).lower():
            return Answer(
                status="error", content="Request timed out. Please try again.", error_type="timeout"
            )
        elif "rate" in str(error).lower():
            return Answer(
                status="error", content="Rate limit exceeded. Please wait.", error_type="rate_limit"
            )
        else:
            return Answer(status="error", content=f"Error: {error!s}", error_type=error_type)
