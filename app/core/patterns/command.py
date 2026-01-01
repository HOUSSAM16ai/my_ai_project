"""
Command Pattern Implementation

Encapsulates requests as objects for queuing, logging, and undo operations.
"""

from typing import Any

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeVar
from uuid import uuid4

T = TypeVar("T")

@dataclass
class CommandResult[T]:
    """Result of command execution."""

    success: bool
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

class Command[T](ABC):
    """Base command interface."""

    def __init__(self):
        self.id = str(uuid4())
        self.created_at = datetime.now()
        self.executed_at: datetime | None = None

    @abstractmethod
    async def execute(self) -> CommandResult[T]:
        """Execute the command."""
        pass

    async def validate(self) -> CommandResult[None]:
        """Validate command before execution."""
        return CommandResult(success=True)

    async def on_success(self, result: CommandResult[T]) -> None:
        """Hook called after successful execution."""
        pass

    async def on_failure(self, result: CommandResult[T]) -> None:
        """Hook called after failed execution."""
        pass

class CommandBus:
    """Command bus for executing commands with middleware support."""

    def __init__(self):
        self._middleware: list[CommandMiddleware] = []

    def add_middleware(self, middleware: "CommandMiddleware") -> None:
        """Add middleware to the bus."""
        self._middleware.append(middleware)

    async def execute(self, command: Command[T]) -> CommandResult[T]:
        """Execute command through middleware chain."""
        # Validate
        validation = await command.validate()
        if not validation.success:
            return CommandResult(success=False, error=validation.error)

        # Execute through middleware
        handler = self._build_handler(command)
        result = await handler()

        # Post-execution hooks
        if result.success:
            await command.on_success(result)
        else:
            await command.on_failure(result)

        command.executed_at = datetime.now()
        return result

    def _build_handler(self, command: Command[T]):
        """Build middleware chain."""

        async def final_handler() -> None:
            return await command.execute()

        handler = final_handler
        for middleware in reversed(self._middleware):
            handler = middleware.wrap(command, handler)

        return handler

class CommandMiddleware(ABC):
    """Base middleware for command processing."""

    @abstractmethod
    def wrap(self, command: Command, next_handler) -> None:  # noqa: unused variable
        """Wrap the next handler with middleware logic."""
        pass
