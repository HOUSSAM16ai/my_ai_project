"""Version management application service."""

import logging
from datetime import UTC, datetime

from ..domain.models import APIVersion
from ..domain.ports import VersionManager

logger = logging.getLogger(__name__)


class VersionService:
    """Manages API versioning and lifecycle."""

    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager

    def get_active_versions(self) -> list[APIVersion]:
        """Get all active API versions."""
        all_versions = self.version_manager.list_versions()
        return [v for v in all_versions if v.status == "active"]

    def check_version_status(self, version: str) -> str:
        """Check the status of a version."""
        api_version = self.version_manager.get_version(version)
        if not api_version:
            return "unknown"

        # Check if version is sunset
        if api_version.sunset_date and datetime.now(UTC) > api_version.sunset_date:
            return "sunset"

        # Check if version is deprecated
        if (
            api_version.deprecation_date
            and datetime.now(UTC) > api_version.deprecation_date
        ):
            return "deprecated"

        return api_version.status

    def is_version_supported(self, version: str) -> bool:
        """Check if a version is still supported."""
        status = self.check_version_status(version)
        return status in ["active", "deprecated"]

    def get_version_info(self, version: str) -> APIVersion | None:
        """Get detailed version information."""
        return self.version_manager.get_version(version)

    def get_breaking_changes(self, version: str) -> list[str]:
        """Get breaking changes for a version."""
        api_version = self.version_manager.get_version(version)
        return api_version.breaking_changes if api_version else []
