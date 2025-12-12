"""GitOps controller application service."""

import logging
from datetime import UTC, datetime

from ..domain.models import DriftDetectionResult, GitOpsApplication, SyncStatus
from ..domain.ports import ApplicationRepository, GitOpsSync

logger = logging.getLogger(__name__)


class GitOpsController:
    """Controls GitOps synchronization and drift detection."""

    def __init__(self, app_repository: ApplicationRepository, sync_engine: GitOpsSync):
        self.app_repository = app_repository
        self.sync_engine = sync_engine

    def register_application(self, app: GitOpsApplication) -> None:
        """Register a new GitOps application."""
        self.app_repository.save_application(app)
        logger.info(f"Registered GitOps app: {app.name}")

    def sync_application(self, app_id: str) -> bool:
        """Synchronize application from Git."""
        app = self.app_repository.get_application(app_id)
        if not app:
            logger.error(f"Application not found: {app_id}")
            return False

        app.sync_status = SyncStatus.SYNCING
        self.app_repository.save_application(app)

        try:
            success = self.sync_engine.sync_application(app)
            app.sync_status = SyncStatus.SYNCED if success else SyncStatus.FAILED
            app.last_sync = datetime.now(UTC)
            self.app_repository.save_application(app)
            return success
        except Exception as e:
            logger.error(f"Sync failed for {app_id}: {e}")
            app.sync_status = SyncStatus.FAILED
            self.app_repository.save_application(app)
            return False

    def detect_drift(self, app_id: str) -> DriftDetectionResult:
        """Detect configuration drift."""
        app = self.app_repository.get_application(app_id)
        if not app:
            return DriftDetectionResult(has_drift=False)

        result = self.sync_engine.detect_drift(app)
        if result.has_drift:
            logger.warning(
                f"Drift detected in {app.name}: {len(result.drifted_resources)} resources"
            )
            app.sync_status = SyncStatus.OUT_OF_SYNC
            self.app_repository.save_application(app)

        return result

    def get_out_of_sync_apps(self) -> list[GitOpsApplication]:
        """Get applications that are out of sync."""
        all_apps = self.app_repository.list_applications()
        return [a for a in all_apps if a.sync_status == SyncStatus.OUT_OF_SYNC]
