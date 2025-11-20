# app/models.py
from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # This block prevents circular imports during runtime
    pass

# Setup password hashing
# Using argon2 for robust security and to avoid bcrypt version conflicts
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def utc_now() -> datetime:
    return datetime.now(UTC)

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=150)
    email: str = Field(max_length=150, unique=True, index=True)
    password_hash: str | None = Field(default=None, max_length=256)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships
    # We use sa_relationship to explicitly define the relationship for SQLAlchemy,
    # bypassing SQLModel's inference which fails with List['String'] forward refs.
    admin_conversations: list[AdminConversation] = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="user")
    )
    missions: list[Mission] = Relationship(
        sa_relationship=relationship("Mission", back_populates="user")
    )

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"

class AdminConversation(SQLModel, table=True):
    __tablename__ = "admin_conversations"
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    user: User = Relationship(
        sa_relationship=relationship("User", back_populates="admin_conversations")
    )
    messages: list[AdminMessage] = Relationship(
        sa_relationship=relationship("AdminMessage", back_populates="conversation")
    )

class AdminMessage(SQLModel, table=True):
    __tablename__ = "admin_messages"
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="admin_conversations.id", index=True)
    role: MessageRole = Field(
        sa_column=Column(
            SAEnum(MessageRole, name="message_role_enum", native_enum=False)
        )
    )
    content: str = Field(sa_column=Column(Text))

    # Relationships
    conversation: AdminConversation = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="messages")
    )

class Mission(SQLModel, table=True):
    __tablename__ = "missions"
    id: int | None = Field(default=None, primary_key=True)
    objective: str
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    user: User = Relationship(
        sa_relationship=relationship("User", back_populates="missions")
    )
    tasks: list[Task] = Relationship(
        sa_relationship=relationship("Task", back_populates="mission")
    )
    mission_plans: list[MissionPlan] = Relationship(
        sa_relationship=relationship("MissionPlan", back_populates="mission")
    )
    mission_events: list[MissionEvent] = Relationship(
        sa_relationship=relationship("MissionEvent", back_populates="mission")
    )

class MissionEvent(SQLModel, table=True):
    __tablename__ = "mission_events"
    id: int | None = Field(default=None, primary_key=True)
    event: str
    mission_id: int = Field(foreign_key="missions.id", index=True)

    # Relationships
    mission: Mission = Relationship(
        sa_relationship=relationship("Mission", back_populates="mission_events")
    )

class MissionPlan(SQLModel, table=True):
    __tablename__ = "mission_plans"
    id: int | None = Field(default=None, primary_key=True)
    plan: str
    mission_id: int = Field(foreign_key="missions.id", index=True)

    # Relationships
    mission: Mission = Relationship(
        sa_relationship=relationship("Mission", back_populates="mission_plans")
    )

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: int | None = Field(default=None, primary_key=True)
    description: str
    mission_id: int = Field(foreign_key="missions.id", index=True)

    # Relationships
    mission: Mission = Relationship(
        sa_relationship=relationship("Mission", back_populates="tasks")
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


# ------------------------------------------------------------------------------
# Model Rebuild & Validation
# ------------------------------------------------------------------------------
import logging
import os

# Ensure reports directory exists
os.makedirs("reports", exist_ok=True)
logging.basicConfig(filename="reports/model_rebuild.log", level=logging.INFO)

try:
    # In Pydantic v2 / SQLModel latest, model_rebuild() is the standard way
    # to resolve forward references.
    for cls in SQLModel.__subclasses__():
        cls.model_rebuild()
    logging.info("SQLModel.model_rebuild() completed successfully.")
except Exception as e:
    logging.error(f"Error during SQLModel.model_rebuild(): {e}")
    # We re-raise so the failure is visible during import/test
    raise e
