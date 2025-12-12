"""Version manager implementation."""

from datetime import UTC, datetime

from ..domain.models import APIVersion
from ..domain.ports import VersionManager


class InMemoryVersionManager(VersionManager):
    """In-memory version management."""

    def __init__(self):
        # Initialize with default versions
        self._versions = {
            "v1": APIVersion(
                version="v1",
                release_date=datetime(2025, 1, 1, tzinfo=UTC),
                status="active",
                changelog="Initial release with CRUD operations and observability",
            ),
            "v2": APIVersion(
                version="v2",
                release_date=datetime(2025, 10, 12, tzinfo=UTC),
                status="active",
                breaking_changes=[
                    "Response format changed to include metadata wrapper",
                    "Authentication now requires JWT tokens",
                    "Rate limiting headers added to all responses",
                ],
                changelog="Enhanced with Zero-Trust security, advanced monitoring, and ML-based features",
            ),
        }

    def get_version(self, version: str) -> APIVersion | None:
        """Get version metadata."""
        return self._versions.get(version)

    def list_versions(self) -> list[APIVersion]:
        """List all API versions."""
        return list(self._versions.values())

    def is_version_active(self, version: str) -> bool:
        """Check if version is active."""
        api_version = self._versions.get(version)
        if not api_version:
            return False

        # Check sunset date
        if api_version.sunset_date and datetime.now(UTC) > api_version.sunset_date:
            return False

        return api_version.status == "active"
