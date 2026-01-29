from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from app.core.domain.common import utc_now

if TYPE_CHECKING:
    from app.core.domain.user import User


class WriterIntent(Enum):
    GENERAL_INQUIRY = auto()
    SOLUTION_REQUEST = auto()
    DIAGNOSIS_REQUEST = auto()
    QUESTION_ONLY_REQUEST = auto()


@dataclass
class StudentProfile:
    level: str  # Beginner, Average, Advanced


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AdminConversation(SQLModel, table=True):
    __tablename__ = "admin_conversations"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    user: User = Relationship(
        sa_relationship=relationship(
            "app.core.domain.user.User", back_populates="admin_conversations"
        )
    )
    messages: list[AdminMessage] = Relationship(
        sa_relationship=relationship(
            "AdminMessage", back_populates="conversation", cascade="all, delete-orphan"
        )
    )


class AdminMessage(SQLModel, table=True):
    __tablename__ = "admin_messages"

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="admin_conversations.id", index=True)
    role: MessageRole
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    conversation: AdminConversation = Relationship(
        sa_relationship=relationship("AdminConversation", back_populates="messages")
    )


class CustomerConversation(SQLModel, table=True):
    __tablename__ = "customer_conversations"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    user: User = Relationship(
        sa_relationship=relationship(
            "app.core.domain.user.User", back_populates="customer_conversations"
        )
    )
    messages: list[CustomerMessage] = Relationship(
        sa_relationship=relationship(
            "CustomerMessage", back_populates="conversation", cascade="all, delete-orphan"
        )
    )


class CustomerMessage(SQLModel, table=True):
    __tablename__ = "customer_messages"

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="customer_conversations.id", index=True)
    role: MessageRole
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    conversation: CustomerConversation = Relationship(
        sa_relationship=relationship("CustomerConversation", back_populates="messages")
    )
