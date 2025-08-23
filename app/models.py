# app/models.py
# ======================================================================================
# ==============  COGNIFORGE AKASHIC GENOME v7.0 – FINAL EVOLVED SCHEMA  ===============
# ======================================================================================
# هذا الملف هو الدستور البنيوي النهائي (حتى اللحظة) لذاكرة وذكاء النظام.
# مبادئ التصميم:
#  1. Consistency  : قيود + Enums تقلل الانجراف.
#  2. Observability: Telemetry، MissionEvent، حقول قياس دقيقة.
#  3. Evolvability : JSONB للحقول المتغيرة، native_enum=False للتعديل السلس.
#  4. Integrity    : Unique / Check / Composite Indexes + آليات ضبط.
#  5. Safety       : قفل المهمات بعد الإنهاء، تسلسل خطوات موجب، تسجيل أحداث.
#
# بعد أي تعديل: أنشئ Migration وراجعه يدوياً.
# ======================================================================================

from __future__ import annotations

import enum
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    Index,
    text,
    func,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from app import db, login_manager

# ======================================================================================
# Utilities
# ======================================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

# ======================================================================================
# Enumerations
# ======================================================================================

class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

class MessageRating(enum.Enum):
    GOOD = "good"
    BAD = "bad"
    NEUTRAL = "neutral"

class MissionStatus(enum.Enum):
    PENDING   = "PENDING"
    PLANNING  = "PLANNING"
    RUNNING   = "RUNNING"
    ADAPTING  = "ADAPTING"
    SUCCESS   = "SUCCESS"
    FAILED    = "FAILED"
    CANCELED  = "CANCELED"

class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED  = "FAILED"
    SKIPPED = "SKIPPED"

class TaskType(enum.Enum):
    TOOL      = "TOOL"
    REASON    = "REASON"
    PLAN      = "PLAN"
    CRITIC    = "CRITIC"
    SUMMARIZE = "SUMMARIZE"

class MissionEventType(enum.Enum):
    CREATED        = "CREATED"
    STATUS_CHANGE  = "STATUS_CHANGE"
    TASK_ADDED     = "TASK_ADDED"
    TASK_UPDATED   = "TASK_UPDATED"
    REPLAN         = "REPLAN"
    ADAPT_START    = "ADAPT_START"
    ADAPT_COMPLETE = "ADAPT_COMPLETE"
    FINALIZED      = "FINALIZED"
    CANCELED       = "CANCELED"
    FAILURE        = "FAILURE"

# ======================================================================================
# Mixins
# ======================================================================================

class Timestamped:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), default=utc_now, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), default=utc_now, onupdate=utc_now, index=True)

# ======================================================================================
# User
# ======================================================================================

class User(UserMixin, Timestamped, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(150), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin      = db.Column(db.Boolean, nullable=False, default=False, server_default=text("false"))

    conversations = db.relationship("Conversation", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    missions      = db.relationship("Mission", backref="initiator", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"

# ======================================================================================
# Conversations & Messages
# ======================================================================================

class Conversation(Timestamped, db.Model):
    __tablename__ = "conversations"

    id       = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    messages = db.relationship(
        "Message",
        backref="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Message.id"
    )

    summary_cache = db.Column(db.Text, nullable=True)       # ملخص سريع (اختياري)
    meta          = db.Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<Conversation id={self.id} user={self.user_id}>"

class Message(db.Model):
    __tablename__ = "messages"

    id              = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role            = db.Column(SAEnum(MessageRole, native_enum=False, length=20), nullable=False, index=True)
    content         = db.Column(db.Text, nullable=False)
    timestamp       = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    tool_name       = db.Column(db.String(120), nullable=True, index=True)
    tool_ok_status  = db.Column(db.Boolean, nullable=True)
    rating          = db.Column(SAEnum(MessageRating, native_enum=False, length=15), nullable=True, index=True)

    meta            = db.Column(JSONB, nullable=True)
    content_hash    = db.Column(db.String(64), nullable=True, index=True)
    tokens_estimate = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        CheckConstraint("length(content) > 0", name="ck_message_nonempty"),
        Index("ix_message_conv_role_time", "conversation_id", "role", "timestamp"),
    )

    def ensure_hash(self):
        if not self.content_hash:
            self.content_hash = hash_content(self.content)

    def __repr__(self):
        return f"<Message id={self.id} role={self.role.value}>"

@event.listens_for(Message, "before_insert")
def _auto_hash_before_insert(mapper, connection, target: Message):
    target.ensure_hash()

# ======================================================================================
# Missions & Tasks
# ======================================================================================

class Mission(Timestamped, db.Model):
    __tablename__ = "missions"

    id            = db.Column(db.Integer, primary_key=True)
    objective     = db.Column(db.Text, nullable=False)
    status        = db.Column(SAEnum(MissionStatus, native_enum=False, length=20), nullable=False, default=MissionStatus.PENDING.value, index=True)
    initiator_id  = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Lifecycle planning
    plan_version  = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"), index=True)
    plan_json     = db.Column(JSONB, nullable=True)
    last_adapted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Results
    result_text   = db.Column(db.Text, nullable=True)
    result_meta   = db.Column(JSONB, nullable=True)

    # Telemetry / aggregated metrics
    telemetry     = db.Column(JSONB, nullable=True)

    # Safety & control
    locked        = db.Column(db.Boolean, nullable=False, default=False, server_default=text("false"), index=True)

    # Counters
    tasks_count   = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    tasks_success = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    tasks_failed  = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))

    tasks = db.relationship(
        "Task",
        backref="mission",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Task.sequence_id"
    )
    events = db.relationship(
        "MissionEvent",
        backref="mission",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="MissionEvent.id"
    )

    __table_args__ = (
        Index("ix_mission_status_initiator", "status", "initiator_id"),
    )

    def __repr__(self):
        return f"<Mission id={self.id} status={self.status.value} locked={self.locked}>"

class Task(Timestamped, db.Model):
    __tablename__ = "tasks"

    id          = db.Column(db.Integer, primary_key=True)
    mission_id  = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_id = db.Column(db.Integer, nullable=False)

    step_type   = db.Column(SAEnum(TaskType, native_enum=False, length=15), nullable=False, default=TaskType.TOOL.value, index=True)
    description = db.Column(db.Text, nullable=False)

    tool_name   = db.Column(db.String(255), nullable=True, index=True)
    tool_args   = db.Column(JSONB, nullable=True)

    status      = db.Column(SAEnum(TaskStatus, native_enum=False, length=15), nullable=False, default=TaskStatus.PENDING.value, index=True)

    # Result payloads
    result_text = db.Column(db.Text, nullable=True)
    result_meta = db.Column(JSONB, nullable=True)

    # Execution metrics
    elapsed_ms      = db.Column(db.Float, nullable=True)
    attempts        = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    prompt_tokens   = db.Column(db.Integer, nullable=True)
    completion_tokens = db.Column(db.Integer, nullable=True)
    cost_usd        = db.Column(db.Numeric(12, 6), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("mission_id", "sequence_id", name="uq_task_mission_sequence"),
        Index("ix_task_mission_status", "mission_id", "status"),
        CheckConstraint("sequence_id > 0", name="ck_task_sequence_positive"),
        CheckConstraint("attempts >= 0", name="ck_task_attempts_nonnegative"),
    )

    def __repr__(self):
        return f"<Task id={self.id} mission={self.mission_id} seq={self.sequence_id} status={self.status.value}>"

# ======================================================================================
# Mission Events (Audit / Trace)
# ======================================================================================

class MissionEvent(Timestamped, db.Model):
    __tablename__ = "mission_events"

    id          = db.Column(db.Integer, primary_key=True)
    mission_id  = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type  = db.Column(SAEnum(MissionEventType, native_enum=False, length=30), nullable=False, index=True)
    payload     = db.Column(JSONB, nullable=True)
    note        = db.Column(db.String(300), nullable=True)

    __table_args__ = (
        Index("ix_mission_event_type_time", "event_type", "created_at"),
    )

    def __repr__(self):
        return f"<MissionEvent mission={self.mission_id} type={self.event_type.value}>"

# ======================================================================================
# Indexes (Additional)
# ======================================================================================

Index("ix_message_conv_hash", Message.conversation_id, Message.content_hash)
Index("ix_task_status_type", Task.status, Task.step_type)
Index("ix_task_tool_name", Task.tool_name)
Index("ix_message_role_time", Message.role, Message.timestamp)

# ======================================================================================
# Helper / Service-Like Builders
# ======================================================================================

def create_message(
    conversation_id: str,
    role: MessageRole,
    content: str,
    *,
    tool_name: Optional[str] = None,
    tool_ok: Optional[bool] = None,
    rating: Optional[MessageRating] = None,
    meta: Optional[Dict[str, Any]] = None,
    content_hash: Optional[str] = None,
    timestamp_override: Optional[datetime] = None,
    tokens_estimate: Optional[int] = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tool_name=tool_name,
        tool_ok_status=tool_ok,
        rating=rating,
        meta=meta,
        content_hash=content_hash or hash_content(content),
        timestamp=timestamp_override or utc_now(),
        tokens_estimate=tokens_estimate,
    )
    db.session.add(msg)
    return msg

def append_task(
    mission: Mission,
    description: str,
    *,
    step_type: TaskType = TaskType.TOOL,
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None
) -> Task:
    if mission.locked:
        raise ValueError("Mission is locked; cannot append new tasks.")
    next_seq = (mission.tasks_count or 0) + 1
    task = Task(
        mission_id=mission.id,
        sequence_id=next_seq,
        step_type=step_type,
        description=description,
        tool_name=tool_name,
        tool_args=tool_args,
    )
    mission.tasks_count = next_seq
    db.session.add(task)
    log_mission_event(mission, MissionEventType.TASK_ADDED, payload={"sequence": next_seq, "step_type": step_type.value, "tool": tool_name})
    return task

def log_mission_event(
    mission: Mission,
    event_type: MissionEventType,
    *,
    payload: Optional[Dict[str, Any]] = None,
    note: Optional[str] = None
) -> MissionEvent:
    evt = MissionEvent(
        mission_id=mission.id,
        event_type=event_type,
        payload=payload,
        note=note
    )
    db.session.add(evt)
    return evt

def finalize_task(
    task: Task,
    *,
    status: TaskStatus,
    result_text: Optional[str] = None,
    result_meta: Optional[Dict[str, Any]] = None,
    elapsed_ms: Optional[float] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    cost_usd: Optional[float] = None
) -> Task:
    if status not in {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED}:
        raise ValueError("finalize_task expects a terminal status.")
    task.status = status
    if result_text is not None:
        task.result_text = result_text
    if result_meta is not None:
        task.result_meta = result_meta
    if elapsed_ms is not None:
        task.elapsed_ms = elapsed_ms
    if prompt_tokens is not None:
        task.prompt_tokens = prompt_tokens
    if completion_tokens is not None:
        task.completion_tokens = completion_tokens
    if cost_usd is not None:
        task.cost_usd = cost_usd
    task.attempts = (task.attempts or 0) + 1

    mission: Mission = task.mission
    if status == TaskStatus.SUCCESS:
        mission.tasks_success = (mission.tasks_success or 0) + 1
    elif status == TaskStatus.FAILED:
        mission.tasks_failed = (mission.tasks_failed or 0) + 1
    log_mission_event(mission, MissionEventType.TASK_UPDATED, payload={"task_id": task.id, "status": status.value})
    return task

def update_mission_status(mission: Mission, new_status: MissionStatus, *, note: Optional[str] = None):
    if mission.locked and new_status not in {MissionStatus.CANCELED, MissionStatus.FAILED}:
        raise ValueError("Locked mission cannot change status except to FAILED or CANCELED.")
    old_status = mission.status
    mission.status = new_status
    if new_status in {MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED}:
        mission.locked = True
    log_mission_event(mission, MissionEventType.STATUS_CHANGE, payload={"from": old_status.value, "to": new_status.value}, note=note)

def replan_mission(mission: Mission, new_plan: Dict[str, Any], *, note: Optional[str] = None):
    if mission.locked:
        raise ValueError("Cannot replan a locked mission.")
    mission.plan_version = (mission.plan_version or 0) + 1
    mission.plan_json = new_plan
    mission.last_adapted_at = utc_now()
    update_mission_status(mission, MissionStatus.ADAPTING) # or PLANNING
    log_mission_event(mission, MissionEventType.REPLAN, payload={"plan_version": mission.plan_version}, note=note)

def sync_mission_counters(mission: Mission):
    actual_total = db.session.query(Task).filter_by(mission_id=mission.id).count()
    if mission.tasks_count != actual_total:
        mission.tasks_count = actual_total
    success_count = db.session.query(Task).filter_by(mission_id=mission.id, status=TaskStatus.SUCCESS).count()
    fail_count    = db.session.query(Task).filter_by(mission_id=mission.id, status=TaskStatus.FAILED).count()
    if mission.tasks_success != success_count:
        mission.tasks_success = success_count
    if mission.tasks_failed != fail_count:
        mission.tasks_failed = fail_count

# ======================================================================================
# Future Extension Guidelines
# ======================================================================================
# - جدولة تنفيذ Tasks عبر طابور (Redis / Celery) والتزامن مع الحقول الموجودة.
# - إضافة حقل priority في Task لجدولة ذكية.
# - إضافة integrity job يتحقق من التناقضات (missions locked yet RUNNING tasks).
# - توسيع Mission.telemetry لتخزين moving averages.
# ======================================================================================
# END OF FILE
# ======================================================================================