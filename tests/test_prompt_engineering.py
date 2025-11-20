# tests/test_prompt_engineering.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.prompt_engineering_service import PromptEngineeringService


@pytest.fixture
def service() -> PromptEngineeringService:
    return PromptEngineeringService()


@pytest.mark.asyncio
async def test_generate_prompt_success(service: PromptEngineeringService, session: AsyncSession):
    user = User(full_name="Test User", email="test@example.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    result = await service.generate_prompt(
        db=session,
        user=user,
        template_name="test_template",
        variables={"prompt": "Hello World"},
        user_description="Create a test prompt",
    )

    assert isinstance(result, str)
    assert "Default template: Hello World" == result
