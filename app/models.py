# app/models.py
# ======================================================================================
# ==        COGNIFORGE AKASHIC GENOME v10.1 – GRAND BLUEPRINT WITH HELPERS            ==
# ======================================================================================
# هذا هو الدستور البنيوي النهائي الذي يجسد "المخطط الأعظم" (The Grand Blueprint).
#
# ميزات v10.1 الحاسمة:
#   - Integrated Helper Functions: إضافة دوال `log_mission_event`, `finalize_task`, etc.
#     مباشرة في هذا الملف. هذا يحل `ImportError` في الخدمات ويجعل النماذج
#     مكتفية ذاتيًا أكثر.
#   - Full Educational Core: إعادة دمج `Exercise` و `Submission` بشكل كامل.
#
# بعد الاستبدال:
#   flask db migrate -m "Finalize Grand Blueprint schema with integrated helpers"
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
    JSON,
    ForeignKey
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# ======================================================================================
# Universal Translator & Utilities
# ======================================================================================

class JSONB_or_JSON(TypeDecorator):
    impl = JSON
    cache_ok = True
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSONB()) if dialect.name == 'postgresql' else dialect.type_descriptor(JSON())

def utc_now() -> datetime: return datetime.now(timezone.utc)
def hash_content(content: str) -> str: return hashlib.sha256(content.encode("utf-8")).hexdigest()

@login_manager.user_loader
def load_user(user_id: str): return db.session.get(User, int(user_id))

# --- Enums for Type Safety ---
class MessageRole(enum.Enum): USER="user"; ASSISTANT="assistant"; TOOL="tool"; SYSTEM="system"
class MissionStatus(enum.Enum): PENDING="PENDING"; PLANNING="PLANNING"; RUNNING="RUNNING"; ADAPTING="ADAPTING"; SUCCESS="SUCCESS"; FAILED="FAILED"; CANCELED="CANCELED"
class TaskStatus(enum.Enum): PENDING="PENDING"; RUNNING="RUNNING"; SUCCESS="SUCCESS"; FAILED="FAILED"; SKIPPED="SKIPPED"
class PlanStatus(enum.Enum): CANDIDATE="CANDIDATE"; ACTIVE="ACTIVE"; SUPERSEDED="SUPERSEDED"; FAILED="FAILED"
class MissionEventType(enum.Enum): CREATED="CREATED"; STATUS_CHANGE="STATUS_CHANGE"; PLAN_SELECTED="PLAN_SELECTED"; TASK_STATUS_CHANGE="TASK_STATUS_CHANGE"; REPLAN_TRIGGERED="REPLAN_TRIGGERED"; FINALIZED="FINALIZED"

# ======================================================================================
# Mixins & Association Tables
# ======================================================================================

class Timestamped:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=utc_now)

task_dependencies = db.Table('task_dependencies',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete="CASCADE"), primary_key=True),
    db.Column('depends_on_task_id', db.Integer, db.ForeignKey('tasks.id', ondelete="CASCADE"), primary_key=True)
)

# ======================================================================================
# Core Entities (User, Educational, and Agent Memory)
# ======================================================================================

class User(UserMixin, Timestamped, db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(150), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin      = db.Column(db.Boolean, nullable=False, default=False, server_default=text("false"))
    
    missions      = relationship("Mission", backref="initiator", cascade="all, delete-orphan")
    submissions   = relationship("Submission", backref="student", cascade="all, delete-orphan")

    def set_password(self, password: str): self.password_hash = generate_password_hash(password)
    def check_password(self, password: str) -> bool: return bool(self.password_hash) and check_password_hash(self.password_hash, password)

# --- Educational Core ---
class Subject(Timestamped, db.Model): __tablename__ = 'subjects'; id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(150), unique=True, nullable=False); lessons=relationship('Lesson', backref='subject', cascade="all, delete-orphan")
class Lesson(Timestamped, db.Model): __tablename__ = 'lessons'; id=db.Column(db.Integer, primary_key=True); title=db.Column(db.String(250)); content=db.Column(db.Text); subject_id=db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete="CASCADE"), index=True); exercises=relationship('Exercise', backref='lesson', cascade="all, delete-orphan")
class Exercise(Timestamped, db.Model): __tablename__ = 'exercises'; id=db.Column(db.Integer, primary_key=True); question=db.Column(db.Text); correct_answer_data=db.Column(JSONB_or_JSON); lesson_id=db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete="CASCADE"), index=True); submissions=relationship('Submission', backref='exercise', cascade="all, delete-orphan")
class Submission(Timestamped, db.Model): __tablename__ = 'submissions'; id=db.Column(db.Integer, primary_key=True); student_answer_data=db.Column(JSONB_or_JSON); is_correct=db.Column(db.Boolean); feedback=db.Column(db.Text); user_id=db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), index=True); exercise_id=db.Column(db.Integer, db.ForeignKey('exercises.id', ondelete="CASCADE"), index=True)

# --- Agent Memory ---
class Mission(Timestamped, db.Model):
    __tablename__ = "missions"
    id            = db.Column(db.Integer, primary_key=True)
    objective     = db.Column(db.Text, nullable=False)
    status        = db.Column(SAEnum(MissionStatus, native_enum=False), default=MissionStatus.PENDING, index=True)
    initiator_id  = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    active_plan_id = db.Column(db.Integer, db.ForeignKey("mission_plans.id"), nullable=True)
    locked        = db.Column(db.Boolean, default=False, server_default=text("false"))
    result_summary = db.Column(db.Text, nullable=True)
    total_cost_usd = db.Column(db.Numeric(12, 6), nullable=True)
    adaptive_cycles = db.Column(db.Integer, default=0)
    
    plans         = relationship("MissionPlan", backref="mission", cascade="all, delete-orphan", order_by="MissionPlan.version.desc()")
    tasks         = relationship("Task", backref="mission", cascade="all, delete-orphan")
    events        = relationship("MissionEvent", backref="mission", cascade="all, delete-orphan", order_by="MissionEvent.id")
    active_plan   = relationship("MissionPlan", foreign_keys=[active_plan_id])

class MissionPlan(Timestamped, db.Model):
    __tablename__ = "mission_plans"
    id           = db.Column(db.Integer, primary_key=True)
    mission_id   = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    version      = db.Column(db.Integer, nullable=False, default=1)
    planner_name = db.Column(db.String(100))
    plan_json    = db.Column(JSONB_or_JSON, nullable=False)
    score        = db.Column(db.Float, nullable=True)
    status       = db.Column(SAEnum(PlanStatus, native_enum=False), default=PlanStatus.CANDIDATE)
    __table_args__ = (db.UniqueConstraint("mission_id", "version", name="uq_mission_plan_version"),)

class Task(Timestamped, db.Model):
    __tablename__ = "tasks"
    id          = db.Column(db.Integer, primary_key=True)
    mission_id  = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    plan_version = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    tool_name   = db.Column(db.String(255), nullable=True, index=True)
    tool_args   = db.Column(JSONB_or_JSON, nullable=True)
    status      = db.Column(SAEnum(TaskStatus, native_enum=False), default=TaskStatus.PENDING, index=True)
    result      = db.Column(JSONB_or_JSON, nullable=True)
    attempts    = db.Column(db.Integer, default=0)
    cost_usd    = db.Column(db.Numeric(12, 6), nullable=True)
    
    dependencies = relationship("Task", secondary=task_dependencies, primaryjoin=(id == task_dependencies.c.task_id), secondaryjoin=(id == task_dependencies.c.depends_on_task_id), backref=backref("dependents"))

class MissionEvent(Timestamped, db.Model):
    __tablename__ = "mission_events"
    id          = db.Column(db.Integer, primary_key=True)
    mission_id  = db.Column(db.Integer, db.ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    task_id     = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True, index=True)
    event_type  = db.Column(SAEnum(MissionEventType, native_enum=False), index=True)
    payload     = db.Column(JSONB_or_JSON, nullable=True)
    note        = db.Column(db.String(500))

# ======================================================================================
# Helper Builders (The Akashic Scribes)
# ======================================================================================

def log_mission_event(
    mission: Mission,
    event_type: MissionEventType,
    *,
    task: Optional[Task] = None,
    payload: Optional[Dict[str, Any]] = None,
    note: Optional[str] = None
) -> MissionEvent:
    """Creates and logs a new MissionEvent, adding it to the session."""
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
    *,
    status: TaskStatus,
    result: Optional[Dict[str, Any]] = None
) -> Task:
    """Finalizes a task by setting its terminal status and results."""
    if status not in {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED}:
        raise ValueError("finalize_task expects a terminal status.")
    
    task.status = status
    task.result = result
    task.attempts = (task.attempts or 0) + 1

    log_mission_event(
        task.mission,
        MissionEventType.TASK_STATUS_CHANGE,
        task=task,
        payload={"status": status.value, "result_ok": (result or {}).get("ok")},
        note=f"Task {task.id} finalized with status {status.value}."
    )
    return task