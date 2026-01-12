from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class AgentResponse(BaseModel):
    success: bool
    data: Any | None = None
    message: str | None = None


@runtime_checkable
class AgentProtocol(Protocol):
    async def process(self, input_data: Any) -> AgentResponse: ...
