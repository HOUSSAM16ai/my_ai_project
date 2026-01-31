"""
خدمات التعلم التعاوني (Collaboration Services).
================================================

تتضمن:
- CollaborativeSession: جلسة تعلم جماعية
- SharedWorkspace: مساحة عمل مشتركة

تتكامل مع:
- Kagent: لتنسيق الوكلاء المساعدين
- WebSocket: للتواصل الحي (مخطط)
"""

from app.services.collaboration.session import (
    CollaborativeSession,
    MessageType,
    SessionMessage,
    SessionParticipant,
    create_session,
    get_session,
    list_active_sessions,
)
from app.services.collaboration.workspace import (
    SharedWorkspace,
    WorkspaceChange,
    get_or_create_workspace,
)

__all__ = [
    # Session
    "CollaborativeSession",
    "SessionMessage",
    "SessionParticipant",
    "MessageType",
    "create_session",
    "get_session",
    "list_active_sessions",
    # Workspace
    "SharedWorkspace",
    "WorkspaceChange",
    "get_or_create_workspace",
]
