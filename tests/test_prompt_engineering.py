# tests/test_prompt_engineering.py
import pytest
from sqlalchemy.orm import Session

from app.models import User
from app.services.prompt_engineering_service import PromptEngineeringService


@pytest.fixture
def service() -> PromptEngineeringService:
    return PromptEngineeringService()

def test_generate_prompt_success(service: PromptEngineeringService, session: Session):
    user = User(full_name="Test User", email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    result = service.generate_prompt(
        db=session,
        user_description="Create a test prompt",
        user=user,
    )

    assert result["status"] == "success"
    assert "prompt_id" in result
    assert "generated_prompt" in result
