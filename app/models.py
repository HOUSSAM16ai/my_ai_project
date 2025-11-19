# app/models.py
"""
New Unified Domain Models using SQLModel.
"""
from __future__ import annotations
import enum
from datetime import datetime, UTC
from typing import List, Optional, Any
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from sqlalchemy import String, Text, DateTime, func, Index
from sqlalchemy.dialects.postgresql import JSONB

# ======================================================================================
# UTILITIES & TYPES
# ======================================================================================

def utc_now() -> datetime:
    return datetime.now(UTC)

# Use SA's JSON type for the Column definition
Json = JSON()

# ======================================================================================
# ENUMS
# ======================================================================================

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

# ======================================================================================
# SQLModel DEFINITIONS
# ======================================================================================

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

class AdminConversation(SQLModel, table=True):
    __tablename__ = "admin_conversations"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)
    conversation_type: str = Field(default="general", max_length=50, index=True)

    context_snapshot: Optional[Any] = Field(default=None, sa_column=Column(Json))
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(Json))

    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    user: User = Relationship(back_populates="admin_conversations")
    messages: List["AdminMessage"] = Relationship(back_populates="conversation")

class AdminMessage(SQLModel, table=True):
    __tablename__ = "admin_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="admin_conversations.id", index=True)
    role: MessageRole
    content: str = Field(sa_column=Column(Text))

    tokens_used: Optional[int] = Field(default=None)
    model_used: Optional[str] = Field(default=None, max_length=100, index=True)

    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    conversation: AdminConversation = Relationship(back_populates="messages")

# NOTE: Other models (Mission, Task, etc.) are omitted for now but would be migrated
# in the same way in a full implementation.
