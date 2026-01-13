from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class AgentResponse(BaseModel):
    success: bool
    data: object | None = None
    message: str | None = None


@runtime_checkable
class AgentProtocol(Protocol):
    async def process(self, input_data: object) -> AgentResponse: ...
