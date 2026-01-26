from app.core.ai_config import ActiveModels, AvailableModels, get_ai_config


class TestAIModelsConfiguration:
    def test_opus_4_5_is_available(self):
        """Verify that Claude Opus 4.5 is available in AvailableModels."""
        assert hasattr(AvailableModels, "CLAUDE_OPUS_4_5")
        assert AvailableModels.CLAUDE_OPUS_4_5 == "anthropic/claude-opus-4.5"

    def test_primary_model_is_configured(self):
        """Verify that the primary model is configured and matches the singleton."""
        config = get_ai_config()
        assert ActiveModels.PRIMARY
        assert config.primary_model == ActiveModels.PRIMARY

    def test_gateway_primary_model_is_configured(self):
        """Verify that the gateway primary model is configured and matches the singleton."""
        config = get_ai_config()
        assert ActiveModels.GATEWAY_PRIMARY
        assert config.gateway_primary == ActiveModels.GATEWAY_PRIMARY

    def test_ai_config_singleton_reflects_changes(self):
        """Verify that the AIConfig singleton reflects the configuration changes."""
        config = get_ai_config()
        assert config.primary_model == ActiveModels.PRIMARY
        assert config.gateway_primary == ActiveModels.GATEWAY_PRIMARY
