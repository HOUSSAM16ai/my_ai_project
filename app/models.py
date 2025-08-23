# app/models.py
# ======================================================================================
# ==          COGNIFORGE AKASHIC GENOME v9.0 – UNIVERSAL COMPATIBILITY SCHEMA         ==
# ======================================================================================
# هذا هو الدستور البنيوي النهائي والمحصّن.
# ميزة v9.0 الحاسمة:
#   - Universal Translator (JSONB_or_JSON): يقدم طبقة تجريد تسمح باستخدام نوع
#     بيانات JSONB عالي الأداء في PostgreSQL (الإنتاج) مع التراجع بأمان إلى
#     نوع JSON العام في SQLite (الاختبارات)، مما يحل مشكلة UnsupportedCompilationError.
#
# هذا يسمح لنا بالاستفادة من أفضل ما في العالمين: سرعة اختبارات SQLite وقوة
# PostgreSQL في الإنتاج، دون الحاجة إلى تغيير الكود.
#
# بعد الاستبدال:
#   flask db migrate -m "Implement universal JSON type and finalize hybrid schema"
#   flask db upgrade
# ======================================================================================

from __future__ import annotations

import enum
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List

from flask_login import UserMixin
from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    Index,
    text,
    func,
    event,
    TypeDecorator,
    JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# ======================================================================================
# Universal Translator for JSON Types (THE CRITICAL FIX)
# ======================================================================================

class JSONB_or_JSON(TypeDecorator):
    """
    Acts as JSONB for PostgreSQL, falls back to generic JSON for all other databases.
    This allows us to use high-performance JSONB in production (Supabase/PostgreSQL)
    and still run high-speed tests with dialect-agnostic backends like SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

# ======================================================================================
# Utilities & Enums
# ======================================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

# --- All Enums from previous advanced versions ---
class MessageRole(enum.Enum): USER="user"; ASSISTANT="assistant"; TOOL="tool"; SYSTEM="system"
class MessageRating(enum.Enum): GOOD="good"; BAD="bad"; NEUTRAL="neutral"
class MissionStatus(enum.Enum): PENDING="PENDING"; PLANNING="PLANNING"; RUNNING="RUNNING"; ADAPTING="ADAPTING"; SUCCESS="SUCCESS"; FAILED="FAILED"; CANCELED="CANCELED"
class TaskStatus(enum.Enum): PENDING="PENDING"; RUNNING="RUNNING"; SUCCESS="SUCCESS"; FAILED="FAILED"; SKIPPED="SKIPPED"
class TaskType(enum.Enum): TOOL="TOOL"; REASON="REASON"; PLAN="PLAN"; CRITIC="CRITIC"; SUMMARIZE="SUMMARIZE"
class MissionEventType(enum.Enum): CREATED="CREATED"; STATUS_CHANGE="STATUS_CHANGE"; TASK_ADDED="TASK_ADDED"; TASK_UPDATED="TASK_UPDATED"; REPLAN="REPLAN"; ADAPT_START="ADAPT_START"; ADAPT_COMPLETE="ADAPT_COMPLETE"; FINALIZED="FINALIZED"; CANCELED="CANCELED"; FAILURE="FAILURE"

# ======================================================================================
# Mixins
# ======================================================================================

class Timestamped:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), default=utc_now, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), default=utc_now, onupdate=utc_now, index=True)

# ======================================================================================
# Core Entities (User, Educational Core, Conversational Memory)
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
    submissions   = db.relationship("Submission", backref="student", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str): self.password_hash = generate_password_hash(password)
    def check_password(self, password: str) -> bool: return bool(self.password_hash) and check_password_hash(self.password_hash, password)

# --- EDUCATIONAL CORE ---

class Subject(Timestamped, db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    lessons = db.relationship('Lesson', backref='subject', lazy='dynamic', cascade="all, delete-orphan")

class Lesson(Timestamped, db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False, index=True)
    exercises = db.relationship('Exercise', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    
class Exercise(Timestamped, db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    correct_answer_data = db.Column(JSONB_or_JSON, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete="CASCADE"), nullable=False, index=True)
    submissions = db.relationship('Submission', backref='exercise', lazy='dynamic', cascade="all, delete-orphan")

class Submission(Timestamped, db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    student_answer_data = db.Column(JSONB_or_JSON, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, index=True)
    feedback = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id', ondelete="CASCADE"), nullable=False, index=True)

# --- CONVERSATIONAL & STRATEGIC MEMORY ---

class Conversation(Timestamped, db.Model):
    __tablename__ = "conversations"
    id       = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    messages = db.relationship("Message", backref="conversation", lazy="dynamic", cascade="all, delete-orphan", order_by="Message.id")
    meta     = db.Column(JSONB_or_JSON, nullable=True)

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
    meta            = db.Column(JSONB_or_JSON, nullable=True)
    content_hash    = db.Column(db.String(64), nullable=True, index=True)
    __table_args__ = (CheckConstraint("length(content) > 0", name="ck_message_nonempty"),)

@event.listens_for(Message, "before_insert")
def _auto_hash_before_insert(mapper, connection, target: Message):
    if not target.content_hash:
        target.content_hash = hash_content(target.content)

class Mission(Timestamped, db.Model):
    __tablename__ = "missions"
    id            = db.Column(db.Integer, primary_key=True)
    objective     = db.Column(db.Text, nullable=False)
    status        = db.Column(SAEnum(MissionStatus, native_enum=False, length=20), nullable=False, default=MissionStatus.PENDING.value, index=True)
    initiator_id  = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_version  = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    plan_json     = db.Column(JSONB_or_JSON, nullable=True)
    last_adapted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    result_text   = db.Column(db.Text, nullable=True)
    result_meta   = db.Column(JSONB_or_JSON, nullable=True)
    telemetry     = db.Column(JSONB_or_JSON, nullable=True)
    locked        = db.Column(db.Boolean, nullable=False, default=False, server_default=text("false"), index=True)
    tasks_count   = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    tasks_success = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    tasks_failed  = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    tasks = db.relationship("Task", backref="mission", lazy="dynamic", cascade="all, delete-orphan", order_by="Task.sequence_id")
    events = db.relationship("MissionEvent", backref="mission", lazy="dynamic", cascade="all, delete-orphan", order_by="MissionEvent.id")

class Task(Timestamped, db.Model):
    __tablename__ = "tasks"
    id          = db.Column(db.Integer, primary_key=True)
    mission_id  = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_id = db.Column(db.Integer, nullable=False)
    step_type   = db.Column(SAEnum(TaskType, native_enum=False, length=15), nullable=False, default=TaskType.TOOL.value, index=True)
    description = db.Column(db.Text, nullable=False)
    tool_name   = db.Column(db.String(255), nullable=True, index=True)
    tool_args   = db.Column(JSONB_or_JSON, nullable=True)
    status      = db.Column(SAEnum(TaskStatus, native_enum=False, length=15), nullable=False, default=TaskStatus.PENDING.value, index=True)
    result_text = db.Column(db.Text, nullable=True)
    result_meta = db.Column(JSONB_or_JSON, nullable=True)
    elapsed_ms  = db.Column(db.Float, nullable=True)
    attempts    = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    cost_usd    = db.Column(db.Numeric(12, 6), nullable=True)
    __table_args__ = (db.UniqueConstraint("mission_id", "sequence_id", name="uq_task_mission_sequence"), CheckConstraint("sequence_id > 0", name="ck_task_sequence_positive"))

class MissionEvent(Timestamped, db.Model):
    __tablename__ = "mission_events"
    id          = db.Column(db.Integer, primary_key=True)
    mission_id  = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type  = db.Column(SAEnum(MissionEventType, native_enum=False, length=30), nullable=False, index=True)
    payload     = db.Column(JSONB_or_JSON, nullable=True)
    note        = db.Column(db.String(300), nullable=True)