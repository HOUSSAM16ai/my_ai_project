# app/models.py
from __future__ import annotations

import enum
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from typing import List

# Setup password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=150)
    email: str = Field(max_length=150, unique=True, index=True)
    password_hash: Optional[str] = Field(default=None, max_length=256)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships - using sa_relationship to be explicit and avoid ambiguity
    admin_conversations: List["AdminConversation"] = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="user")
    )
    missions: List["Mission"] = Relationship(
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
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    user: "User" = Relationship(
        sa_relationship=relationship("User", back_populates="admin_conversations")
    )
    messages: List["AdminMessage"] = Relationship(
        sa_relationship=relationship("AdminMessage", back_populates="conversation")
    )

class AdminMessage(SQLModel, table=True):
    __tablename__ = "admin_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="admin_conversations.id", index=True)
    role: MessageRole = Field(sa_column=Column(SAEnum(MessageRole)))
    content: str = Field(sa_column=Column(Text))

    # Relationships
    conversation: "AdminConversation" = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="messages")
    )

class Mission(SQLModel, table=True):
    __tablename__ = "missions"
    id: Optional[int] = Field(default=None, primary_key=True)
    objective: str
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    user: "User" = Relationship(
        sa_relationship=relationship("User", back_populates="missions")
    )
    tasks: List["Task"] = Relationship(
        sa_relationship=relationship("Task", back_populates="mission")
    )
    mission_plans: List["MissionPlan"] = Relationship(
        sa_relationship=relationship("MissionPlan", back_populates="mission")
    )
    mission_events: List["MissionEvent"] = Relationship(
        sa_relationship=relationship("MissionEvent", back_populates="mission")
    )

class MissionEvent(SQLModel, table=True):
    __tablename__ = "mission_events"
    id: Optional[int] = Field(default=None, primary_key=True)
    event: str
    mission_id: int = Field(foreign_key="missions.id", index=True)

    # Relationships
    mission: "Mission" = Relationship(
        sa_relationship=relationship("Mission", back_populates="mission_events")
    )

class MissionPlan(SQLModel, table=True):
    __tablename__ = "mission_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    plan: str
    mission_id: int = Field(foreign_key="missions.id", index=True)

    # Relationships
    mission: "Mission" = Relationship(
        sa_relationship=relationship("Mission", back_populates="mission_plans")
    )

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    mission_id: int = Field(foreign_key="missions.id", index=True)

    # Relationships
    mission: "Mission" = Relationship(
        sa_relationship=relationship("Mission", back_populates="tasks")
    )

class PromptTemplate(SQLModel, table=True):
    __tablename__ = "prompt_templates"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    template: str

    generated_prompts: List["GeneratedPrompt"] = Relationship(
        sa_relationship=relationship("GeneratedPrompt", back_populates="template")
    )

class GeneratedPrompt(SQLModel, table=True):
    __tablename__ = "generated_prompts"
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    template_id: int = Field(foreign_key="prompt_templates.id", index=True)

    # Relationships
    template: "PromptTemplate" = Relationship(
        sa_relationship=relationship("PromptTemplate", back_populates="generated_prompts")
    )


# ------------------------------------------------------------------------------
# Model Rebuild & Validation
# ------------------------------------------------------------------------------
import sys
import traceback

try:
    # In Pydantic v2 / SQLModel latest, model_rebuild() is the standard way
    # to resolve forward references.
    SQLModel.model_rebuild()
except Exception as e:
    print("SQLModel.model_rebuild() failed:", file=sys.stderr)
    traceback.print_exc()
