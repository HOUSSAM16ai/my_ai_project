"""Mock GitOps sync engine for testing."""

import logging
from datetime import UTC, datetime

from ..domain.models import DriftDetectionResult, GitOpsApplication
from ..domain.ports import GitOpsSync

logger = logging.getLogger(__name__)


class MockGitOpsSync(GitOpsSync):
    """Mock implementation of GitOps sync."""

    def sync_application(self, app: GitOpsApplication) -> bool:
        """Mock sync - always succeeds."""
        logger.info(f"Mock sync for {app.name} from {app.git_repo}@{app.git_branch}")
        return True

    def detect_drift(self, app: GitOpsApplication) -> DriftDetectionResult:
        """Mock drift detection - no drift."""
        return DriftDetectionResult(
            has_drift=False, drifted_resources=[], detected_at=datetime.now(UTC)
        )
