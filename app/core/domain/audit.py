"""
Audit Domain Models.
Contains AuditLog, PromptTemplate, GeneratedPrompt.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, DateTime, func
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from app.core.domain.common import utc_now

if TYPE_CHECKING:
    from app.core.domain.user import User


class AuditLog(SQLModel, table=True):
    """
    Central Audit Log for sensitive operations.
    """

    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    actor_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(max_length=150, index=True)
    target_type: str = Field(max_length=100)
    target_id: str | None = Field(default=None, max_length=150)
    details: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON, nullable=False, default=dict),
    )
    ip: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
    )

    actor: User | None = Relationship(
        sa_relationship=relationship("app.core.domain.user.User", back_populates="audit_logs"),
    )


class PromptTemplate(SQLModel, table=True):
    __tablename__ = "prompt_templates"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    template: str

    generated_prompts: list[GeneratedPrompt] = Relationship(
        sa_relationship=relationship("GeneratedPrompt", back_populates="template")
    )


class GeneratedPrompt(SQLModel, table=True):
    __tablename__ = "generated_prompts"
    id: int | None = Field(default=None, primary_key=True)
    prompt: str
    template_id: int = Field(foreign_key="prompt_templates.id", index=True)

    # Relationships
    template: PromptTemplate = Relationship(
        sa_relationship=relationship("PromptTemplate", back_populates="generated_prompts")
    )
