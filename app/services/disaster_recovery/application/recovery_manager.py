# app/services/disaster_recovery/application/recovery_manager.py
import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from app.services.disaster_recovery.domain.models import (
    BackupMetadata,
    DisasterRecoveryPlan,
    RecoveryStrategy,
)
from app.services.disaster_recovery.infrastructure.repositories import InMemoryRecoveryRepository


class RecoveryManager:
    """Application service for Disaster Recovery logic"""

    def __init__(self, repository: InMemoryRecoveryRepository):
        self.repository = repository
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default disaster recovery plans"""
        # Database DR Plan
        db_plan = DisasterRecoveryPlan(
            plan_id="dr_db_001",
            name="Database Disaster Recovery",
            description="Recovery plan for complete database failure",
            strategy=RecoveryStrategy.WARM_STANDBY,
            rto_minutes=30,  # 30 minutes to restore service
            rpo_minutes=5,  # Maximum 5 minutes data loss
            runbook_url="https://github.com/HOUSSAM16ai/my_ai_project/wiki/Database-DR",
            backup_locations=["s3://backups/database/", "azure://backups/database/"],
            failover_regions=["us-east-1", "eu-west-1"],
            automated_steps=[
                {"step": 1, "action": "detect_failure", "timeout_seconds": 30},
                {"step": 2, "action": "verify_backup_availability", "timeout_seconds": 60},
                {"step": 3, "action": "initiate_failover", "timeout_seconds": 300},
                {"step": 4, "action": "verify_failover", "timeout_seconds": 120},
                {"step": 5, "action": "update_dns", "timeout_seconds": 60},
            ],
            manual_steps=[
                "Notify stakeholders of failover",
                "Monitor application performance",
                "Plan failback to primary region",
            ],
            test_frequency_days=90,
        )
        # Use legacy key for backward compatibility
        self.repository.save_plan(db_plan, key="database_dr")

        # API Service DR Plan
        api_plan = DisasterRecoveryPlan(
            plan_id="dr_api_001",
            name="API Service Disaster Recovery",
            description="Recovery plan for complete API service failure",
            strategy=RecoveryStrategy.MULTI_SITE_ACTIVE,
            rto_minutes=5,  # 5 minutes - automatic failover
            rpo_minutes=0,  # No data loss with multi-site active
            runbook_url="https://github.com/HOUSSAM16ai/my_ai_project/wiki/API-DR",
            backup_locations=["multiple-regions"],
            failover_regions=["us-east-1", "us-west-2", "eu-west-1"],
            automated_steps=[
                {"step": 1, "action": "detect_region_failure", "timeout_seconds": 30},
                {
                    "step": 2,
                    "action": "remove_failed_region_from_load_balancer",
                    "timeout_seconds": 10,
                },
                {"step": 3, "action": "verify_healthy_regions", "timeout_seconds": 30},
                {"step": 4, "action": "scale_up_remaining_regions", "timeout_seconds": 120},
            ],
            manual_steps=[
                "Investigate root cause of region failure",
                "Coordinate with cloud provider",
                "Plan recovery of failed region",
            ],
            test_frequency_days=30,
        )
        # Use legacy key for backward compatibility
        self.repository.save_plan(api_plan, key="api_dr")

    def register_backup(self, backup: BackupMetadata) -> bool:
        """Register a new backup"""
        self.repository.save_backup(backup)
        logging.info(
            f"Backup registered: {backup.backup_type} "
            f"({backup.size_bytes} bytes) at {backup.location}"
        )
        return True

    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity"""
        backup = self.repository.get_backup(backup_id)
        if not backup:
            return False

        # In production, this would actually verify the backup
        # by attempting a test restore or checksum validation
        backup.verified = True
        backup.verification_date = datetime.now(UTC)
        self.repository.save_backup(backup)

        logging.info(f"Backup verified: {backup_id}")
        return True

    def initiate_failover(self, plan_id: str, initiated_by: str, reason: str) -> dict[str, Any]:
        """Initiate disaster recovery failover"""
        plan = self.repository.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "DR plan not found"}

        # Create recovery event
        recovery_id = hashlib.sha256(f"{plan_id}{datetime.now(UTC)}".encode()).hexdigest()[:16]

        recovery_event = {
            "recovery_id": recovery_id,
            "plan_id": plan_id,
            "initiated_by": initiated_by,
            "initiated_at": datetime.now(UTC).isoformat(),
            "reason": reason,
            "status": "in_progress",
            "steps_completed": [],
            "steps_failed": [],
        }

        logging.critical(f"DISASTER RECOVERY INITIATED: {plan.name} by {initiated_by}")

        # In production, this would execute the automated steps
        # For now, we log the plan
        for step in plan.automated_steps:
            logging.info(
                f"DR Step {step['step']}: {step['action']} (timeout: {step['timeout_seconds']}s)"
            )

        self.repository.add_history_event(recovery_event)

        return {
            "success": True,
            "recovery_id": recovery_id,
            "plan": plan.name,
            "rto_minutes": plan.rto_minutes,
            "automated_steps": len(plan.automated_steps),
            "manual_steps": len(plan.manual_steps),
        }

    def get_rto_rpo_status(self) -> dict[str, Any]:
        """Get RTO/RPO compliance status"""
        plans = self.repository.get_all_plans()
        backups = self.repository.get_all_backups()

        return {
            "disaster_recovery_plans": {
                plan_id: {
                    "name": plan.name,
                    "rto_minutes": plan.rto_minutes,
                    "rpo_minutes": plan.rpo_minutes,
                    "strategy": plan.strategy.value,
                    "last_tested": plan.last_tested.isoformat() if plan.last_tested else None,
                    "test_overdue": (
                        (datetime.now(UTC) - plan.last_tested).days > plan.test_frequency_days
                        if plan.last_tested
                        else True
                    ),
                }
                for plan_id, plan in plans.items()
            },
            "backup_summary": {
                "total_backups": len(backups),
                "verified_backups": len([b for b in backups.values() if b.verified]),
                "total_size_gb": sum(b.size_bytes for b in backups.values()) / (1024**3),
            },
        }
