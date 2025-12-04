from datetime import datetime, timedelta, UTC
import pytest
from app.services.api_disaster_recovery_service import (
    DisasterRecoveryService,
    OnCallIncidentService,
    RecoveryStrategy,
    IncidentSeverity,
    IncidentStatus,
    OnCallRole,
    BackupMetadata,
    OnCallSchedule,
    get_disaster_recovery_service,
    get_oncall_incident_service
)

class TestDisasterRecoveryService:
    """Test suite for DisasterRecoveryService"""

    @pytest.fixture
    def dr_service(self):
        # Reset the singleton for testing or create a fresh instance
        # Since the class methods don't support reset easily, we'll instantiate directly
        return DisasterRecoveryService()

    def test_default_plans_initialization(self, dr_service):
        """Test that default DR plans are initialized correctly"""
        assert "database_dr" in dr_service.dr_plans
        assert "api_dr" in dr_service.dr_plans

        db_plan = dr_service.dr_plans["database_dr"]
        assert db_plan.strategy == RecoveryStrategy.WARM_STANDBY
        assert db_plan.rto_minutes == 30

    def test_register_backup(self, dr_service):
        """Test registering a new backup"""
        backup = BackupMetadata(
            backup_id="bk_test_001",
            backup_type="database",
            created_at=datetime.now(UTC),
            size_bytes=1024 * 1024 * 100,  # 100MB
            location="s3://test-bucket/backup.sql",
            retention_days=30,
            encryption_enabled=True,
            verified=False
        )

        result = dr_service.register_backup(backup)
        assert result is True
        assert "bk_test_001" in dr_service.backups

    def test_verify_backup(self, dr_service):
        """Test verifying a backup"""
        backup = BackupMetadata(
            backup_id="bk_test_verify",
            backup_type="database",
            created_at=datetime.now(UTC),
            size_bytes=1000,
            location="s3://test",
            retention_days=30,
            encryption_enabled=True,
            verified=False
        )
        dr_service.register_backup(backup)

        # Verify existing backup
        assert dr_service.verify_backup("bk_test_verify") is True
        assert dr_service.backups["bk_test_verify"].verified is True
        assert dr_service.backups["bk_test_verify"].verification_date is not None

        # Verify non-existing backup
        assert dr_service.verify_backup("bk_missing") is False

    def test_initiate_failover_success(self, dr_service):
        """Test initiating a failover successfully"""
        result = dr_service.initiate_failover(
            plan_id="database_dr",
            initiated_by="admin_user",
            reason="Simulated failure"
        )

        assert result["success"] is True
        assert result["plan"] == "Database Disaster Recovery"
        assert len(dr_service.recovery_history) == 1
        assert dr_service.recovery_history[0]["status"] == "in_progress"

    def test_initiate_failover_failure(self, dr_service):
        """Test initiating a failover for a non-existent plan"""
        result = dr_service.initiate_failover(
            plan_id="non_existent_plan",
            initiated_by="admin_user",
            reason="Test"
        )

        assert result["success"] is False
        assert result["error"] == "DR plan not found"

    def test_get_rto_rpo_status(self, dr_service):
        """Test retrieving RTO/RPO status"""
        status = dr_service.get_rto_rpo_status()

        assert "disaster_recovery_plans" in status
        assert "database_dr" in status["disaster_recovery_plans"]
        assert "backup_summary" in status
        assert status["backup_summary"]["total_backups"] == 0

class TestOnCallIncidentService:
    """Test suite for OnCallIncidentService"""

    @pytest.fixture
    def incident_service(self):
        return OnCallIncidentService()

    def test_create_incident(self, incident_service):
        """Test creating a new incident"""
        incident_id = incident_service.create_incident(
            title="Test Incident",
            description="Something is broken",
            severity=IncidentSeverity.SEV1,
            detected_by="monitoring_system",
            affected_services=["api"]
        )

        assert incident_id in incident_service.incidents
        incident = incident_service.incidents[incident_id]
        assert incident.title == "Test Incident"
        assert incident.status == IncidentStatus.DETECTED
        assert len(incident.timeline) == 1

    def test_update_incident_status(self, incident_service):
        """Test updating incident status"""
        incident_id = incident_service.create_incident(
            title="Update Test",
            description="Testing update",
            severity=IncidentSeverity.SEV2,
            detected_by="user",
            affected_services=["db"]
        )

        result = incident_service.update_incident_status(
            incident_id=incident_id,
            new_status=IncidentStatus.INVESTIGATING,
            updated_by="responder",
            notes="Starting investigation"
        )

        assert result is True
        incident = incident_service.incidents[incident_id]
        assert incident.status == IncidentStatus.INVESTIGATING
        assert len(incident.timeline) == 2

    def test_update_non_existent_incident(self, incident_service):
        """Test updating a non-existent incident"""
        result = incident_service.update_incident_status(
            incident_id="fake_id",
            new_status=IncidentStatus.RESOLVED,
            updated_by="user"
        )
        assert result is False

    def test_assign_incident(self, incident_service):
        """Test assigning an incident"""
        incident_id = incident_service.create_incident(
            title="Assignment Test",
            description="Testing assignment",
            severity=IncidentSeverity.SEV3,
            detected_by="user",
            affected_services=["ui"]
        )

        result = incident_service.assign_incident(
            incident_id=incident_id,
            assigned_to="engineer_1",
            assigned_by="lead"
        )

        assert result is True
        assert incident_service.incidents[incident_id].assigned_to == "engineer_1"

    def test_on_call_schedule(self, incident_service):
        """Test adding and retrieving on-call schedule"""
        now = datetime.now(UTC)
        schedule = OnCallSchedule(
            schedule_id="sch_001",
            role=OnCallRole.PRIMARY,
            engineer_id="eng_001",
            engineer_name="John Doe",
            engineer_contact={"email": "john@example.com"},
            shift_start=now - timedelta(hours=1),
            shift_end=now + timedelta(hours=8),
            is_active=True
        )

        incident_service.add_on_call_schedule(schedule)

        current = incident_service.get_current_on_call(OnCallRole.PRIMARY)
        assert current is not None
        assert current.engineer_id == "eng_001"

        # Test finding no one
        none_schedule = incident_service.get_current_on_call(OnCallRole.SECONDARY)
        assert none_schedule is None

    def test_create_post_incident_review(self, incident_service):
        """Test creating a PIR"""
        pir_id = incident_service.create_post_incident_review(
            incident_id="inc_001",
            conducted_by="manager",
            attendees=["eng1", "eng2"],
            what_happened="Service down",
            what_went_well=["Detection"],
            what_could_improve=["Recovery speed"],
            action_items=[{"owner": "eng1", "task": "fix bug"}]
        )

        assert pir_id in incident_service.post_incident_reviews
        assert incident_service.post_incident_reviews[pir_id].what_happened == "Service down"

    def test_incident_metrics(self, incident_service):
        """Test calculating incident metrics"""
        # Create a resolved incident to test MTTR
        incident_id = incident_service.create_incident(
            title="Resolved Incident",
            description="Fixed",
            severity=IncidentSeverity.SEV1,
            detected_by="system",
            affected_services=["all"]
        )

        # Simulate time passing and resolution
        incident = incident_service.incidents[incident_id]
        incident.resolved_at = incident.detected_at + timedelta(minutes=10)
        incident.status = IncidentStatus.RESOLVED

        metrics = incident_service.get_incident_metrics()

        assert metrics["total_incidents"] == 1
        assert metrics["mttr_minutes"] == 10.0
        assert metrics["by_severity"]["sev1"] == 1
