
import pytest
from app.config.ai_models import ActiveModels, AvailableModels, get_ai_config, AIConfig

class TestAIModelsConfiguration:
    def test_opus_4_5_is_available(self):
        """Verify that Claude Opus 4.5 is available in AvailableModels."""
        assert hasattr(AvailableModels, "CLAUDE_OPUS_4_5")
        assert AvailableModels.CLAUDE_OPUS_4_5 == "anthropic/claude-opus-4.5"

    def test_primary_model_is_opus_4_5(self):
        """Verify that the primary model is set to Claude Opus 4.5."""
        assert ActiveModels.PRIMARY == AvailableModels.CLAUDE_OPUS_4_5
        assert ActiveModels.PRIMARY == "anthropic/claude-opus-4.5"

    def test_gateway_primary_model_is_opus_4_5(self):
        """Verify that the gateway primary model is set to Claude Opus 4.5."""
        assert ActiveModels.GATEWAY_PRIMARY == AvailableModels.CLAUDE_OPUS_4_5
        assert ActiveModels.GATEWAY_PRIMARY == "anthropic/claude-opus-4.5"

    def test_ai_config_singleton_reflects_changes(self):
        """Verify that the AIConfig singleton reflects the configuration changes."""
        config = get_ai_config()
        assert config.primary_model == "anthropic/claude-opus-4.5"
        assert config.gateway_primary == "anthropic/claude-opus-4.5"
