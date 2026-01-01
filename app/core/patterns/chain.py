"""
Chain of Responsibility Pattern

Decouples sender from receiver by giving multiple objects a chance to handle request.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")

class ChainLink[T, R](ABC):
    """Base chain link."""

    def __init__(self):
        self._next: ChainLink[T, R] | None = None

    def set_next(self, link: "ChainLink[T, R]") -> "ChainLink[T, R]":
        """Set next link in chain."""
        self._next = link
        return link

    async def handle(self, request: T) -> R | None:
        """Handle request or pass to next link."""
        if await self.can_handle(request):
            return await self.process(request)

        if self._next:
            return await self._next.handle(request)

        return None

    @abstractmethod
    async def can_handle(self, request: T) -> bool:
        """Check if this link can handle the request."""
        pass

    @abstractmethod
    async def process(self, request: T) -> R:
        """Process the request."""
        pass

class Chain[T, R]:
    """Chain manager."""

    def __init__(self):
        self._head: ChainLink[T, R] | None = None
        self._tail: ChainLink[T, R] | None = None

    def add(self, link: ChainLink[T, R]) -> "Chain[T, R]":
        """Add link to chain."""
        if not self._head:
            self._head = link
            self._tail = link
        else:
            self._tail.set_next(link)
            self._tail = link
        return self

    async def execute(self, request: T) -> R | None:
        """Execute chain."""
        if self._head:
            return await self._head.handle(request)
        return None
