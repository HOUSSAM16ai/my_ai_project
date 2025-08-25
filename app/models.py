# app/models.py
# ======================================================================================
#  COGNIFORGE DOMAIN MODELS v12.2  "TIMESTAMP GUARD / OVERMIND+ MAESTRO SAFE"          #
# ======================================================================================
#  WHY v12.2?
#    (1) حلّ المشكلة التي ظهرت في التنفيذ:
#          psycopg2.errors.DatatypeMismatch: column "started_at" is of type timestamp with time zone but expression is of type numeric
#        السبب كان إسناد أرقام float (time.time()) مباشرةً إلى أعمدة DateTime.
#
#    (2) إضافة طبقة حراسة (Guard Layer) تحوّل أي قيمة (float/int/str ISO) يتم تمريرها
#        إلى started_at / finished_at / next_retry_at إلى datetime UTC تلقائياً قبل الحفظ.
#
#    (3) واجهات مريحة:
#        - Task.mark_started()
#        - Task.mark_finished()
#        - Task.schedule_retry(backoff_seconds)
#        - Task.compute_duration()
#
#    (4) ضبط finalize_task ليستخدم utc_now ويُضيف حدثاً منظماً.
#
#    (5) تحسين __repr__ لتسهيل التشخيص، وإضافة خصائص مشتقة:
#        - Task.is_terminal
#        - Task.duration_seconds (قراءة فقط)
#
#    (6) دوال مساعدة إضافية:
#        - coerce_datetime(value): تحويل آمن للقيم المختلفة إلى datetime
#
#    (7) تحسين تعاريف العلاقات مع overlaps و foreign_keys بوضوح كما في 12.1.
#
#  ملاحظة:
#    مصدر الخطأ الأصلي هو SERVICE (مثل master_agent_service) الذي كان يكتب time.time().
#    هذا الإصدار يعمل حتى لو استمر ذلك مؤقتاً، لأنه سيحوّل float -> datetime UTC.
#
# ======================================================================================

from __future__ import annotations

import enum
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict, List, Union

from flask_login import UserMixin
from sqlalchemy import (
    func, text,
    ForeignKey,
    UniqueConstraint,
    Index,
    TypeDecorator,
    JSON as SAJSON,
    event
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    relationship, backref,
    Mapped, mapped_column
)

from app import db, login_manager

# ======================================================================================
# UTILITIES
# ======================================================================================

class JSONB_or_JSON(TypeDecorator):
    """
    اختيار JSONB في PostgreSQL وإلا JSON عادي في باقي المحركات.
    """
    impl = SAJSON
    cache_ok = True
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSONB()) if dialect.name == 'postgresql' else dialect.type_descriptor(SAJSON())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def coerce_datetime(value: Any) -> Optional[datetime]:
    """
    يحوّل عدة أنواع إلى datetime(timezone=UTC):

      - None -> None
      - datetime (مع / بدون tz) -> مع إلحاق UTC إن لم توجد
      - int / float (epoch seconds) -> datetime UTC
      - str ISO8601 -> محاولة التحويل
      - أي قيمة غير معروفة -> تُهمل (ترجع None)
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(value, str):
        # محاولات ISO شائعة
        for fmt in ("%Y-%m-%d %H:%M:%S.%f%z",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S%z",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f%z",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
        # محاولة أخيرة: fromisoformat
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
    # غير مدعوم
    return None

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

# ======================================================================================
# ENUMS
# ======================================================================================

class MessageRole(enum.Enum):
    USER="user"; ASSISTANT="assistant"; TOOL="tool"; SYSTEM="system"

class MissionStatus(enum.Enum):
    PENDING="PENDING"; PLANNING="PLANNING"; PLANNED="PLANNED"; RUNNING="RUNNING"
    ADAPTING="ADAPTING"; SUCCESS="SUCCESS"; FAILED="FAILED"; CANCELED="CANCELED"

class TaskStatus(enum.Enum):
    PENDING="PENDING"; RUNNING="RUNNING"; SUCCESS="SUCCESS"; FAILED="FAILED"; RETRY="RETRY"; SKIPPED="SKIPPED"

class PlanStatus(enum.Enum):
    DRAFT="DRAFT"; VALID="VALID"; SUPERSEDED="SUPERSEDED"; FAILED="FAILED"

class TaskType(enum.Enum):
    TOOL="TOOL"; SYSTEM="SYSTEM"; META="META"; VERIFICATION="VERIFICATION"

class MissionEventType(enum.Enum):
    CREATED="CREATED"; STATUS_CHANGE="STATUS_CHANGE"; PLAN_SELECTED="PLAN_SELECTED"
    EXECUTION_STARTED="EXECUTION_STARTED"; TASK_STARTED="TASK_STARTED"
    TASK_COMPLETED="TASK_COMPLETED"; TASK_FAILED="TASK_FAILED"
    REPLAN_TRIGGERED="REPLAN_TRIGGERED"; REPLAN_APPLIED="REPLAN_APPLIED"; FINALIZED="FINALIZED"

# ======================================================================================
# MIXINS
# ======================================================================================

class Timestamped:
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False,
        server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=utc_now
    )

# ======================================================================================
# USER
# ======================================================================================

class User(UserMixin, Timestamped, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    email: Mapped[str] = mapped_column(db.String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(db.String(256))
    is_admin: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False, server_default=text("false"))

    missions: Mapped[List["Mission"]] = relationship("Mission", back_populates="initiator", cascade="all, delete-orphan")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password: str):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"

# ======================================================================================
# EDUCATIONAL MODELS (OPTIONAL)
# ======================================================================================

class Subject(Timestamped, db.Model):
    __tablename__ = 'subjects'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text)
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="subject", cascade="all, delete-orphan")

class Lesson(Timestamped, db.Model):
    __tablename__ = 'lessons'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(250))
    content: Mapped[Optional[str]] = mapped_column(db.Text)
    subject_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('subjects.id', ondelete="CASCADE"), index=True)
    subject: Mapped[Subject] = relationship("Subject", back_populates="lessons")
    exercises: Mapped[List["Exercise"]] = relationship("Exercise", back_populates="lesson", cascade="all, delete-orphan")

class Exercise(Timestamped, db.Model):
    __tablename__ = 'exercises'
    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[Optional[str]] = mapped_column(db.Text)
    correct_answer_data: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    lesson_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('lessons.id', ondelete="CASCADE"), index=True)
    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="exercises")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="exercise", cascade="all, delete-orphan")

class Submission(Timestamped, db.Model):
    __tablename__ = 'submissions'
    id: Mapped[int] = mapped_column(primary_key=True)
    student_answer_data: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    is_correct: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    feedback: Mapped[Optional[str]] = mapped_column(db.Text)
    user_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), index=True)
    exercise_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('exercises.id', ondelete="CASCADE"), index=True)
    student: Mapped[User] = relationship("User", back_populates="submissions")
    exercise: Mapped[Exercise] = relationship("Exercise", back_populates="submissions")

# ======================================================================================
# CORE: Mission / MissionPlan / Task / MissionEvent
# ======================================================================================

class Mission(Timestamped, db.Model):
    __tablename__ = "missions"
    id: Mapped[int] = mapped_column(primary_key=True)
    objective: Mapped[str] = mapped_column(db.Text, nullable=False)
    status: Mapped[MissionStatus] = mapped_column(db.Enum(MissionStatus, native_enum=False), default=MissionStatus.PENDING, index=True)
    initiator_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    active_plan_id: Mapped[Optional[int]] = mapped_column(db.Integer, ForeignKey("mission_plans.id", use_alter=True), nullable=True)

    locked: Mapped[bool] = mapped_column(db.Boolean, default=False, server_default=text("false"))
    result_summary: Mapped[Optional[str]] = mapped_column(db.Text)
    total_cost_usd = mapped_column(db.Numeric(12, 6))
    adaptive_cycles: Mapped[int] = mapped_column(db.Integer, default=0)

    initiator: Mapped[User] = relationship("User", back_populates="missions")

    plans: Mapped[List["MissionPlan"]] = relationship(
        "MissionPlan",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="desc(MissionPlan.version)",
        foreign_keys="MissionPlan.mission_id",
        overlaps="active_plan,mission"
    )

    active_plan: Mapped[Optional["MissionPlan"]] = relationship(
        "MissionPlan",
        foreign_keys=[active_plan_id],
        post_update=True,
        uselist=False,
        overlaps="plans,mission"
    )

    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="mission", cascade="all, delete-orphan")
    events: Mapped[List["MissionEvent"]] = relationship("MissionEvent", back_populates="mission", cascade="all, delete-orphan", order_by="MissionEvent.id")

    def __repr__(self):
        return f"<Mission id={self.id} status={self.status.value} objective={self.objective[:30]!r}>"

class MissionPlan(Timestamped, db.Model):
    __tablename__ = "mission_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    planner_name: Mapped[Optional[str]] = mapped_column(db.String(120))
    status: Mapped[PlanStatus] = mapped_column(db.Enum(PlanStatus, native_enum=False), default=PlanStatus.VALID, index=True)
    score: Mapped[Optional[float]] = mapped_column(db.Float)
    rationale: Mapped[Optional[str]] = mapped_column(db.Text)
    raw_json: Mapped[dict] = mapped_column(JSONB_or_JSON)
    stats_json: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    warnings_json: Mapped[Optional[list]] = mapped_column(JSONB_or_JSON)
    content_hash: Mapped[Optional[str]] = mapped_column(db.String(128), index=True)

    mission: Mapped[Mission] = relationship(
        "Mission",
        back_populates="plans",
        foreign_keys=[mission_id],
        overlaps="active_plan,plans"
    )

    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("mission_id", "version", name="uq_mission_plan_version"),)

    def __repr__(self):
        return f"<MissionPlan id={self.id} v={self.version} planner={self.planner_name} score={self.score}>"

# جدول اختياري للتبعيات
task_dependencies = db.Table(
    'task_dependencies',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete="CASCADE"), primary_key=True),
    db.Column('depends_on_task_id', db.Integer, db.ForeignKey('tasks.id', ondelete="CASCADE"), primary_key=True),
)

class Task(Timestamped, db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("mission_plans.id", ondelete="CASCADE"), index=True)
    task_key: Mapped[str] = mapped_column(db.String(120), index=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text)
    task_type: Mapped[TaskType] = mapped_column(db.Enum(TaskType, native_enum=False), default=TaskType.TOOL, index=True)
    tool_name: Mapped[Optional[str]] = mapped_column(db.String(255), index=True)
    tool_args_json: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    depends_on_json: Mapped[Optional[list]] = mapped_column(JSONB_or_JSON)
    priority: Mapped[int] = mapped_column(db.Integer, default=0)
    risk_level: Mapped[Optional[str]] = mapped_column(db.String(20))
    criticality: Mapped[Optional[str]] = mapped_column(db.String(20))
    status: Mapped[TaskStatus] = mapped_column(db.Enum(TaskStatus, native_enum=False), default=TaskStatus.PENDING, index=True)
    attempt_count: Mapped[int] = mapped_column(db.Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(db.Integer, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    result_text: Mapped[Optional[str]] = mapped_column(db.Text)
    error_text: Mapped[Optional[str]] = mapped_column(db.Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(db.Integer)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    result: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    cost_usd = mapped_column(db.Numeric(12, 6))

    mission: Mapped[Mission] = relationship("Mission", back_populates="tasks")
    plan: Mapped[MissionPlan] = relationship("MissionPlan", back_populates="tasks", overlaps="plans,active_plan,mission")

    dependencies: Mapped[List["Task"]] = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=(id == task_dependencies.c.task_id),
        secondaryjoin=(id == task_dependencies.c.depends_on_task_id),
        backref=backref("dependents")
    )

    __table_args__ = (
        Index("ix_task_mission_status", "mission_id", "status"),
        Index("ix_task_plan_taskkey", "plan_id", "task_key"),
    )

    # ---------- Convenience / Derived ----------
    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.duration_ms is not None:
            return self.duration_ms / 1000.0
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    # ---------- Lifecycle convenience ----------
    def mark_started(self):
        self.status = TaskStatus.RUNNING
        self.started_at = utc_now()

    def mark_finished(self, status: TaskStatus, result_text: str | None = None, error: str | None = None):
        if status not in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED):
            raise ValueError("mark_finished expects a terminal status.")
        self.status = status
        self.finished_at = utc_now()
        if self.started_at and self.finished_at:
            self.duration_ms = int((self.finished_at - self.started_at).total_seconds() * 1000)
        if result_text:
            self.result_text = result_text
        if error:
            self.error_text = error

    def schedule_retry(self, backoff_seconds: float):
        self.status = TaskStatus.RETRY
        self.next_retry_at = utc_now() + timedelta(seconds=backoff_seconds)

    def compute_duration(self):
        if self.started_at and self.finished_at:
            self.duration_ms = int((self.finished_at - self.started_at).total_seconds() * 1000)

    def __repr__(self):
        return f"<Task id={self.id} key={self.task_key} status={self.status.value}>"

class MissionEvent(Timestamped, db.Model):
    __tablename__ = "mission_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[MissionEventType] = mapped_column(db.Enum(MissionEventType, native_enum=False), index=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    note: Mapped[Optional[str]] = mapped_column(db.String(500))
    mission: Mapped[Mission] = relationship("Mission", back_populates="events")
    task: Mapped[Optional[Task]] = relationship("Task")

    def __repr__(self):
        return f"<MissionEvent id={self.id} type={self.event_type.value}>"

# ======================================================================================
# MODEL-LEVEL EVENT LISTENERS (Timestamp Autocoerce)
# ======================================================================================

def _coerce_task_datetime_fields(mapper, connection, target: Task):
    """
    يحوّل أي قيم غير datetime في الحقول الحساسة إلى datetime UTC:
      started_at / finished_at / next_retry_at
    """
    for field_name in ("started_at", "finished_at", "next_retry_at"):
        raw = getattr(target, field_name, None)
        coerced = coerce_datetime(raw)
        if raw is not None and coerced is None:
            # إن وصلت قيمة غير قابلة للتحويل تبقى كما هي (أو يمكن تصفيرها)
            setattr(target, field_name, None)
        else:
            setattr(target, field_name, coerced)

event.listen(Task, "before_insert", _coerce_task_datetime_fields)
event.listen(Task, "before_update", _coerce_task_datetime_fields)

# ======================================================================================
# HELPERS
# ======================================================================================

def update_mission_status(mission: Mission, new_status: MissionStatus, note: Optional[str] = None):
    old_status = mission.status
    if old_status != new_status:
        mission.status = new_status
        evt = MissionEvent(
            mission_id=mission.id,
            event_type=MissionEventType.STATUS_CHANGE,
            payload={"old": old_status.value, "new": new_status.value},
            note=note
        )
        db.session.add(evt)

def log_mission_event(
    mission: Mission,
    event_type: MissionEventType,
    *,
    task: Optional[Task] = None,
    payload: Optional[Dict[str, Any]] = None,
    note: Optional[str] = None
) -> MissionEvent:
    evt = MissionEvent(
        mission_id=mission.id,
        task_id=task.id if task else None,
        event_type=event_type,
        payload=payload,
        note=note
    )
    db.session.add(evt)
    return evt

def finalize_task(
    task: Task,
    status: TaskStatus,
    *,
    result_text: Optional[str] = None,
    error_text: Optional[str] = None
):
    """
    إنهاء مهمة (Terminal) وتسجيل حدث.
    """
    if status not in {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED}:
        raise ValueError("finalize_task expects a terminal TaskStatus.")
    # حافظ على started_at إن كانت موجودة
    if task.started_at is None:
        task.started_at = utc_now()
    task.finished_at = utc_now()
    task.compute_duration()
    task.status = status
    if result_text is not None:
        task.result_text = result_text
    if error_text is not None:
        task.error_text = error_text
    event_type = MissionEventType.TASK_COMPLETED if status == TaskStatus.SUCCESS else MissionEventType.TASK_FAILED
    log_mission_event(
        task.mission,
        event_type,
        task=task,
        payload={
            "status": status.value,
            "result_excerpt": (task.result_text or "")[:120],
            "error_excerpt": (task.error_text or "")[:120],
            "duration_ms": task.duration_ms
        }
    )

# ======================================================================================
# END OF FILE
# ======================================================================================