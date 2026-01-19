from __future__ import annotations

from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.services.audit.enums import AuditAction


class AuditLogEntry(BaseModel):
    """
    A unified, high-precision schema for an audit log entry before persistence.
    """
    actor_user_id: int | None = Field(None, description="The user performing the action")
    action: AuditAction | str = Field(..., description="The action performed")
    target_type: str = Field(..., description="The type of the target entity")
    target_id: str | None = Field(None, description="The ID of the target entity")
    metadata: Mapping[str, object] = Field(default_factory=dict, description="Additional context")
    ip: str | None = Field(None, description="IP address of the actor")
    user_agent: str | None = Field(None, description="User Agent of the actor")

    model_config = ConfigDict(from_attributes=True)
