# app/models.py
from __future__ import annotations

import enum
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, TypeDecorator, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    pass

# Setup password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def utc_now() -> datetime:
    return datetime.now(UTC)


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
    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=150)
    email: str = Field(max_length=150, unique=True, index=True)
    password_hash: str | None = Field(default=None, max_length=256)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )

    # Relationships
    admin_conversations: list[AdminConversation] = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="user")
    )
    missions: list[Mission] = Relationship(
        sa_relationship=relationship("Mission", back_populates="initiator")
    )

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return pwd_context.verify(password, self.password_hash)

    def verify_password(self, password: str) -> bool:
        return self.check_password(password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class AdminConversation(SQLModel, table=True):
    __tablename__ = "admin_conversations"
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)
    conversation_type: str = Field(default="general", max_length=50)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

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
    role: MessageRole = Field(sa_column=Column(SAEnum(MessageRole)))
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    # Relationships
    conversation: AdminConversation = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="messages")
    )


class Mission(SQLModel, table=True):
    __tablename__ = "missions"
    id: int | None = Field(default=None, primary_key=True)
    objective: str = Field(sa_column=Column(Text))
    status: MissionStatus = Field(
        default=MissionStatus.PENDING, sa_column=Column(SAEnum(MissionStatus))
    )
    initiator_id: int = Field(foreign_key="users.id", index=True)
    active_plan_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("mission_plans.id", use_alter=True)),
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )

    # Relationships
    initiator: User = Relationship(sa_relationship=relationship("User", back_populates="missions"))
    tasks: list[Task] = Relationship(
        sa_relationship=relationship(
            "Task", back_populates="mission", foreign_keys="[Task.mission_id]"
        )
    )
    mission_plans: list[MissionPlan] = Relationship(
        sa_relationship=relationship(
            "MissionPlan", back_populates="mission", foreign_keys="[MissionPlan.mission_id]"
        )
    )
    events: list[MissionEvent] = Relationship(
        sa_relationship=relationship("MissionEvent", back_populates="mission")
    )


class JSONText(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that serializes JSON to Text for storage
    and deserializes Text to JSON on retrieval.
    Ensures compatibility with SQLite while allowing dict/list usage in Python.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Always serialize to JSON string to preserve type info
        # This handles dict, list, int, bool, and str correctly
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value


class MissionPlan(SQLModel, table=True):
    __tablename__ = "mission_plans"
    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="missions.id", index=True)
    version: int = Field(default=1)
    planner_name: str = Field(max_length=100)
    status: PlanStatus = Field(default=PlanStatus.DRAFT, sa_column=Column(SAEnum(PlanStatus)))
    score: float = Field(default=0.0)
    rationale: str | None = Field(sa_column=Column(Text))
    # Avoid JSONB for SQLite compat
    raw_json: Any | None = Field(sa_column=Column(JSONText))
    stats_json: Any | None = Field(sa_column=Column(JSONText))
    warnings_json: Any | None = Field(sa_column=Column(JSONText))
    content_hash: str | None = Field(max_length=64)

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    # Relationships
    mission: Mission = Relationship(
        sa_relationship=relationship(
            "Mission", back_populates="mission_plans", foreign_keys="[MissionPlan.mission_id]"
        )
    )
    tasks: list[Task] = Relationship(sa_relationship=relationship("Task", back_populates="plan"))


class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="missions.id", index=True)
    plan_id: int | None = Field(default=None, foreign_key="mission_plans.id", index=True)
    task_key: str = Field(max_length=50)
    description: str | None = Field(sa_column=Column(Text))
    tool_name: str | None = Field(max_length=100)
    # Avoid JSONB for SQLite compat, use JSON if available or Text
    tool_args_json: Any | None = Field(
        default=None, sa_column=Column(JSONText)
    )  # Postgres specific or use string
    status: TaskStatus = Field(default=TaskStatus.PENDING, sa_column=Column(SAEnum(TaskStatus)))
    attempt_count: int = Field(default=0)
    max_attempts: int = Field(default=3)
    priority: int = Field(default=0)
    risk_level: str | None = Field(max_length=50)
    criticality: str | None = Field(max_length=50)
    depends_on_json: Any | None = Field(default=None, sa_column=Column(JSONText))
    result_text: str | None = Field(sa_column=Column(Text))
    result_meta_json: Any | None = Field(default=None, sa_column=Column(JSONText))
    error_text: str | None = Field(sa_column=Column(Text))

    started_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True)))
    finished_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True)))
    next_retry_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True)))
    duration_ms: int | None = Field(default=0)

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )

    # Relationships
    mission: Mission = Relationship(
        sa_relationship=relationship(
            "Mission", back_populates="tasks", foreign_keys="[Task.mission_id]"
        )
    )
    plan: MissionPlan = Relationship(
        sa_relationship=relationship(
            "MissionPlan", back_populates="tasks", foreign_keys="[Task.plan_id]"
        )
    )


class MissionEvent(SQLModel, table=True):
    __tablename__ = "mission_events"
    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="missions.id", index=True)
    event_type: MissionEventType = Field(sa_column=Column(SAEnum(MissionEventType)))
    payload_json: Any | None = Field(default=None, sa_column=Column(JSONText))

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    # Relationships
    mission: Mission = Relationship(
        sa_relationship=relationship("Mission", back_populates="events")
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


# Helpers
def log_mission_event(mission: Mission, event_type: MissionEventType, payload: dict, session=None):
    import json

    evt = MissionEvent(
        mission_id=mission.id, event_type=event_type, payload_json=json.dumps(payload)
    )
    if session:
        session.add(evt)


def update_mission_status(
    mission: Mission, status: MissionStatus, note: str | None = None, session=None
):
    mission.status = status
    mission.updated_at = utc_now()


# Rebuild models for forward refs
try:
    SQLModel.model_rebuild()
except Exception:
    import traceback

    traceback.print_exc()
