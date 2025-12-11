# app/services/disaster_recovery/application/incident_manager.py
import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from app.services.disaster_recovery.domain.models import (
    EscalationPolicy,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    NotificationChannel,
    OnCallRole,
    OnCallSchedule,
    PostIncidentReview,
)
from app.services.disaster_recovery.infrastructure.repositories import InMemoryIncidentRepository


class IncidentManager:
    """Application service for Incident Management logic"""

    def __init__(self, repository: InMemoryIncidentRepository):
        self.repository = repository
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default escalation policies"""
        # SEV1 Escalation Policy
        sev1_policy = EscalationPolicy(
            policy_id="esc_sev1",
            name="SEV1 Critical Escalation",
            severity=IncidentSeverity.SEV1,
            escalation_levels=[
                {
                    "level": 1,
                    "timeout_minutes": 5,
                    "roles": [OnCallRole.PRIMARY],
                    "description": "Primary on-call engineer",
                },
                {
                    "level": 2,
                    "timeout_minutes": 10,
                    "roles": [OnCallRole.SECONDARY, OnCallRole.INCIDENT_COMMANDER],
                    "description": "Secondary engineer and incident commander",
                },
                {
                    "level": 3,
                    "timeout_minutes": 15,
                    "roles": [OnCallRole.ESCALATION, OnCallRole.TECHNICAL_LEAD],
                    "description": "Engineering leadership",
                },
            ],
            notification_channels=[
                NotificationChannel.PAGERDUTY,
                NotificationChannel.SMS,
                NotificationChannel.PHONE_CALL,
                NotificationChannel.SLACK,
            ],
        )
        self.repository.save_policy(sev1_policy)

        # SEV2 Escalation Policy
        sev2_policy = EscalationPolicy(
            policy_id="esc_sev2",
            name="SEV2 High Priority Escalation",
            severity=IncidentSeverity.SEV2,
            escalation_levels=[
                {
                    "level": 1,
                    "timeout_minutes": 10,
                    "roles": [OnCallRole.PRIMARY],
                    "description": "Primary on-call engineer",
                },
                {
                    "level": 2,
                    "timeout_minutes": 20,
                    "roles": [OnCallRole.SECONDARY],
                    "description": "Secondary engineer",
                },
            ],
            notification_channels=[NotificationChannel.PAGERDUTY, NotificationChannel.SLACK],
        )
        self.repository.save_policy(sev2_policy)

    def create_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        detected_by: str,
        affected_services: list[str],
    ) -> str:
        """Create a new incident"""
        incident_id = hashlib.sha256(f"{title}{datetime.now(UTC)}".encode()).hexdigest()[:16]

        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.DETECTED,
            detected_at=datetime.now(UTC),
            affected_services=affected_services,
        )

        # Add to timeline
        incident.timeline.append(
            {
                "timestamp": incident.detected_at.isoformat(),
                "event": "incident_detected",
                "by": detected_by,
                "description": f"Incident detected: {description}",
            }
        )

        self.repository.save_incident(incident)

        # Trigger escalation
        self._trigger_escalation(incident)

        logging.error(f"INCIDENT CREATED [{severity.value.upper()}]: {title} ({incident_id})")

        return incident_id

    def update_incident_status(
        self,
        incident_id: str,
        new_status: IncidentStatus,
        updated_by: str,
        notes: str | None = None,
    ) -> bool:
        """Update incident status"""
        incident = self.repository.get_incident(incident_id)
        if not incident:
            return False

        old_status = incident.status
        incident.status = new_status

        # Update timestamps
        now = datetime.now(UTC)
        if new_status == IncidentStatus.ACKNOWLEDGED:
            incident.acknowledged_at = now
        elif new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = now
        elif new_status == IncidentStatus.CLOSED:
            incident.closed_at = now

        # Add to timeline
        incident.timeline.append(
            {
                "timestamp": now.isoformat(),
                "event": "status_changed",
                "by": updated_by,
                "from": old_status.value,
                "to": new_status.value,
                "notes": notes,
            }
        )

        self.repository.save_incident(incident)

        logging.info(f"Incident {incident_id} status: {old_status.value} -> {new_status.value}")

        return True

    def assign_incident(self, incident_id: str, assigned_to: str, assigned_by: str) -> bool:
        """Assign incident to engineer"""
        incident = self.repository.get_incident(incident_id)
        if not incident:
            return False

        incident.assigned_to = assigned_to

        incident.timeline.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "assigned",
                "by": assigned_by,
                "to": assigned_to,
            }
        )
        self.repository.save_incident(incident)
        return True

    def _trigger_escalation(self, incident: Incident):
        """Trigger incident escalation based on severity"""
        policy_key = f"{incident.severity.value}_policy"
        policy = self.repository.get_policy(policy_key)

        if not policy:
            logging.warning(f"No escalation policy for {incident.severity.value}")
            return

        # Log escalation
        logging.info(
            f"Escalation triggered for incident {incident.incident_id} using policy: {policy.name}"
        )

        # In production, this would:
        # - Send notifications through configured channels
        # - Page on-call engineers
        # - Start escalation timer

        for level in policy.escalation_levels:
            logging.info(
                f"Escalation Level {level['level']}: {level['description']} "
                f"(timeout: {level['timeout_minutes']} minutes)"
            )

    def add_on_call_schedule(self, schedule: OnCallSchedule):
        """Add an on-call schedule"""
        self.repository.add_schedule(schedule)

    def get_current_on_call(self, role: OnCallRole) -> OnCallSchedule | None:
        """Get current on-call engineer for a role"""
        now = datetime.now(UTC)
        schedules = self.repository.get_schedules()

        for schedule in schedules:
            if (
                schedule.role == role
                and schedule.is_active
                and schedule.shift_start <= now <= schedule.shift_end
            ):
                return schedule

        return None

    def create_post_incident_review(
        self,
        incident_id: str,
        conducted_by: str,
        attendees: list[str],
        what_happened: str,
        what_went_well: list[str],
        what_could_improve: list[str],
        action_items: list[dict[str, Any]],
    ) -> str:
        """Create post-incident review"""
        pir_id = hashlib.sha256(f"{incident_id}{datetime.now(UTC)}".encode()).hexdigest()[:16]

        pir = PostIncidentReview(
            pir_id=pir_id,
            incident_id=incident_id,
            conducted_at=datetime.now(UTC),
            attendees=attendees,
            what_happened=what_happened,
            what_went_well=what_went_well,
            what_could_improve=what_could_improve,
            action_items=action_items,
            lessons_learned=[],
        )

        self.repository.save_pir(pir)
        logging.info(f"Post-incident review created: {pir_id}")

        return pir_id

    def get_incident_metrics(self) -> dict[str, Any]:
        """Get incident metrics"""
        incidents = self.repository.get_all_incidents()
        pirs = self.repository.get_all_pirs()

        total = len(incidents)
        by_severity: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for incident in incidents.values():
            sev = incident.severity.value
            stat = incident.status.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_status[stat] = by_status.get(stat, 0) + 1

        # Calculate MTTR (Mean Time To Resolution)
        resolved_incidents = [i for i in incidents.values() if i.resolved_at is not None]

        mttr_minutes = 0.0
        if resolved_incidents:
            total_resolution_time = sum(
                (i.resolved_at - i.detected_at).total_seconds() / 60
                for i in resolved_incidents  # type: ignore
            )
            mttr_minutes = total_resolution_time / len(resolved_incidents)

        return {
            "total_incidents": total,
            "by_severity": by_severity,
            "by_status": by_status,
            "mttr_minutes": mttr_minutes,
            "total_pirs": len(pirs),
        }
