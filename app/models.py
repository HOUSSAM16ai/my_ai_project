# app/models.py
from __future__ import annotations
import enum
from datetime import datetime, UTC
from typing import List, Optional, Any
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from sqlalchemy import String, Text, DateTime, func, Index

def utc_now() -> datetime:
    return datetime.now(UTC)

Json = JSON()

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
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    admin_conversations: List["AdminConversation"] = Relationship(back_populates="user")
    missions: List["Mission"] = Relationship(back_populates="user")

class AdminConversation(SQLModel, table=True):
    __tablename__ = "admin_conversations"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)
    user: "User" = Relationship(back_populates="admin_conversations")
    messages: List["AdminMessage"] = Relationship(back_populates="conversation")

class AdminMessage(SQLModel, table=True):
    __tablename__ = "admin_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="admin_conversations.id", index=True)
    role: MessageRole
    content: str = Field(sa_column=Column(Text))
    conversation: "AdminConversation" = Relationship(back_populates="messages")

class Mission(SQLModel, table=True):
    __tablename__ = "missions"
    id: Optional[int] = Field(default=None, primary_key=True)
    objective: str
    user_id: int = Field(foreign_key="users.id", index=True)
    user: "User" = Relationship(back_populates="missions")
    tasks: List["Task"] = Relationship(back_populates="mission")
    mission_plans: List["MissionPlan"] = Relationship(back_populates="mission")
    mission_events: List["MissionEvent"] = Relationship(back_populates="mission")

class MissionEvent(SQLModel, table=True):
    __tablename__ = "mission_events"
    id: Optional[int] = Field(default=None, primary_key=True)
    event: str
    mission_id: int = Field(foreign_key="missions.id", index=True)
    mission: "Mission" = Relationship(back_populates="mission_events")

class MissionPlan(SQLModel, table=True):
    __tablename__ = "mission_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    plan: str
    mission_id: int = Field(foreign_key="missions.id", index=True)
    mission: "Mission" = Relationship(back_populates="mission_plans")

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    mission_id: int = Field(foreign_key="missions.id", index=True)
    mission: "Mission" = Relationship(back_populates="tasks")

class PromptTemplate(SQLModel, table=True):
    __tablename__ = "prompt_templates"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    template: str

class GeneratedPrompt(SQLModel, table=True):
    __tablename__ = "generated_prompts"
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    template_id: int = Field(foreign_key="prompt_templates.id", index=True)

# Manually update forward references to resolve relationship errors
User.update_forward_refs()
AdminConversation.update_forward_refs()
AdminMessage.update_forward_refs()
Mission.update_forward_refs()
MissionEvent.update_forward_refs()
MissionPlan.update_forward_refs()
Task.update_forward_refs()
