# app/models.py
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Setup password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

class MissionStatus(str, enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    PLANNED = "planned"
    RUNNING = "running"
    ADAPTING = "adapting"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"

class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    VALID = "valid"
    INVALID = "invalid"
    SELECTED = "selected"
    ABANDONED = "abandoned"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"

class MissionEventType(str, enum.Enum):
    CREATED = "mission_created"
    ARCHITECTURE_CLASSIFIED = "architecture_classified"
    PLAN_SELECTED = "plan_selected"
    EXECUTION_STARTED = "execution_started"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    REPLAN_TRIGGERED = "replan_triggered"
    REPLAN_APPLIED = "replan_applied"
    RISK_SUMMARY = "risk_summary"
    MISSION_COMPLETED = "mission_completed"
    MISSION_FAILED = "mission_failed"
    FINALIZED = "mission_finalized"

# ==============================================================================
# MODELS
# ==============================================================================

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

    # Relationships
    admin_conversations: List["AdminConversation"] = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="user")
    )
    missions: List["Mission"] = Relationship(
        sa_relationship=relationship("Mission", back_populates="initiator")
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
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

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
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    conversation: "AdminConversation" = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="messages")
    )

class Mission(SQLModel, table=True):
    __tablename__ = "missions"
    id: Optional[int] = Field(default=None, primary_key=True)
    objective: str = Field(sa_column=Column(Text))
    status: MissionStatus = Field(default=MissionStatus.PENDING, sa_column=Column(SAEnum(MissionStatus)))
    initiator_id: int = Field(foreign_key="users.id", index=True)
    active_plan_id: Optional[int] = Field(default=None, foreign_key="mission_plans.id")

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships
    initiator: "User" = Relationship(
        sa_relationship=relationship("User", back_populates="missions")
    )
    tasks: List["Task"] = Relationship(
        sa_relationship=relationship("Task", back_populates="mission", foreign_keys="[Task.mission_id]")
    )
    mission_plans: List["MissionPlan"] = Relationship(
        sa_relationship=relationship("MissionPlan", back_populates="mission", foreign_keys="[MissionPlan.mission_id]")
    )
    events: List["MissionEvent"] = Relationship(
        sa_relationship=relationship("MissionEvent", back_populates="mission")
    )

class MissionPlan(SQLModel, table=True):
    __tablename__ = "mission_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="missions.id", index=True)
    version: int = Field(default=1)
    planner_name: str = Field(max_length=100)
    status: PlanStatus = Field(default=PlanStatus.DRAFT, sa_column=Column(SAEnum(PlanStatus)))
    score: float = Field(default=0.0)
    rationale: Optional[str] = Field(sa_column=Column(Text))
    # Avoid JSONB for SQLite compat
    raw_json: Optional[str] = Field(sa_column=Column(Text))
    stats_json: Optional[str] = Field(sa_column=Column(Text))
    warnings_json: Optional[str] = Field(sa_column=Column(Text))
    content_hash: Optional[str] = Field(max_length=64)

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    mission: "Mission" = Relationship(
        sa_relationship=relationship("Mission", back_populates="mission_plans", foreign_keys="[MissionPlan.mission_id]")
    )
    tasks: List["Task"] = Relationship(
        sa_relationship=relationship("Task", back_populates="plan")
    )

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: Optional[int] = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="missions.id", index=True)
    plan_id: Optional[int] = Field(default=None, foreign_key="mission_plans.id", index=True)
    task_key: str = Field(max_length=50)
    description: Optional[str] = Field(sa_column=Column(Text))
    tool_name: Optional[str] = Field(max_length=100)
    # Avoid JSONB for SQLite compat, use JSON if available or Text
    tool_args_json: Optional[Any] = Field(default=None, sa_column=Column(Text)) # Postgres specific or use string
    status: TaskStatus = Field(default=TaskStatus.PENDING, sa_column=Column(SAEnum(TaskStatus)))
    attempt_count: int = Field(default=0)
    max_attempts: int = Field(default=3)
    priority: int = Field(default=0)
    risk_level: Optional[str] = Field(max_length=50)
    criticality: Optional[str] = Field(max_length=50)
    depends_on_json: Optional[Any] = Field(default=None, sa_column=Column(Text))
    result_text: Optional[str] = Field(sa_column=Column(Text))
    result_meta_json: Optional[Any] = Field(default=None, sa_column=Column(Text))
    error_text: Optional[str] = Field(sa_column=Column(Text))

    started_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    finished_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    next_retry_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    duration_ms: Optional[int] = Field(default=0)

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships
    mission: "Mission" = Relationship(
        sa_relationship=relationship("Mission", back_populates="tasks", foreign_keys="[Task.mission_id]")
    )
    plan: "MissionPlan" = Relationship(
        sa_relationship=relationship("MissionPlan", back_populates="tasks", foreign_keys="[Task.plan_id]")
    )

class MissionEvent(SQLModel, table=True):
    __tablename__ = "mission_events"
    id: Optional[int] = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="missions.id", index=True)
    event_type: MissionEventType = Field(sa_column=Column(SAEnum(MissionEventType)))
    payload_json: Optional[Any] = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    mission: "Mission" = Relationship(
        sa_relationship=relationship("Mission", back_populates="events")
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

# Helpers
def log_mission_event(mission: Mission, event_type: MissionEventType, payload: dict, session=None):
    import json
    evt = MissionEvent(
        mission_id=mission.id,
        event_type=event_type,
        payload_json=json.dumps(payload)
    )
    if session:
        session.add(evt)

def update_mission_status(mission: Mission, status: MissionStatus, note: str | None = None, session=None):
    mission.status = status
    mission.updated_at = utc_now()

# Rebuild models for forward refs
import sys
import traceback
try:
    SQLModel.model_rebuild()
except Exception:
    traceback.print_exc()
