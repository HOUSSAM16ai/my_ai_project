import threading
from app.services.disaster_recovery.application.incident_manager import IncidentManager
from app.services.disaster_recovery.application.recovery_manager import RecoveryManager
from app.services.disaster_recovery.domain.models import BackupMetadata, DisasterRecoveryPlan, EscalationPolicy, Incident, IncidentSeverity, IncidentStatus, NotificationChannel, OnCallRole, OnCallSchedule, PostIncidentReview, RecoveryStrategy
from app.services.disaster_recovery.infrastructure.repositories import InMemoryIncidentRepository, InMemoryRecoveryRepository
__all__ = ['BackupMetadata', 'DisasterRecoveryPlan',
    'DisasterRecoveryService', 'EscalationPolicy', 'Incident',
    'IncidentSeverity', 'IncidentStatus', 'NotificationChannel',
    'OnCallIncidentService', 'OnCallRole', 'OnCallSchedule',
    'PostIncidentReview', 'RecoveryStrategy',
    'get_disaster_recovery_service', 'get_oncall_incident_service']


class DisasterRecoveryService:
    """
    Facade for Disaster Recovery Service ensuring backward compatibility.
    Delegates to RecoveryManager.
    """

    def __init__(self):
        self.repository = InMemoryRecoveryRepository()
        self.manager = RecoveryManager(self.repository)

    @property
    def dr_plans(self):
        return self.repository.get_all_plans()

    @property
    def backups(self):
        return self.repository.get_all_backups()

    @property
    def recovery_history(self):
        return self.repository._recovery_history

    def register_backup(self, backup: BackupMetadata) ->bool:
        return self.manager.register_backup(backup)

    def verify_backup(self, backup_id: str) ->bool:
        return self.manager.verify_backup(backup_id)

    def initiate_failover(self, plan_id: str, initiated_by: str, reason: str):
        return self.manager.initiate_failover(plan_id, initiated_by, reason)

    def get_rto_rpo_status(self):
        return self.manager.get_rto_rpo_status()


class OnCallIncidentService:
    """
    Facade for On-Call Incident Service ensuring backward compatibility.
    Delegates to IncidentManager.
    """

    def __init__(self):
        self.repository = InMemoryIncidentRepository()
        self.manager = IncidentManager(self.repository)

    @property
    def incidents(self):
        return self.repository.get_all_incidents()

    @property
    def on_call_schedules(self):
        return self.repository.get_schedules()

    @property
    def post_incident_reviews(self):
        return self.repository.get_all_pirs()

    def create_incident(self, title, description, severity, detected_by,
        affected_services):
        return self.manager.create_incident(title, description, severity,
            detected_by, affected_services)

    def update_incident_status(self, incident_id, new_status, updated_by,
        notes=None):
        return self.manager.update_incident_status(incident_id, new_status,
            updated_by, notes)

    def assign_incident(self, incident_id, assigned_to, assigned_by):
        return self.manager.assign_incident(incident_id, assigned_to,
            assigned_by)

    def add_on_call_schedule(self, schedule):
        self.manager.add_on_call_schedule(schedule)

    def get_current_on_call(self, role):
        return self.manager.get_current_on_call(role)

    def create_post_incident_review(self, incident_id, conducted_by,
        attendees, what_happened, what_went_well, what_could_improve,
        action_items):
        return self.manager.create_post_incident_review(incident_id,
            conducted_by, attendees, what_happened, what_went_well,
            what_could_improve, action_items)

    def get_incident_metrics(self):
        return self.manager.get_incident_metrics()


_dr_service_instance: DisasterRecoveryService | None = None
_oncall_service_instance: OnCallIncidentService | None = None
_service_lock = threading.Lock()


def get_disaster_recovery_service() ->DisasterRecoveryService:
    global _dr_service_instance
    if _dr_service_instance is None:
        with _service_lock:
            if _dr_service_instance is None:
                _dr_service_instance = DisasterRecoveryService()
    return _dr_service_instance


def get_oncall_incident_service() ->OnCallIncidentService:
    global _oncall_service_instance
    if _oncall_service_instance is None:
        with _service_lock:
            if _oncall_service_instance is None:
                _oncall_service_instance = OnCallIncidentService()
    return _oncall_service_instance
