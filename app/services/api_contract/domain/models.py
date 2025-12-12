"""Domain models for API Contract service."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class APIVersion:
    """API version metadata."""

    version: str
    release_date: datetime
    status: str  # 'active', 'deprecated', 'sunset'
    deprecation_date: datetime | None = None
    sunset_date: datetime | None = None
    breaking_changes: list[str] = field(default_factory=list)
    changelog: str = ""


@dataclass
class ContractSchema:
    """API contract schema definition."""

    name: str
    version: str
    schema: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    hash: str = ""


@dataclass
class ContractValidationResult:
    """Result of contract validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class BreakingChange:
    """Breaking change detection result."""

    field_path: str
    change_type: str  # 'removed', 'type_changed', 'required_added'
    old_value: Any
    new_value: Any
    severity: str  # 'critical', 'major', 'minor'
