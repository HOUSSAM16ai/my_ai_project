# ======================================================================================
#  COGNIFORGE DOMAIN MODELS  v13.2  • "UNIFIED OVERMIND⇄MAESTRO NEURO-LAYER (Pro+)"   #
# ======================================================================================
#  PURPOSE (الغرض):
#    نموذج نطاق (Domain Model) موحّد دلالياً بين طبقات:
#      - Overmind Orchestrator
#      - Maestro Generation Service
#    مع دعم أحداث مهمة (Mission Events) تحليلية/نهائية أوسع.
#
#  WHAT'S NEW in v13.2 (مقارنة بـ v13.1):
#    - توضيح الوضع الفعلي لعمود mission_events.event_type بعد الهجرة "الخارقة":
#        أصبح نوعه TEXT (غير محدود عملياً) + (اختياري) CHECK ≤ 128.
#    - تصحيح الملاحظة السابقة (لم تكن دقيقة دائماً) بخصوص "لا حاجة لهجرة":
#        رغم استخدام native_enum=False، الإنشاء الأولي أعطى VARCHAR(17) فتطلّبنا هجرة
#        لتوسيعه عند إضافة قيمة أطول (ARCHITECTURE_CLASSIFIED).
#    - توثيق سلسلة الهجرات المتعلقة بالموديلات الأساسية.
#
#  SEMANTIC MISSION EVENTS (الإصدار التحليلي):
#      MISSION_UPDATED, RISK_SUMMARY, ARCHITECTURE_CLASSIFIED,
#      MISSION_COMPLETED, MISSION_FAILED, FINALIZED
#
#  CORE UPGRADES vs v13.0 (مراجعة سريعة):
#    1) توسيع MissionEventType لتحليلات أغنى ولوحات مراقبة.
#    2) توافق خلفي: المستهلكون القدامى ما زالوا يعتمدون على FINALIZED و STATUS_CHANGE.
#    3) فصل واضح بين:
#         - الأحداث الانتقالية  (STATUS_CHANGE)
#         - التصنيف التحليلي   (RISK_SUMMARY / ARCHITECTURE_CLASSIFIED)
#         - المخرجات النهائية   (MISSION_COMPLETED / MISSION_FAILED / FINALIZED)
#    4) المحافظة على finalize_task idempotent.
#
#  PRE-EXISTING FEATURES:
#    - result_meta_json قناة وصفية للنتائج
#    - تحويل الطوابع الزمنية المرنة (coerce_datetime)
#    - منطق إعادة المحاولة (retry scheduling)
#    - حساب مدة متسق (compute_duration)
#    - فهارس متكررة الاستعلام
#    - تهشير المحتوى (hash_content)
#    - إحصاءات مشتقة على Mission (success_ratio ...)
#    - واجهات موحّدة (update_mission_status / log_mission_event / finalize_task)
#    - JSONB_or_JSON تجريد PostgreSQL/SQLite
#
#  MIGRATION HISTORY (ذات صلة):
#    - 0fe9bd3b1f3c : Genesis schema
#    - 0b5107e8283d : إضافة result_meta_json لِـ Task
#    - 20250902_event_type_text_and_index_super :
#         * تحويل mission_events.event_type إلى TEXT
#         * فهرس مركّب (mission_id, created_at, event_type)
#         * (اختياري) CHECK (char_length(event_type) <= 128)
#
#  NOTE (مهم):
#    - استخدام db.Enum(..., native_enum=False) يعني تخزين القيم كسلاسل (VARCHAR/TEXT)،
#      ولكن الطول الابتدائي يمكن أن يكون محدوداً (كما حدث: 17) => إضافة قيمة أطول
#      قد تتطلب هجرة توسيع أو تحويل إلى TEXT (وهو ما تم الآن).
#    - حالياً العمود TEXT: لا يلزم تعديل إضافي في هذا الملف لحل الخطأ السابق.
#    - إذا كان CHECK ≤ 128 مفعل في قاعدة البيانات، فهو طبقة حماية فقط؛ جميع القيم الحالية
#      أقل بكثير من 128.
#
#  TRANSACTION POLICY:
#    - هذا الملف لا يقوم بالـ commit. مسؤولية إدارة المعاملات تقع على الطبقات العليا
#      (الخدمات / orchestrator).
#
#  OPTIONAL FUTURE EXTENSIONS:
#    - إضافة Validator قبل log_mission_event للتحقق من الطول أو منع أحداث مكررة.
#    - استبدال Enum بنص حر + طبقة تحقق إذا أصبح التطور سريع الإيقاع جداً.
#
# ======================================================================================

from __future__ import annotations

import enum
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict, List

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
# CONFIG / CONSTANTS (اختياري — يعكس قيد الهجرة إذا كان مفعلاً)
# ======================================================================================

EVENT_TYPE_MAX_LEN = 128  # مطابقة للهجرة (إن وُجد CHECK). مرجع فقط—العمود TEXT.

# ======================================================================================
# UTILITIES
# ======================================================================================

class JSONB_or_JSON(TypeDecorator):
    """
    استخدام JSONB في PostgreSQL وإلا JSON قياسي (JSON).
    يحافظ على واجهة موحّدة للبيئات المختلفة.
    """
    impl = SAJSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return (
            dialect.type_descriptor(JSONB())
            if dialect.name == 'postgresql'
            else dialect.type_descriptor(SAJSON())
        )

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def coerce_datetime(value: Any) -> Optional[datetime]:
    """
    تحويل مرن إلى datetime بتوقيت UTC.
    يقبل: datetime / int أو float (Epoch) / string (مجموعة صيغ) / وإلا None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(value, str):
        fmts = (
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
        )
        for fmt in fmts:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
    return None

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

# ======================================================================================
# ENUMS
# ======================================================================================

class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

class MissionStatus(enum.Enum):
    PENDING  = "PENDING"
    PLANNING = "PLANNING"
    PLANNED  = "PLANNED"
    RUNNING  = "RUNNING"
    ADAPTING = "ADAPTING"
    SUCCESS  = "SUCCESS"
    FAILED   = "FAILED"
    CANCELED = "CANCELED"

class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED  = "FAILED"
    RETRY   = "RETRY"
    SKIPPED = "SKIPPED"

class PlanStatus(enum.Enum):
    DRAFT      = "DRAFT"
    VALID      = "VALID"
    SUPERSEDED = "SUPERSEDED"
    FAILED     = "FAILED"

class TaskType(enum.Enum):
    TOOL         = "TOOL"
    SYSTEM       = "SYSTEM"
    META         = "META"
    VERIFICATION = "VERIFICATION"

class MissionEventType(enum.Enum):
    # Lifecycle & Planning
    CREATED           = "CREATED"
    STATUS_CHANGE     = "STATUS_CHANGE"
    PLAN_SELECTED     = "PLAN_SELECTED"
    EXECUTION_STARTED = "EXECUTION_STARTED"

    # Task-level events
    TASK_STARTED   = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED    = "TASK_FAILED"

    # Adaptation / Replanning
    REPLAN_TRIGGERED = "REPLAN_TRIGGERED"
    REPLAN_APPLIED   = "REPLAN_APPLIED"

    # Generic / legacy
    MISSION_UPDATED = "MISSION_UPDATED"

    # Analytical
    RISK_SUMMARY            = "RISK_SUMMARY"
    ARCHITECTURE_CLASSIFIED = "ARCHITECTURE_CLASSIFIED"

    # Terminal outcomes
    MISSION_COMPLETED = "MISSION_COMPLETED"
    MISSION_FAILED    = "MISSION_FAILED"

    # Final closure marker
    FINALIZED = "FINALIZED"

# ======================================================================================
# MIXINS
# ======================================================================================

class Timestamped:
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=utc_now
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

    def set_password(self, password: str):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"



# ======================================================================================
# CORE: Mission / MissionPlan / Task / MissionEvent
# ======================================================================================

class Mission(Timestamped, db.Model):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    objective: Mapped[str] = mapped_column(db.Text, nullable=False)
    status: Mapped[MissionStatus] = mapped_column(
        db.Enum(MissionStatus, native_enum=False),
        default=MissionStatus.PENDING,
        index=True
    )
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
    events: Mapped[List["MissionEvent"]] = relationship(
        "MissionEvent",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionEvent.id"
    )

    # ---- Derived analytics ----
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)

    @property
    def completed_tasks(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.SUCCESS)

    @property
    def failed_tasks(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

    @property
    def success_ratio(self) -> float:
        if not self.tasks:
            return 0.0
        return self.completed_tasks / len(self.tasks)

    def __repr__(self):
        return f"<Mission id={self.id} status={self.status.value} objective={self.objective[:30]!r}>"

class MissionPlan(Timestamped, db.Model):
    __tablename__ = "mission_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    planner_name: Mapped[Optional[str]] = mapped_column(db.String(120))
    status: Mapped[PlanStatus] = mapped_column(
        db.Enum(PlanStatus, native_enum=False),
        default=PlanStatus.VALID,
        index=True
    )
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

# --- Optional explicit dependencies table ---
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

    status: Mapped[TaskStatus] = mapped_column(
        db.Enum(TaskStatus, native_enum=False),
        default=TaskStatus.PENDING,
        index=True
    )
    attempt_count: Mapped[int] = mapped_column(db.Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(db.Integer, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))

    # Results & telemetry
    result_text: Mapped[Optional[str]] = mapped_column(db.Text)
    error_text: Mapped[Optional[str]] = mapped_column(db.Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(db.Integer)

    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))

    result: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)           # Structured output
    result_meta_json: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)  # Free-form meta
    cost_usd = mapped_column(db.Numeric(12, 6))

    mission: Mapped[Mission] = relationship("Mission", back_populates="tasks")
    plan: Mapped[MissionPlan] = relationship(
        "MissionPlan", back_populates="tasks", overlaps="plans,active_plan,mission"
    )

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

    # ---------- Derived ----------
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

    # ---------- Lifecycle Helpers ----------
    def mark_started(self):
        if self.status not in (TaskStatus.PENDING, TaskStatus.RETRY, TaskStatus.RUNNING):
            return
        self.status = TaskStatus.RUNNING
        if not self.started_at:
            self.started_at = utc_now()

    def mark_finished(self, status: TaskStatus, result_text: Optional[str] = None, error: Optional[str] = None):
        if status not in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED):
            raise ValueError("mark_finished expects a terminal status.")
        self.status = status
        if not self.started_at:
            self.started_at = utc_now()
        self.finished_at = utc_now()
        self.compute_duration()
        if result_text is not None:
            self.result_text = result_text
        if error is not None:
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
    event_type: Mapped[MissionEventType] = mapped_column(
        db.Enum(MissionEventType, native_enum=False),
        index=True
    )
    payload: Mapped[Optional[dict]] = mapped_column(JSONB_or_JSON)
    note: Mapped[Optional[str]] = mapped_column(db.String(500))

    mission: Mapped[Mission] = relationship("Mission", back_populates="events")
    task: Mapped[Optional[Task]] = relationship("Task")

    def __repr__(self):
        return f"<MissionEvent id={self.id} type={self.event_type.value}>"



# ======================================================================================
# MODEL EVENT LISTENERS (Timestamp Coercion)
# ======================================================================================

def _coerce_task_datetime_fields(_mapper, _connection, target: Task):
    """
    يحوّل أي قيم (float/int/ISO) إلى datetime UTC للحقول:
      started_at, finished_at, next_retry_at
    """
    for attr in ("started_at", "finished_at", "next_retry_at"):
        raw = getattr(target, attr, None)
        coerced = coerce_datetime(raw)
        if raw is not None and coerced is None:
            setattr(target, attr, None)
        else:
            setattr(target, attr, coerced)

event.listen(Task, "before_insert", _coerce_task_datetime_fields)
event.listen(Task, "before_update", _coerce_task_datetime_fields)

# ======================================================================================
# HELPERS / SERVICE-LAYER BRIDGES
# ======================================================================================

def update_mission_status(mission: Mission, new_status: MissionStatus, note: Optional[str] = None):
    """
    تغيير حالة المهمة مع تسجيل حدث STATUS_CHANGE (دون commit).
    """
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
    """
    إضافة حدث إلى سجل المهمة (دون commit).
    يمكن توسيعه لاحقاً للتحقق من الطول أو منع التكرار.
    """
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
    إنهاء مهمة (Terminal) بشكل آمن و idempotent (بدون commit).
    """
    if status not in {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED}:
        raise ValueError("finalize_task expects a terminal TaskStatus.")

    # Idempotent guard
    if task.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED):
        if result_text and not task.result_text:
            task.result_text = result_text
        if error_text and not task.error_text:
            task.error_text = error_text
        return

    if task.started_at is None:
        task.started_at = utc_now()
    task.finished_at = utc_now()
    task.compute_duration()
    task.status = status

    if result_text is not None:
        task.result_text = result_text
    if error_text is not None:
        task.error_text = error_text

    event_type = (MissionEventType.TASK_COMPLETED
                  if status == TaskStatus.SUCCESS
                  else MissionEventType.TASK_FAILED)
    log_mission_event(
        task.mission,
        event_type,
        task=task,
        payload={
            "status": status.value,
            "result_excerpt": (task.result_text or "")[:160],
            "error_excerpt": (task.error_text or "")[:160],
            "duration_ms": task.duration_ms,
            "attempts": task.attempt_count
        }
    )

# ======================================================================================
# END OF FILE
# ======================================================================================
