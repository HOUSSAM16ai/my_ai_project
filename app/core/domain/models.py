"""
Database Models Facade.

This file now acts as a facade, re-exporting models from specific domain modules.
This maintains backward compatibility while we refactor towards Bounded Contexts.

Principles:
- Facade Pattern: Provides a unified interface to a set of interfaces in a subsystem.
- Backward Compatibility: Existing imports like `from app.core.domain.models import User` continue to work.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import SQLModel

# Re-export from domain sub-modules
from app.core.domain.common import (
    utc_now,
    CaseInsensitiveEnum,
    FlexibleEnum,
    JSONText,
)
from app.core.domain.user import (
    pwd_context,
    UserStatus,
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    RefreshToken,
    PasswordResetToken,
)
from app.core.domain.chat import (
    MessageRole,
    AdminConversation,
    AdminMessage,
    CustomerConversation,
    CustomerMessage,
)
from app.core.domain.mission import (
    MissionStatus,
    PlanStatus,
    TaskStatus,
    MissionEventType,
    Mission,
    MissionPlan,
    Task,
    MissionEvent,
    log_mission_event,
    update_mission_status,
)
from app.core.domain.audit import (
    AuditLog,
    PromptTemplate,
    GeneratedPrompt,
)

if TYPE_CHECKING:
    pass

# Rebuild models for forward refs across the split files
# This is crucial because SQLModel needs to resolve string forward references
# and since they are now in different files, we must ensure they "see" each other
# by having them imported here where the app might initialize.

try:
    SQLModel.model_rebuild()
except Exception:
    import traceback
    # traceback.print_exc()
    # It might fail if some models are not fully defined yet or circular deps logic
    # But usually model_rebuild is robust.
    pass
