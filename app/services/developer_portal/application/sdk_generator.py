# app/services/developer_portal/application/sdk_generator.py
"""SDK Generation Service - Single Responsibility"""

import hashlib
import uuid
from datetime import datetime, UTC

from app.services.developer_portal.domain.models import SDKPackage, SDKLanguage
from app.services.developer_portal.domain.ports import SDKRepository


class SDKGenerator:
    """
    Generates SDK packages.
    
    Single Responsibility: SDK generation, versioning, distribution.
    """

    def __init__(self, repository: SDKRepository):
        self._repo = repository

    def generate_sdk(
        self,
        language: SDKLanguage,
        api_version: str,
    ) -> SDKPackage:
        """Generate SDK for a language"""
        sdk_id = str(uuid.uuid4())
        version = self._get_next_version(language)

        # Mock SDK generation (in real app, this would compile/package code)
        sdk_content = self._generate_sdk_content(language, api_version)
        checksum = hashlib.sha256(sdk_content.encode()).hexdigest()

        sdk = SDKPackage(
            sdk_id=sdk_id,
            language=language,
            version=version,
            api_version=api_version,
            generated_at=datetime.now(UTC),
            download_url=f"https://sdks.example.com/{language.value}/{version}/sdk.zip",
            checksum=checksum,
            size_bytes=len(sdk_content),
        )

        self._repo.create(sdk)
        return sdk

    def increment_download_count(self, sdk_id: str) -> bool:
        """Increment SDK download counter"""
        sdk = self._repo.get(sdk_id)
        if not sdk:
            return False

        sdk.downloads += 1
        # Note: This would require update method in repository
        return True

    def _get_next_version(self, language: SDKLanguage) -> str:
        """Calculate next version number"""
        existing = self._repo.list_by_language(language.value)
        if not existing:
            return "1.0.0"

        # Simple version increment (in real app, use semver library)
        versions = [int(sdk.version.split(".")[0]) for sdk in existing]
        next_major = max(versions) + 1 if versions else 1
        return f"{next_major}.0.0"

    def _generate_sdk_content(self, language: SDKLanguage, api_version: str) -> str:
        """Generate SDK source code (mock)"""
        return f"# Generated SDK for {language.value}\n# API Version: {api_version}\n"
