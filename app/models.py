# ======================================================================================
#  COGNIFORGE DOMAIN MODELS  v14.1  • "SUPERHUMAN ADMIN CHAT + OVERMIND CORE"       #
# ======================================================================================
#  PURPOSE (الغرض):
#    نموذج نطاق (Domain Model) نقي ومركّز حصرياً على نظام Overmind:
#      - إزالة جميع الجداول القديمة غير المتعلقة بـ Overmind
#      - إزالة جداول التعليم القديمة (subjects, lessons, exercises, submissions)
#      - إزالة جداول الأدمن القديمة (admin_conversations, admin_messages)
#      - إزالة جدول task_dependencies المساعد (نستخدم depends_on_json بدلاً منه)
#
#  WHAT'S NEW in v14.1 (مقارنة بـ v14.0):
#    - 🔥 RESTORED: AdminConversation & AdminMessage models with SUPERHUMAN design
#    - 💪 ENHANCED: Advanced metadata, analytics, and indexing capabilities
#    - 🚀 SUPERIOR: Professional-grade conversation tracking surpassing tech giants
#    - 📊 METRICS: Token usage, latency, cost tracking, and conversation analytics
#    - 🔍 SEARCH: Content hashing, semantic embeddings support, and advanced indexing
#    - ⚡ PERFORMANCE: Optimized JSONB fields and composite indexes for blazing speed
#
#  CORE MODELS (النماذج الأساسية النقية):
#    ✅ User               - حسابات المستخدمين
#    ✅ AdminConversation  - محادثات الأدمن (نظام تسجيل خارق)
#    ✅ AdminMessage       - رسائل محادثات الأدمن (تتبع متقدم)
#    ✅ Mission            - المهام الرئيسية
#    ✅ MissionPlan        - خطط تنفيذ المهام
#    ✅ Task               - المهام الفرعية (باستخدام depends_on_json للتبعيات)
#    ✅ MissionEvent       - سجل أحداث المهام
#
#  REMOVED LEGACY SYSTEMS:
#    ❌ Education Kingdom (subjects, lessons, exercises, submissions)
#    ❌ task_dependencies helper table (replaced by depends_on_json)
#
#  SEMANTIC MISSION EVENTS (الإصدار التحليلي):
#      MISSION_UPDATED, RISK_SUMMARY, ARCHITECTURE_CLASSIFIED,
#      MISSION_COMPLETED, MISSION_FAILED, FINALIZED
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
#    - 0fe9bd3b1f3c : Genesis schema (with legacy tables)
#    - 0b5107e8283d : إضافة result_meta_json لِـ Task
#    - 20250902_event_type_text_and_index_super : تحويل event_type إلى TEXT
#    - c670e137ea84 : إضافة admin chat system (legacy)
#    - 20250103_purify_db : 🔥 PURIFICATION - إزالة جميع الجداول القديمة
#
#  NOTE (مهم):
#    - استخدام db.Enum(..., native_enum=False) يعني تخزين القيم كسلاسل (VARCHAR/TEXT)
#    - Task.depends_on_json يحتوي على قائمة task_keys للتبعيات (أبسط وأكثر مرونة)
#    - لا توجد علاقات many-to-many معقدة بعد الآن
#
#  TRANSACTION POLICY:
#    - هذا الملف لا يقوم بالـ commit. مسؤولية إدارة المعاملات تقع على الطبقات العليا
#      (الخدمات / orchestrator).
#
# ======================================================================================

from __future__ import annotations

# Version information for conftest.py version checking
__version__ = "14.1.0"

import enum
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from flask_login import UserMixin
from sqlalchemy import JSON as SAJSON
from sqlalchemy import (
    ForeignKey,
    Index,
    TypeDecorator,
    UniqueConstraint,
    event,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
            if dialect.name == "postgresql"
            else dialect.type_descriptor(SAJSON())
        )


def utc_now() -> datetime:
    return datetime.now(UTC)


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def coerce_datetime(value: Any) -> datetime | None:
    """
    تحويل مرن إلى datetime بتوقيت UTC.
    يقبل: datetime / int أو float (Epoch) / string (مجموعة صيغ) / وإلا None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, int | float):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
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
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC)
            except Exception:
                continue
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
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
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    ADAPTING = "ADAPTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY = "RETRY"
    SKIPPED = "SKIPPED"


class PlanStatus(enum.Enum):
    DRAFT = "DRAFT"
    VALID = "VALID"
    SUPERSEDED = "SUPERSEDED"
    FAILED = "FAILED"


class TaskType(enum.Enum):
    TOOL = "TOOL"
    SYSTEM = "SYSTEM"
    META = "META"
    VERIFICATION = "VERIFICATION"


class MissionEventType(enum.Enum):
    # Lifecycle & Planning
    CREATED = "CREATED"
    STATUS_CHANGE = "STATUS_CHANGE"
    PLAN_SELECTED = "PLAN_SELECTED"
    EXECUTION_STARTED = "EXECUTION_STARTED"

    # Task-level events
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"

    # Adaptation / Replanning
    REPLAN_TRIGGERED = "REPLAN_TRIGGERED"
    REPLAN_APPLIED = "REPLAN_APPLIED"

    # Generic / legacy
    MISSION_UPDATED = "MISSION_UPDATED"

    # Analytical
    RISK_SUMMARY = "RISK_SUMMARY"
    ARCHITECTURE_CLASSIFIED = "ARCHITECTURE_CLASSIFIED"

    # Terminal outcomes
    MISSION_COMPLETED = "MISSION_COMPLETED"
    MISSION_FAILED = "MISSION_FAILED"

    # Final closure marker
    FINALIZED = "FINALIZED"


# ======================================================================================
# MIXINS
# ======================================================================================


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=utc_now
    )


# ======================================================================================
# USER
# ======================================================================================


class User(UserMixin, Timestamped, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    email: Mapped[str] = mapped_column(db.String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(db.String(256))
    is_admin: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, default=False, server_default=text("false")
    )

    missions: Mapped[list[Mission]] = relationship(
        "Mission", back_populates="initiator", cascade="all, delete-orphan"
    )
    admin_conversations: Mapped[list[AdminConversation]] = relationship(
        "AdminConversation", cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash

        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ======================================================================================
# ADMIN CONVERSATION SYSTEM - SUPERHUMAN CHAT HISTORY
# ======================================================================================


class AdminConversation(Timestamped, db.Model):
    """
    محادثات الأدمن - نظام تسجيل خارق للمحادثات
    تصميم احترافي يتفوق على الشركات العملاقة مثل OpenAI و Microsoft و Google
    """

    __tablename__ = "admin_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(500), nullable=False)
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_type: Mapped[str] = mapped_column(
        db.String(50), nullable=False, default="general", index=True
    )

    # Enhanced metadata for superior intelligence
    deep_index_summary: Mapped[str | None] = mapped_column(db.Text)  # Project context snapshot
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB_or_JSON)  # Full contextual data
    tags: Mapped[list | None] = mapped_column(JSONB_or_JSON)  # Searchable tags

    # Analytics & metrics (enterprise-grade)
    total_messages: Mapped[int] = mapped_column(db.Integer, default=0, server_default=text("0"))
    total_tokens: Mapped[int] = mapped_column(db.Integer, default=0, server_default=text("0"))
    avg_response_time_ms: Mapped[float | None] = mapped_column(db.Float)

    # Status tracking
    is_archived: Mapped[bool] = mapped_column(
        db.Boolean, default=False, server_default=text("false"), index=True
    )
    last_message_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), index=True)

    # Relationships
    user: Mapped[User] = relationship("User", overlaps="admin_conversations")
    messages: Mapped[list[AdminMessage]] = relationship(
        "AdminMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AdminMessage.created_at",
    )

    __table_args__ = (
        Index("ix_admin_conv_user_type", "user_id", "conversation_type"),
        Index("ix_admin_conv_archived_updated", "is_archived", "updated_at"),
    )

    def __repr__(self):
        return f"<AdminConversation id={self.id} title={self.title[:30]!r}>"

    def update_stats(self):
        """Update conversation statistics"""
        self.total_messages = len(self.messages)
        self.total_tokens = sum(m.tokens_used or 0 for m in self.messages)

        response_times = [
            m.latency_ms for m in self.messages if m.latency_ms and m.role == "assistant"
        ]
        if response_times:
            self.avg_response_time_ms = sum(response_times) / len(response_times)

        if self.messages:
            # Ensure all datetimes are timezone-aware before comparison
            message_times = [coerce_datetime(m.created_at) for m in self.messages]
            message_times = [t for t in message_times if t is not None]
            if message_times:
                self.last_message_at = max(message_times)


class AdminMessage(Timestamped, db.Model):
    """
    رسائل محادثات الأدمن - تسجيل دقيق لكل رسالة
    نظام تتبع متقدم يحفظ كل التفاصيل مع metadata كاملة
    """

    __tablename__ = "admin_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("admin_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        db.String(20), nullable=False, index=True
    )  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(db.Text, nullable=False)

    # AI Model metrics (for professional tracking)
    tokens_used: Mapped[int | None] = mapped_column(db.Integer)
    model_used: Mapped[str | None] = mapped_column(db.String(100), index=True)
    latency_ms: Mapped[float | None] = mapped_column(db.Float)
    cost_usd: Mapped[float | None] = mapped_column(db.Numeric(12, 6))

    # Advanced metadata (JSONB for performance)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB_or_JSON
    )  # Custom data, analysis results, etc.

    # Content analytics
    content_hash: Mapped[str | None] = mapped_column(db.String(64), index=True)  # For deduplication
    embedding_vector: Mapped[list | None] = mapped_column(
        JSONB_or_JSON
    )  # For semantic search (future)

    # Relationship
    conversation: Mapped[AdminConversation] = relationship(
        "AdminConversation", back_populates="messages"
    )

    __table_args__ = (
        Index("ix_admin_msg_conv_role", "conversation_id", "role"),
        Index("ix_admin_msg_created", "created_at"),
    )

    def __repr__(self):
        preview = self.content[:50] if len(self.content) > 50 else self.content
        return f"<AdminMessage id={self.id} role={self.role} preview={preview!r}>"

    def compute_content_hash(self):
        """Compute SHA256 hash of content for deduplication"""
        if self.content:
            self.content_hash = hash_content(self.content)


# ======================================================================================
# PROMPT ENGINEERING SYSTEM - SUPERHUMAN EDITION
# ======================================================================================


class PromptTemplate(Timestamped, db.Model):
    """
    نموذج قوالب Prompt Engineering الخارقة (SUPERHUMAN PROMPT TEMPLATES)

    يخزن قوالب Meta-Prompt الديناميكية مع:
    - متغيرات المشروع (project variables)
    - أمثلة Few-Shot من سياق المشروع
    - إعدادات RAG للسياق
    - تتبع الأداء والنسخ
    """

    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(db.Text)

    # Template content with variables like {project_name}, {user_description}, etc.
    template_content: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Category: "code_generation", "documentation", "architecture", "testing", etc.
    category: Mapped[str] = mapped_column(db.String(100), index=True, default="general")

    # Few-shot examples from project (JSON array of examples)
    few_shot_examples: Mapped[list | None] = mapped_column(JSONB_or_JSON)

    # Configuration for RAG (max chunks, relevance threshold, etc.)
    rag_config: Mapped[dict | None] = mapped_column(JSONB_or_JSON)

    # Template variables definition
    variables: Mapped[list | None] = mapped_column(
        JSONB_or_JSON
    )  # List of variable names and descriptions

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(db.Integer, default=0, server_default=text("0"))
    success_rate: Mapped[float | None] = mapped_column(db.Float)  # User feedback based

    # Version control
    version: Mapped[int] = mapped_column(db.Integer, default=1, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, server_default=text("true"))

    # Creator
    created_by_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[User] = relationship("User")

    __table_args__ = (
        Index("ix_prompt_template_category_active", "category", "is_active"),
        Index("ix_prompt_template_usage", "usage_count"),
    )

    def __repr__(self):
        return f"<PromptTemplate id={self.id} name={self.name!r} category={self.category}>"


class GeneratedPrompt(Timestamped, db.Model):
    """
    سجل Prompts المولدة (GENERATED PROMPTS HISTORY)

    يحفظ كل prompt تم توليده للتتبع والتحليل والتحسين المستمر:
    - الوصف المدخل من المستخدم
    - القالب المستخدم
    - السياق المسترجع (RAG)
    - الـ Prompt النهائي المولد
    - تقييم المستخدم (feedback loop)
    """

    __tablename__ = "generated_prompts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Input from user
    user_description: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Template used
    template_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("prompt_templates.id", ondelete="SET NULL"), index=True
    )
    template: Mapped[PromptTemplate | None] = relationship("PromptTemplate")

    # Generated output
    generated_prompt: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Context used (from RAG)
    context_snippets: Mapped[list | None] = mapped_column(JSONB_or_JSON)

    # Metadata about generation process
    generation_metadata: Mapped[dict | None] = mapped_column(
        JSONB_or_JSON
    )  # tokens, latency, model, etc.

    # User feedback (RLHF style)
    rating: Mapped[int | None] = mapped_column(db.Integer)  # 1-5 stars
    feedback_text: Mapped[str | None] = mapped_column(db.Text)

    # Link to conversation if generated during chat
    conversation_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("admin_conversations.id", ondelete="SET NULL"), index=True
    )
    conversation: Mapped[AdminConversation | None] = relationship("AdminConversation")

    # Creator
    created_by_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[User] = relationship("User")

    # Content hash for deduplication
    content_hash: Mapped[str | None] = mapped_column(db.String(64), index=True)

    __table_args__ = (
        Index("ix_generated_prompt_template_rating", "template_id", "rating"),
        Index("ix_generated_prompt_created", "created_at"),
    )

    def __repr__(self):
        preview = (
            self.user_description[:50] if len(self.user_description) > 50 else self.user_description
        )
        return f"<GeneratedPrompt id={self.id} description={preview!r}>"

    def compute_content_hash(self):
        """Compute SHA256 hash of generated prompt for deduplication"""
        if self.generated_prompt:
            self.content_hash = hash_content(self.generated_prompt)


# ======================================================================================
# CORE: Mission / MissionPlan / Task / MissionEvent
# ======================================================================================


class Mission(Timestamped, db.Model):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    objective: Mapped[str] = mapped_column(db.Text, nullable=False)
    status: Mapped[MissionStatus] = mapped_column(
        db.Enum(MissionStatus, native_enum=False), default=MissionStatus.PENDING, index=True
    )
    initiator_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    active_plan_id: Mapped[int | None] = mapped_column(
        db.Integer, ForeignKey("mission_plans.id", use_alter=True), nullable=True
    )

    locked: Mapped[bool] = mapped_column(db.Boolean, default=False, server_default=text("false"))
    result_summary: Mapped[str | None] = mapped_column(db.Text)
    total_cost_usd = mapped_column(db.Numeric(12, 6))
    adaptive_cycles: Mapped[int] = mapped_column(db.Integer, default=0)

    initiator: Mapped[User] = relationship("User", back_populates="missions")

    plans: Mapped[list[MissionPlan]] = relationship(
        "MissionPlan",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="desc(MissionPlan.version)",
        foreign_keys="MissionPlan.mission_id",
        overlaps="active_plan,mission",
    )

    active_plan: Mapped[MissionPlan | None] = relationship(
        "MissionPlan",
        foreign_keys=[active_plan_id],
        post_update=True,
        uselist=False,
        overlaps="plans,mission",
    )

    tasks: Mapped[list[Task]] = relationship(
        "Task", back_populates="mission", cascade="all, delete-orphan"
    )
    events: Mapped[list[MissionEvent]] = relationship(
        "MissionEvent",
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionEvent.id",
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
        return (
            f"<Mission id={self.id} status={self.status.value} objective={self.objective[:30]!r}>"
        )


class MissionPlan(Timestamped, db.Model):
    __tablename__ = "mission_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    planner_name: Mapped[str | None] = mapped_column(db.String(120))
    status: Mapped[PlanStatus] = mapped_column(
        db.Enum(PlanStatus, native_enum=False), default=PlanStatus.VALID, index=True
    )
    score: Mapped[float | None] = mapped_column(db.Float)
    rationale: Mapped[str | None] = mapped_column(db.Text)
    raw_json: Mapped[dict] = mapped_column(JSONB_or_JSON)
    stats_json: Mapped[dict | None] = mapped_column(JSONB_or_JSON)
    warnings_json: Mapped[list | None] = mapped_column(JSONB_or_JSON)
    content_hash: Mapped[str | None] = mapped_column(db.String(128), index=True)

    mission: Mapped[Mission] = relationship(
        "Mission", back_populates="plans", foreign_keys=[mission_id], overlaps="active_plan,plans"
    )

    tasks: Mapped[list[Task]] = relationship(
        "Task", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("mission_id", "version", name="uq_mission_plan_version"),)

    def __repr__(self):
        return f"<MissionPlan id={self.id} v={self.version} planner={self.planner_name} score={self.score}>"


class Task(Timestamped, db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("mission_plans.id", ondelete="CASCADE"), index=True
    )

    task_key: Mapped[str] = mapped_column(db.String(120), index=True)
    description: Mapped[str | None] = mapped_column(db.Text)
    task_type: Mapped[TaskType] = mapped_column(
        db.Enum(TaskType, native_enum=False), default=TaskType.TOOL, index=True
    )

    tool_name: Mapped[str | None] = mapped_column(db.String(255), index=True)
    tool_args_json: Mapped[dict | None] = mapped_column(JSONB_or_JSON)
    depends_on_json: Mapped[list | None] = mapped_column(JSONB_or_JSON)

    priority: Mapped[int] = mapped_column(db.Integer, default=0)
    risk_level: Mapped[str | None] = mapped_column(db.String(20))
    criticality: Mapped[str | None] = mapped_column(db.String(20))

    status: Mapped[TaskStatus] = mapped_column(
        db.Enum(TaskStatus, native_enum=False), default=TaskStatus.PENDING, index=True
    )
    attempt_count: Mapped[int] = mapped_column(db.Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(db.Integer, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True))

    # Results & telemetry
    result_text: Mapped[str | None] = mapped_column(db.Text)
    error_text: Mapped[str | None] = mapped_column(db.Text)
    duration_ms: Mapped[int | None] = mapped_column(db.Integer)

    started_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True))

    result: Mapped[dict | None] = mapped_column(JSONB_or_JSON)  # Structured output
    result_meta_json: Mapped[dict | None] = mapped_column(JSONB_or_JSON)  # Free-form meta
    cost_usd = mapped_column(db.Numeric(12, 6))

    mission: Mapped[Mission] = relationship("Mission", back_populates="tasks")
    plan: Mapped[MissionPlan] = relationship(
        "MissionPlan", back_populates="tasks", overlaps="plans,active_plan,mission"
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
    def duration_seconds(self) -> float | None:
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

    def mark_finished(
        self, status: TaskStatus, result_text: str | None = None, error: str | None = None
    ):
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
    mission_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )
    event_type: Mapped[MissionEventType] = mapped_column(
        db.Enum(MissionEventType, native_enum=False), index=True
    )
    payload: Mapped[dict | None] = mapped_column(JSONB_or_JSON)
    note: Mapped[str | None] = mapped_column(db.String(500))

    mission: Mapped[Mission] = relationship("Mission", back_populates="events")
    task: Mapped[Task | None] = relationship("Task")

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


def update_mission_status(mission: Mission, new_status: MissionStatus, note: str | None = None):
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
            note=note,
        )
        db.session.add(evt)


def log_mission_event(
    mission: Mission,
    event_type: MissionEventType,
    *,
    task: Task | None = None,
    payload: dict[str, Any] | None = None,
    note: str | None = None,
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
        note=note,
    )
    db.session.add(evt)
    return evt


def finalize_task(
    task: Task,
    status: TaskStatus,
    *,
    result_text: str | None = None,
    error_text: str | None = None,
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

    event_type = (
        MissionEventType.TASK_COMPLETED
        if status == TaskStatus.SUCCESS
        else MissionEventType.TASK_FAILED
    )
    log_mission_event(
        task.mission,
        event_type,
        task=task,
        payload={
            "status": status.value,
            "result_excerpt": (task.result_text or "")[:160],
            "error_excerpt": (task.error_text or "")[:160],
            "duration_ms": task.duration_ms,
            "attempts": task.attempt_count,
        },
    )


# ======================================================================================
# END OF FILE
# ======================================================================================
