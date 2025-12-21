from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeneratedPrompt, PromptTemplate, User
from app.services.ai_engineering.prompt_engineering_service import prompt_engineering_service


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    return User(id=1, email="test@example.com", is_admin=False)


@pytest.mark.asyncio
async def test_generate_prompt_existing_template(mock_db_session, mock_user):
    """Test generating a prompt with an existing template."""
    template_name = "existing_template"
    template_content = "Hello, {name}!"
    variables = {"name": "World"}

    # Mock the database result for existing template
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = PromptTemplate(
        id=1, name=template_name, template=template_content
    )
    mock_db_session.execute.return_value = mock_result

    result = await prompt_engineering_service.generate_prompt(
        mock_db_session, mock_user, template_name, variables
    )

    assert result == "Hello, World!"
    # Verify we didn't add a new template
    # Verify we added a generated prompt record
    assert mock_db_session.add.call_count == 1
    assert isinstance(mock_db_session.add.call_args[0][0], GeneratedPrompt)
    assert mock_db_session.commit.call_count == 1


@pytest.mark.asyncio
async def test_generate_prompt_missing_template(mock_db_session, mock_user):
    """Test generating a prompt when the template is missing (should create default)."""
    template_name = "new_template"
    variables = {"prompt": "test prompt"}

    # Mock the database result for missing template
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db_session.execute.return_value = mock_result

    # Mock add/refresh
    def side_effect_refresh(obj):
        if isinstance(obj, PromptTemplate):
            obj.id = 2
        return None

    mock_db_session.refresh.side_effect = side_effect_refresh

    result = await prompt_engineering_service.generate_prompt(
        mock_db_session, mock_user, template_name, variables
    )

    assert result == "Default template: test prompt"

    # Verify we added a new template AND a generated prompt record
    assert mock_db_session.add.call_count == 2

    # Check that the first added object was a PromptTemplate
    added_template = mock_db_session.add.call_args_list[0][0][0]
    assert isinstance(added_template, PromptTemplate)
    assert added_template.name == template_name

    # Check that the second added object was a GeneratedPrompt
    added_generated = mock_db_session.add.call_args_list[1][0][0]
    assert isinstance(added_generated, GeneratedPrompt)
    assert added_generated.prompt == "Default template: test prompt"
    assert added_generated.template_id == 2

    assert mock_db_session.commit.call_count == 2


@pytest.mark.asyncio
async def test_generate_prompt_formatting_error(mock_db_session, mock_user):
    """Test that a KeyError is raised if variables don't match the template."""
    template_name = "broken_template"
    template_content = "Hello, {name}!"
    variables = {"wrong_key": "World"}

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = PromptTemplate(
        id=1, name=template_name, template=template_content
    )
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(KeyError):
        await prompt_engineering_service.generate_prompt(
            mock_db_session, mock_user, template_name, variables
        )
