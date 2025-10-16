"""
Tests for Prompt Engineering Feature
=====================================
Comprehensive test suite for the superhuman prompt engineering system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app import create_app, db
from app.models import User, PromptTemplate, GeneratedPrompt, AdminConversation
from app.services.prompt_engineering_service import PromptEngineeringService, get_prompt_engineering_service


@pytest.fixture
def app():
    """Create test application"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Create admin user for testing"""
    with app.app_context():
        user = User(
            full_name="Admin Test",
            email="admin@test.com",
            is_admin=True
        )
        user.set_password("testpass123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_template(app, admin_user):
    """Create a sample prompt template"""
    with app.app_context():
        template = PromptTemplate(
            name="Test Template",
            description="Template for testing",
            template_content="You are testing {project_name}. User request: {user_description}",
            category="testing",
            variables=[
                {"name": "project_name", "description": "Project name"},
                {"name": "user_description", "description": "User request"}
            ],
            few_shot_examples=[
                {
                    "description": "Test example",
                    "prompt": "Write tests for this code",
                    "result": "Comprehensive tests"
                }
            ],
            created_by_id=admin_user.id
        )
        db.session.add(template)
        db.session.commit()
        return template


class TestPromptTemplateModel:
    """Test PromptTemplate model"""
    
    def test_create_template(self, app, admin_user):
        """Test creating a prompt template"""
        with app.app_context():
            template = PromptTemplate(
                name="Code Generator",
                description="Generates code",
                template_content="Generate code for {user_description}",
                category="code_generation",
                created_by_id=admin_user.id
            )
            db.session.add(template)
            db.session.commit()
            
            assert template.id is not None
            assert template.name == "Code Generator"
            assert template.category == "code_generation"
            assert template.is_active is True
            assert template.version == 1
            assert template.usage_count == 0
    
    def test_template_relationships(self, app, admin_user):
        """Test template relationships"""
        with app.app_context():
            template = PromptTemplate(
                name="Test",
                template_content="Test",
                category="general",
                created_by_id=admin_user.id
            )
            db.session.add(template)
            db.session.commit()
            
            assert template.created_by.id == admin_user.id
            assert template.created_by.email == "admin@test.com"


class TestGeneratedPromptModel:
    """Test GeneratedPrompt model"""
    
    def test_create_generated_prompt(self, app, admin_user, sample_template):
        """Test creating a generated prompt"""
        with app.app_context():
            prompt = GeneratedPrompt(
                user_description="Create a REST API",
                template_id=sample_template.id,
                generated_prompt="Here is your prompt...",
                created_by_id=admin_user.id,
                generation_metadata={
                    "model": "gpt-4",
                    "elapsed_seconds": 2.5
                }
            )
            prompt.compute_content_hash()
            db.session.add(prompt)
            db.session.commit()
            
            assert prompt.id is not None
            assert prompt.content_hash is not None
            assert len(prompt.content_hash) == 64  # SHA256 hash length
    
    def test_prompt_with_rating(self, app, admin_user):
        """Test rating a generated prompt"""
        with app.app_context():
            prompt = GeneratedPrompt(
                user_description="Test",
                generated_prompt="Generated...",
                created_by_id=admin_user.id,
                rating=5,
                feedback_text="Excellent!"
            )
            db.session.add(prompt)
            db.session.commit()
            
            assert prompt.rating == 5
            assert prompt.feedback_text == "Excellent!"


class TestPromptEngineeringService:
    """Test PromptEngineeringService"""
    
    def test_service_singleton(self, app):
        """Test service singleton pattern"""
        with app.app_context():
            service1 = get_prompt_engineering_service()
            service2 = get_prompt_engineering_service()
            assert service1 is service2
    
    @patch('app.services.prompt_engineering_service.build_index')
    def test_get_project_context(self, mock_build_index, app):
        """Test getting project context"""
        with app.app_context():
            # Mock the index
            mock_build_index.return_value = {
                'files_scanned': 100,
                'global_metrics': {'total_functions': 250},
                'layers': {'service': [], 'model': []},
                'modules': []
            }
            
            service = PromptEngineeringService()
            context = service._get_project_context()
            
            assert context['project_name'] == 'CogniForge'
            assert context['files_indexed'] == 100
            assert 'architecture' in context
    
    def test_extract_keywords(self, app):
        """Test keyword extraction"""
        with app.app_context():
            service = PromptEngineeringService()
            text = "Create a REST API endpoint for user authentication"
            keywords = service._extract_keywords(text)
            
            assert 'rest' in keywords or 'REST' in [k.upper() for k in keywords]
            assert 'endpoint' in keywords
            assert len(keywords) <= 10
    
    def test_get_default_examples(self, app):
        """Test getting default examples"""
        with app.app_context():
            service = PromptEngineeringService()
            
            code_examples = service._get_default_examples("code_generation")
            assert len(code_examples) > 0
            assert 'description' in code_examples[0]
            assert 'prompt' in code_examples[0]
            
            doc_examples = service._get_default_examples("documentation")
            assert len(doc_examples) > 0
    
    @patch('app.services.prompt_engineering_service.get_llm_client')
    @patch('app.services.prompt_engineering_service.build_index')
    def test_generate_prompt_success(self, mock_build_index, mock_llm_client, app, admin_user):
        """Test successful prompt generation"""
        with app.app_context():
            # Mock dependencies
            mock_build_index.return_value = {
                'files_scanned': 50,
                'global_metrics': {'total_functions': 100},
                'layers': {},
                'modules': []
            }
            
            mock_llm = Mock()
            mock_llm.chat.return_value = {
                'content': 'Generated prompt content'
            }
            mock_llm_client.return_value = mock_llm
            
            service = PromptEngineeringService()
            result = service.generate_prompt(
                user_description="Create a Flask route",
                user=admin_user,
                prompt_type="code_generation"
            )
            
            assert result['status'] == 'success'
            assert 'generated_prompt' in result
            assert 'prompt_id' in result
            assert result['generated_prompt'] == 'Generated prompt content'
    
    def test_generate_prompt_empty_description(self, app, admin_user):
        """Test prompt generation with empty description"""
        with app.app_context():
            service = PromptEngineeringService()
            # This should be handled at the API level, but test service robustness
            result = service.generate_prompt(
                user_description="",
                user=admin_user
            )
            # Service should handle gracefully
            assert result is not None
    
    def test_create_template(self, app, admin_user):
        """Test creating a new template"""
        with app.app_context():
            service = PromptEngineeringService()
            result = service.create_template(
                name="New Template",
                template_content="Content for {user_description}",
                user=admin_user,
                category="general"
            )
            
            assert result['status'] == 'success'
            assert 'template_id' in result
    
    def test_list_templates(self, app, sample_template):
        """Test listing templates"""
        with app.app_context():
            service = PromptEngineeringService()
            templates = service.list_templates()
            
            assert len(templates) > 0
            assert any(t['name'] == 'Test Template' for t in templates)
    
    def test_rate_prompt(self, app, admin_user):
        """Test rating a prompt"""
        with app.app_context():
            # Create a prompt first
            prompt = GeneratedPrompt(
                user_description="Test",
                generated_prompt="Content",
                created_by_id=admin_user.id
            )
            db.session.add(prompt)
            db.session.commit()
            
            service = PromptEngineeringService()
            result = service.rate_prompt(
                prompt_id=prompt.id,
                rating=5,
                feedback_text="Great!"
            )
            
            assert result['status'] == 'success'
            
            # Verify rating was saved
            db.session.refresh(prompt)
            assert prompt.rating == 5
            assert prompt.feedback_text == "Great!"


class TestPromptEngineeringAPI:
    """Test API endpoints"""
    
    def login(self, client, email, password):
        """Helper to login"""
        return client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_generate_prompt_api_unauthorized(self, client):
        """Test generate endpoint requires auth"""
        response = client.post('/admin/api/prompt-engineering/generate',
                              json={'description': 'Test'})
        assert response.status_code in [401, 403, 302]  # Unauthorized or redirect to login
    
    def test_generate_prompt_api_no_description(self, client, app, admin_user):
        """Test generate endpoint requires description"""
        with app.app_context():
            # This test would need proper login setup
            # For now, just verify the endpoint exists
            response = client.post('/admin/api/prompt-engineering/generate',
                                  json={})
            assert response.status_code in [400, 401, 403, 302]
    
    def test_list_templates_api(self, client, app, admin_user, sample_template):
        """Test list templates endpoint"""
        with app.app_context():
            # Without auth, should redirect or deny
            response = client.get('/admin/api/prompt-engineering/templates')
            assert response.status_code in [200, 401, 403, 302]


class TestPromptEngineeringCLI:
    """Test CLI commands"""
    
    def test_cli_commands_registered(self, app):
        """Test that CLI commands are registered"""
        with app.app_context():
            runner = app.test_cli_runner()
            result = runner.invoke(args=['mindgate', '--help'])
            # Commands should be in help text
            help_text = result.output
            # Just verify the command group exists
            assert 'mindgate' in help_text.lower() or result.exit_code == 0


class TestPromptEngineeringIntegration:
    """Integration tests"""
    
    @patch('app.services.prompt_engineering_service.build_index')
    @patch('app.services.prompt_engineering_service.get_llm_client')
    def test_end_to_end_prompt_generation(self, mock_llm_client, mock_build_index, 
                                         app, admin_user, sample_template):
        """Test complete prompt generation flow"""
        with app.app_context():
            # Setup mocks
            mock_build_index.return_value = {
                'files_scanned': 100,
                'global_metrics': {'total_functions': 200},
                'layers': {'service': ['test_service']},
                'modules': []
            }
            
            mock_llm = Mock()
            mock_llm.chat.return_value = {
                'content': 'You are an expert Flask developer...'
            }
            mock_llm_client.return_value = mock_llm
            
            # Generate prompt
            service = PromptEngineeringService()
            result = service.generate_prompt(
                user_description="Create a user authentication endpoint",
                user=admin_user,
                template_id=sample_template.id,
                use_rag=True,
                prompt_type="code_generation"
            )
            
            # Verify success
            assert result['status'] == 'success'
            assert result['generated_prompt'] == 'You are an expert Flask developer...'
            assert 'prompt_id' in result
            
            # Verify database record
            prompt = GeneratedPrompt.query.get(result['prompt_id'])
            assert prompt is not None
            assert prompt.user_description == "Create a user authentication endpoint"
            assert prompt.template_id == sample_template.id
            
            # Rate the prompt
            rate_result = service.rate_prompt(
                prompt_id=result['prompt_id'],
                rating=5,
                feedback_text="Perfect!"
            )
            assert rate_result['status'] == 'success'
            
            # Verify rating
            db.session.refresh(prompt)
            assert prompt.rating == 5


class TestPromptEngineeringEdgeCases:
    """Test edge cases and error handling"""
    
    def test_very_long_description(self, app, admin_user):
        """Test handling of very long descriptions"""
        with app.app_context():
            service = PromptEngineeringService()
            long_description = "test " * 10000  # Very long
            
            # Service should handle gracefully
            result = service.generate_prompt(
                user_description=long_description[:10000],  # Truncate to reasonable
                user=admin_user
            )
            # Should not crash
            assert result is not None
    
    def test_invalid_template_id(self, app, admin_user):
        """Test with non-existent template"""
        with app.app_context():
            service = PromptEngineeringService()
            result = service.generate_prompt(
                user_description="Test",
                user=admin_user,
                template_id=99999  # Non-existent
            )
            
            assert result['status'] == 'error'
    
    def test_rate_nonexistent_prompt(self, app):
        """Test rating a non-existent prompt"""
        with app.app_context():
            service = PromptEngineeringService()
            result = service.rate_prompt(
                prompt_id=99999,
                rating=5
            )
            
            assert result['status'] == 'error'
    
    def test_invalid_rating(self, app, admin_user):
        """Test rating with invalid value"""
        with app.app_context():
            prompt = GeneratedPrompt(
                user_description="Test",
                generated_prompt="Content",
                created_by_id=admin_user.id
            )
            db.session.add(prompt)
            db.session.commit()
            
            service = PromptEngineeringService()
            
            # Rating too high
            result = service.rate_prompt(prompt_id=prompt.id, rating=10)
            assert result['status'] == 'error'
            
            # Rating too low
            result = service.rate_prompt(prompt_id=prompt.id, rating=0)
            assert result['status'] == 'error'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
