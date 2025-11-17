"""
Tests for Prompt Engineering Feature
=====================================
Comprehensive test suite for the superhuman prompt engineering system.
"""

from unittest.mock import Mock, patch

import pytest

from app.models import GeneratedPrompt, PromptTemplate
from app.services.prompt_engineering_service import (
    PromptEngineeringService,
    get_prompt_engineering_service,
)


@pytest.fixture
def sample_template(admin_user, db_session):
    """Create a sample prompt template"""
    template = PromptTemplate(
        name="Test Template",
        description="Template for testing",
        template_content="You are testing {project_name}. User request: {user_description}",
        category="testing",
        variables=[
            {"name": "project_name", "description": "Project name"},
            {"name": "user_description", "description": "User request"},
        ],
        few_shot_examples=[
            {
                "description": "Test example",
                "prompt": "Write tests for this code",
                "result": "Comprehensive tests",
            }
        ],
        created_by_id=admin_user.id,
    )
    db_session.add(template)
    db_session.commit()
    return template


class TestPromptTemplateModel:
    """Test PromptTemplate model"""

    def test_create_template(self, admin_user, db_session):
        """Test creating a prompt template"""
        template = PromptTemplate(
            name="Code Generator",
            description="Generates code",
            template_content="Generate code for {user_description}",
            category="code_generation",
            created_by_id=admin_user.id,
        )
        db_session.add(template)
        db_session.commit()

        assert template.id is not None
        assert template.name == "Code Generator"
        assert template.category == "code_generation"
        assert template.is_active is True
        assert template.version == 1
        assert template.usage_count == 0

    def test_template_relationships(self, admin_user, db_session):
        """Test template relationships"""
        template = PromptTemplate(
            name="Test",
            template_content="Test",
            category="general",
            created_by_id=admin_user.id,
        )
        db_session.add(template)
        db_session.commit()

        assert template.created_by.id == admin_user.id
        assert template.created_by.email == admin_user.email


class TestGeneratedPromptModel:
    """Test GeneratedPrompt model"""

    def test_create_generated_prompt(self, admin_user, sample_template, db_session):
        """Test creating a generated prompt"""
        prompt = GeneratedPrompt(
            user_description="Create a REST API",
            template_id=sample_template.id,
            generated_prompt="Here is your prompt...",
            created_by_id=admin_user.id,
            generation_metadata={"model": "gpt-4", "elapsed_seconds": 2.5},
        )
        prompt.compute_content_hash()
        db_session.add(prompt)
        db_session.commit()

        assert prompt.id is not None
        assert prompt.content_hash is not None
        assert len(prompt.content_hash) == 64  # SHA256 hash length

    def test_prompt_with_rating(self, admin_user, db_session):
        """Test rating a generated prompt"""
        prompt = GeneratedPrompt(
            user_description="Test",
            generated_prompt="Generated...",
            created_by_id=admin_user.id,
            rating=5,
            feedback_text="Excellent!",
        )
        db_session.add(prompt)
        db_session.commit()

        assert prompt.rating == 5
        assert prompt.feedback_text == "Excellent!"


class TestPromptEngineeringService:
    """Test PromptEngineeringService"""

    def test_service_singleton(self):
        """Test service singleton pattern"""
        service1 = get_prompt_engineering_service()
        service2 = get_prompt_engineering_service()
        assert service1 is service2

    @patch("app.services.prompt_engineering_service.build_index")
    def test_get_project_context(self, mock_build_index):
        """Test getting project context"""
        mock_build_index.return_value = {
            "files_scanned": 100,
            "global_metrics": {"total_functions": 250},
            "layers": {"service": [], "model": []},
            "modules": [],
        }

        service = PromptEngineeringService()
        context = service._get_project_context()

        assert context["project_name"] == "CogniForge"
        assert context["files_indexed"] == 100
        assert "architecture" in context

    def test_extract_keywords(self):
        """Test keyword extraction"""
        service = PromptEngineeringService()
        text = "Create a REST API endpoint for user authentication"
        keywords = service._extract_keywords(text)

        assert "rest" in keywords or "REST" in [k.upper() for k in keywords]
        assert "endpoint" in keywords
        assert len(keywords) <= 10

    def test_get_default_examples(self):
        """Test getting default examples"""
        service = PromptEngineeringService()

        code_examples = service._get_default_examples("code_generation")
        assert len(code_examples) > 0
        assert "description" in code_examples[0]
        assert "prompt" in code_examples[0]

        doc_examples = service._get_default_examples("documentation")
        assert len(doc_examples) > 0

    @patch("app.services.prompt_engineering_service.get_llm_client")
    @patch("app.services.prompt_engineering_service.build_index")
    def test_generate_prompt_success(self, mock_build_index, mock_llm_client, admin_user):
        """Test successful prompt generation"""
        mock_build_index.return_value = {
            "files_scanned": 50,
            "global_metrics": {"total_functions": 100},
            "layers": {},
            "modules": [],
        }

        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "Generated prompt content with enough characters to pass the 50 char validation check in the service"
        }
        mock_llm_client.return_value = mock_llm

        service = PromptEngineeringService()
        result = service.generate_prompt(
            user_description="Create a Flask route",
            user=admin_user,
            prompt_type="code_generation",
        )

        assert result["status"] == "success"
        assert "generated_prompt" in result
        assert "prompt_id" in result
        assert len(result["generated_prompt"]) > 50
        assert (
            "Generated prompt content" in result["generated_prompt"]
            or "Create a Flask route" in result["generated_prompt"]
        )

    def test_generate_prompt_empty_description(self, admin_user):
        """Test prompt generation with empty description"""
        service = PromptEngineeringService()
        result = service.generate_prompt(user_description="", user=admin_user)
        assert result is not None

    def test_create_template(self, admin_user):
        """Test creating a new template"""
        service = PromptEngineeringService()
        result = service.create_template(
            name="New Template",
            template_content="Content for {user_description}",
            user=admin_user,
            category="general",
        )

        assert result["status"] == "success"
        assert "template_id" in result

    def test_list_templates(self, sample_template):
        """Test listing templates"""
        service = PromptEngineeringService()
        templates = service.list_templates()

        assert len(templates) > 0
        assert any(t["name"] == "Test Template" for t in templates)

    def test_rate_prompt(self, admin_user, db_session):
        """Test rating a prompt"""
        prompt = GeneratedPrompt(
            user_description="Test",
            generated_prompt="Content",
            created_by_id=admin_user.id,
        )
        db_session.add(prompt)
        db_session.commit()

        service = PromptEngineeringService()
        result = service.rate_prompt(prompt_id=prompt.id, rating=5, feedback_text="Great!")

        assert result["status"] == "success"
        db_session.refresh(prompt)
        assert prompt.rating == 5
        assert prompt.feedback_text == "Excellent!"


class TestPromptEngineeringAPI:
    """Test API endpoints"""

    def test_generate_prompt_api_unauthorized(self, client):
        """Test generate endpoint requires auth"""
        response = client.post(
            "/admin/api/prompt-engineering/generate", json={"description": "Test"}
        )
        assert response.status_code in [401, 403]

    def test_generate_prompt_api_no_description(self, client, admin_user):
        """Test generate endpoint requires description"""
        response = client.post("/admin/api/prompt-engineering/generate", json={})
        assert response.status_code in [400, 422, 401, 403]

    def test_list_templates_api(self, client, admin_user, sample_template):
        """Test list templates endpoint"""
        response = client.get("/admin/api/prompt-engineering/templates")
        assert response.status_code in [200, 401, 403]


@pytest.mark.skip(reason="CLI tests require a different runner (Typer's CliRunner)")
class TestPromptEngineeringCLI:
    """Test CLI commands"""

    def test_cli_commands_registered(self, app):
        """Test that CLI commands are registered"""
        pass


class TestPromptEngineeringIntegration:
    """Integration tests"""

    @patch("app.services.prompt_engineering_service.build_index")
    @patch("app.services.prompt_engineering_service.get_llm_client")
    def test_end_to_end_prompt_generation(
        self, mock_llm_client, mock_build_index, admin_user, sample_template, db_session
    ):
        """Test complete prompt generation flow"""
        mock_build_index.return_value = {
            "files_scanned": 100,
            "global_metrics": {"total_functions": 200},
            "layers": {"service": ["test_service"]},
            "modules": [],
        }

        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "You are an expert Flask developer with superhuman skills in creating authentication endpoints using best practices and security standards."
        }
        mock_llm_client.return_value = mock_llm

        service = PromptEngineeringService()
        result = service.generate_prompt(
            user_description="Create a user authentication endpoint",
            user=admin_user,
            template_id=sample_template.id,
            use_rag=True,
            prompt_type="code_generation",
        )

        assert result["status"] == "success"
        assert "generated_prompt" in result
        assert len(result["generated_prompt"]) > 50
        assert "prompt_id" in result

        prompt = db_session.get(GeneratedPrompt, result["prompt_id"])
        assert prompt is not None
        assert prompt.user_description == "Create a user authentication endpoint"
        assert prompt.template_id == sample_template.id

        rate_result = service.rate_prompt(
            prompt_id=result["prompt_id"], rating=5, feedback_text="Perfect!"
        )
        assert rate_result["status"] == "success"

        db_session.refresh(prompt)
        assert prompt.rating == 5


class TestPromptEngineeringEdgeCases:
    """Test edge cases and error handling"""

    def test_very_long_description(self, admin_user):
        """Test handling of very long descriptions"""
        service = PromptEngineeringService()
        long_description = "test " * 10000

        result = service.generate_prompt(
            user_description=long_description[:10000],
            user=admin_user,
        )
        assert result is not None

    def test_invalid_template_id(self, admin_user):
        """Test with non-existent template"""
        service = PromptEngineeringService()
        result = service.generate_prompt(
            user_description="Test",
            user=admin_user,
            template_id=99999,
        )
        assert result["status"] == "error"

    def test_rate_nonexistent_prompt(self):
        """Test rating a non-existent prompt"""
        service = PromptEngineeringService()
        result = service.rate_prompt(prompt_id=99999, rating=5)
        assert result["status"] == "error"

    def test_invalid_rating(self, admin_user, db_session):
        """Test rating with invalid value"""
        prompt = GeneratedPrompt(
            user_description="Test", generated_prompt="Content", created_by_id=admin_user.id
        )
        db_session.add(prompt)
        db_session.commit()

        service = PromptEngineeringService()

        result = service.rate_prompt(prompt_id=prompt.id, rating=10)
        assert result["status"] == "error"

        result = service.rate_prompt(prompt_id=prompt.id, rating=0)
        assert result["status"] == "error"
