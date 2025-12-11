# app/services/disaster_recovery/domain/models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IncidentSeverity(Enum):
    """Incident severity levels"""

    SEV1 = "sev1"  # Critical - Complete outage
    SEV2 = "sev2"  # High - Major functionality impaired
    SEV3 = "sev3"  # Medium - Minor functionality impaired
    SEV4 = "sev4"  # Low - Minimal impact


class IncidentStatus(Enum):
    """Incident lifecycle status"""

    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    CLOSED = "closed"


class OnCallRole(Enum):
    """On-call team roles"""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    ESCALATION = "escalation"
    INCIDENT_COMMANDER = "incident_commander"
    COMMUNICATIONS_LEAD = "communications_lead"
    TECHNICAL_LEAD = "technical_lead"


class RecoveryStrategy(Enum):
    """Disaster recovery strategies"""

    BACKUP_RESTORE = "backup_restore"
    FAILOVER = "failover"
    PILOT_LIGHT = "pilot_light"
    WARM_STANDBY = "warm_standby"
    HOT_STANDBY = "hot_standby"
    MULTI_SITE_ACTIVE = "multi_site_active"


class NotificationChannel(Enum):
    """Communication channels"""

    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    PHONE_CALL = "phone_call"


@dataclass
class Incident:
    """Incident record"""

    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    assigned_to: str | None = None
    affected_services: list[str] = field(default_factory=list)
    impact_description: str = ""
    root_cause: str | None = None
    resolution: str | None = None
    timeline: list[dict[str, Any]] = field(default_factory=list)
    notifications_sent: list[str] = field(default_factory=list)


@dataclass
class OnCallSchedule:
    """On-call rotation schedule"""

    schedule_id: str
    role: OnCallRole
    engineer_id: str
    engineer_name: str
    engineer_contact: dict[str, str]  # email, phone, slack, etc.
    shift_start: datetime
    shift_end: datetime
    is_active: bool = True


@dataclass
class EscalationPolicy:
    """Incident escalation policy"""

    policy_id: str
    name: str
    severity: IncidentSeverity
    escalation_levels: list[dict[str, Any]]  # Each level has timeout and contacts
    notification_channels: list[NotificationChannel]


@dataclass
class DisasterRecoveryPlan:
    """Disaster recovery plan"""

    plan_id: str
    name: str
    description: str
    strategy: RecoveryStrategy
    rto_minutes: int  # Recovery Time Objective in minutes
    rpo_minutes: int  # Recovery Point Objective in minutes
    runbook_url: str
    backup_locations: list[str]
    failover_regions: list[str]
    automated_steps: list[dict[str, Any]]
    manual_steps: list[str]
    last_tested: datetime | None = None
    test_frequency_days: int = 90


@dataclass
class BackupMetadata:
    """Backup metadata"""

    backup_id: str
    backup_type: str  # 'database', 'files', 'configuration', 'full'
    created_at: datetime
    size_bytes: int
    location: str
    retention_days: int
    encryption_enabled: bool
    verified: bool = False
    verification_date: datetime | None = None


@dataclass
class PostIncidentReview:
    """Post-Incident Review (PIR)"""

    pir_id: str
    incident_id: str
    conducted_at: datetime
    attendees: list[str]
    what_happened: str
    what_went_well: list[str]
    what_could_improve: list[str]
    action_items: list[dict[str, Any]]  # owner, description, deadline
    lessons_learned: list[str]
