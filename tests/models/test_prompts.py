from app.core.domain.models import GeneratedPrompt, PromptTemplate


class TestPromptTemplateModel:
    """Tests for PromptTemplate model."""

    def test_template_creation(self):
        """PromptTemplate can be created with required fields."""
        template = PromptTemplate(name="greeting", template="Hello, {name}!")
        assert template.name == "greeting"
        assert template.template == "Hello, {name}!"


class TestGeneratedPromptModel:
    """Tests for GeneratedPrompt model."""

    def test_prompt_creation(self):
        """GeneratedPrompt can be created with required fields."""
        prompt = GeneratedPrompt(prompt="Hello, World!", template_id=1)
        assert prompt.prompt == "Hello, World!"
        assert prompt.template_id == 1
