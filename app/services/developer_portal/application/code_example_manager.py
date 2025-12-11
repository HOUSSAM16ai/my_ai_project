# app/services/developer_portal/application/code_example_manager.py
"""Code Example Management Service - Single Responsibility"""

import uuid
from datetime import datetime, UTC

from app.services.developer_portal.domain.models import CodeExample, SDKLanguage
from app.services.developer_portal.domain.ports import CodeExampleRepository


class CodeExampleManager:
    """
    Manages code examples.
    
    Single Responsibility: Code example creation, organization, retrieval.
    """

    def __init__(self, repository: CodeExampleRepository):
        self._repo = repository

    def create_example(
        self,
        title: str,
        description: str,
        language: SDKLanguage,
        code: str,
        endpoint: str,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> CodeExample:
        """Create new code example"""
        example = CodeExample(
            example_id=str(uuid.uuid4()),
            title=title,
            description=description,
            language=language,
            code=code,
            endpoint=endpoint,
            category=category,
            created_at=datetime.now(UTC),
            tags=tags or [],
        )

        self._repo.create(example)
        return example

    def get_examples_by_category(self, category: str) -> list[CodeExample]:
        """Get all examples for a category"""
        return self._repo.list_by_category(category)

    def get_example(self, example_id: str) -> CodeExample | None:
        """Get specific example"""
        return self._repo.get(example_id)
