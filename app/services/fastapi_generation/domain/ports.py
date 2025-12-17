"""
Domain Ports - FastAPI Generation Service
=========================================
Repository interfaces (abstractions).
Define contracts without implementation.
"""
from __future__ import annotations

from typing import Any, Protocol

from .models import (
    CompletionRequest,
    StructuredJsonRequest,
)


class LLMClientPort(Protocol):
    """Port for LLM client interactions."""

    def text_completion(self, request: CompletionRequest) -> str:
        """
        Generate text completion.

        Args:
            request: Completion request parameters

        Returns:
            Generated text

        Raises:
            RuntimeError: If completion fails
        """
        ...

    def structured_json(self, request: StructuredJsonRequest) -> dict[str, Any] | None:
        """
        Generate structured JSON response.

        Args:
            request: Structured JSON request parameters

        Returns:
            Parsed JSON object or None if failed
        """
        ...


class ModelSelectorPort(Protocol):
    """Port for model selection logic."""

    def select_model(
        self, explicit: str | None = None, task: Any = None
    ) -> str:
        """
        Select appropriate model based on context.

        Args:
            explicit: Explicitly requested model
            task: Task object for context

        Returns:
            Selected model name
        """
        ...


class ErrorMessageBuilderPort(Protocol):
    """Port for building error messages."""

    def build_error_message(
        self, error: str, prompt_length: int, max_tokens: int
    ) -> str:
        """
        Build bilingual error message.

        Args:
            error: Error description
            prompt_length: Length of prompt
            max_tokens: Max tokens used

        Returns:
            Formatted error message
        """
        ...


class ContextFinderPort(Protocol):
    """Port for finding related context."""

    def find_related_context(self, description: str) -> Any:
        """
        Find related context for a description.

        Args:
            description: Description to find context for

        Returns:
            Context object
        """
        ...


class TaskExecutorPort(Protocol):
    """Port for task execution."""

    def execute(self, task: Any, model: str | None = None) -> None:
        """
        Execute a task.

        Args:
            task: Task to execute
            model: Optional model override
        """
        ...


__all__ = [
    "LLMClientPort",
    "ModelSelectorPort",
    "ErrorMessageBuilderPort",
    "ContextFinderPort",
    "TaskExecutorPort",
]
