"""
Database Models Facade.

This file now acts as a facade, re-exporting models from specific domain modules.
This maintains backward compatibility while we refactor towards Bounded Contexts.

Principles:
- Facade Pattern: Provides a unified interface to a set of interfaces in a subsystem.
- Backward Compatibility: Existing imports like `from app.core.domain.models import User` continue to work.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from sqlmodel import SQLModel

from app.core.domain.audit import AuditLog, GeneratedPrompt, PromptTemplate
from app.core.domain.chat import (
    AdminConversation,
    AdminMessage,
    CustomerConversation,
    CustomerMessage,
    MessageRole,
)
from app.core.domain.common import CaseInsensitiveEnum, FlexibleEnum, JSONText, utc_now
from app.core.domain.mission import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    PlanStatus,
    Task,
    TaskStatus,
    log_mission_event,
    update_mission_status,
)
from app.core.domain.user import (
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    User,
    UserRole,
    UserStatus,
)
from app.security.passwords import pwd_context

if TYPE_CHECKING:
    pass

# Rebuild models for forward refs across the split files
# This is crucial because SQLModel needs to resolve string forward references
# and since they are now in different files, we must ensure they "see" each other
# by having them imported here where the app might initialize.

with suppress(Exception):
    # traceback.print_exc()
    # It might fail if some models are not fully defined yet or circular deps logic
    # But usually model_rebuild is robust.
    SQLModel.model_rebuild()

__all__ = [
    "AdminConversation",
    "AdminMessage",
    "AuditLog",
    "CaseInsensitiveEnum",
    "CustomerConversation",
    "CustomerMessage",
    "FlexibleEnum",
    "GeneratedPrompt",
    "JSONText",
    "MessageRole",
    "Mission",
    "MissionEvent",
    "MissionEventType",
    "MissionPlan",
    "MissionStatus",
    "PasswordResetToken",
    "Permission",
    "PlanStatus",
    "PromptTemplate",
    "log_mission_event",
    "pwd_context",
    "RefreshToken",
    "Role",
    "RolePermission",
    "Task",
    "TaskStatus",
    "update_mission_status",
    "User",
    "UserRole",
    "UserStatus",
    "utc_now",
]
