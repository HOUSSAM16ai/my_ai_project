# app/services/developer_portal/domain/models.py
"""
Developer Portal Domain Models
==============================
Pure business entities and enumerations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SDKLanguage(Enum):
    """Supported SDK languages"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUBY = "ruby"
    JAVA = "java"
    PHP = "php"
    CSHARP = "csharp"


class TicketStatus(Enum):
    """Support ticket status"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(Enum):
    """Support ticket priority"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class APIKeyStatus(Enum):
    """API key status"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class APIKey:
    """API key for developers"""

    key_id: str
    key_value: str
    name: str
    developer_id: str
    status: APIKeyStatus
    created_at: datetime
    scopes: list[str] = field(default_factory=list)
    allowed_ips: list[str] = field(default_factory=list)
    total_requests: int = 0
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


@dataclass
class SupportTicket:
    """Developer support ticket"""

    ticket_id: str
    developer_id: str
    subject: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    category: str = "general"
    assigned_to: str | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SDKPackage:
    """Generated SDK package"""

    sdk_id: str
    language: SDKLanguage
    version: str
    api_version: str
    generated_at: datetime
    download_url: str
    checksum: str
    size_bytes: int
    downloads: int = 0
    documentation_url: str | None = None


@dataclass
class CodeExample:
    """Code example for API documentation"""

    example_id: str
    title: str
    description: str
    language: SDKLanguage
    code: str
    endpoint: str
    category: str
    created_at: datetime
    tags: list[str] = field(default_factory=list)


__all__ = [
    "SDKLanguage",
    "TicketStatus",
    "TicketPriority",
    "APIKeyStatus",
    "APIKey",
    "SupportTicket",
    "SDKPackage",
    "CodeExample",
]
