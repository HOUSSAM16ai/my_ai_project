# tests/test_prompt_engineering.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.ai_engineering.prompt_engineering_service import PromptEngineeringService


@pytest.fixture
def service() -> PromptEngineeringService:
    return PromptEngineeringService()


@pytest.mark.asyncio
async def test_generate_prompt_success(service: PromptEngineeringService, db_session: AsyncSession):
    from app.models import PromptTemplate

    # Pre-create the template to avoid race conditions and ensure test isolation
    template = PromptTemplate(name="test_template", template="Default template: {prompt}")
    db_session.add(template)
    await db_session.commit()

    user = User(full_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    result = await service.generate_prompt(
        db=db_session,
        user=user,
        template_name="test_template",
        variables={"prompt": "Hello World"},
        user_description="Create a test prompt",
    )

    assert isinstance(result, str)
    assert result == "Default template: Hello World"
