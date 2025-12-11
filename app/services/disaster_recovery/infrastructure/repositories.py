# app/services/disaster_recovery/infrastructure/repositories.py
import threading

from app.services.disaster_recovery.domain.models import (
    BackupMetadata,
    DisasterRecoveryPlan,
    EscalationPolicy,
    Incident,
    OnCallSchedule,
    PostIncidentReview,
)


class InMemoryRecoveryRepository:
    """In-memory repository for disaster recovery data"""

    def __init__(self):
        self._plans: dict[str, DisasterRecoveryPlan] = {}
        self._backups: dict[str, BackupMetadata] = {}
        self._recovery_history: list[dict] = []
        self._lock = threading.RLock()

    def get_plan(self, plan_id: str) -> DisasterRecoveryPlan | None:
        with self._lock:
            return self._plans.get(plan_id)

    def save_plan(self, plan: DisasterRecoveryPlan, key: str | None = None):
        """Save a plan, optionally specifying a lookup key different from plan_id"""
        with self._lock:
            lookup_key = key if key else plan.plan_id
            self._plans[lookup_key] = plan

    def get_all_plans(self) -> dict[str, DisasterRecoveryPlan]:
        with self._lock:
            return self._plans.copy()

    def get_backup(self, backup_id: str) -> BackupMetadata | None:
        with self._lock:
            return self._backups.get(backup_id)

    def save_backup(self, backup: BackupMetadata):
        with self._lock:
            self._backups[backup.backup_id] = backup

    def get_all_backups(self) -> dict[str, BackupMetadata]:
        with self._lock:
            return self._backups.copy()

    def add_history_event(self, event: dict):
        with self._lock:
            self._recovery_history.append(event)
            # Keep only last 1000 events
            if len(self._recovery_history) > 1000:
                self._recovery_history.pop(0)


class InMemoryIncidentRepository:
    """In-memory repository for incident data"""

    def __init__(self):
        self._incidents: dict[str, Incident] = {}
        self._schedules: list[OnCallSchedule] = []
        self._policies: dict[str, EscalationPolicy] = {}
        self._pirs: dict[str, PostIncidentReview] = {}
        self._lock = threading.RLock()

    def get_incident(self, incident_id: str) -> Incident | None:
        with self._lock:
            return self._incidents.get(incident_id)

    def save_incident(self, incident: Incident):
        with self._lock:
            self._incidents[incident.incident_id] = incident

    def get_all_incidents(self) -> dict[str, Incident]:
        with self._lock:
            return self._incidents.copy()

    def add_schedule(self, schedule: OnCallSchedule):
        with self._lock:
            self._schedules.append(schedule)

    def get_schedules(self) -> list[OnCallSchedule]:
        with self._lock:
            return list(self._schedules)

    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        with self._lock:
            return self._policies.get(policy_id)

    def save_policy(self, policy: EscalationPolicy):
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_pir(self, pir_id: str) -> PostIncidentReview | None:
        with self._lock:
            return self._pirs.get(pir_id)

    def save_pir(self, pir: PostIncidentReview):
        with self._lock:
            self._pirs[pir.pir_id] = pir

    def get_all_pirs(self) -> dict[str, PostIncidentReview]:
        with self._lock:
            return self._pirs.copy()
