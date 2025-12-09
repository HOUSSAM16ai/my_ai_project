"""
Tests for refactored ai_gateway functions.
Ensures complexity reduction maintains functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.ai_gateway import NeuralRoutingMesh


class TestAIGatewayRefactored:
    """Test refactored AI Gateway methods."""

    @pytest.fixture
    def mesh(self):
        """Create a NeuralRoutingMesh instance."""
        return NeuralRoutingMesh(api_key="test_api_key")

    def test_validate_messages_empty(self, mesh):
        """Test validation rejects empty messages."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            mesh._validate_messages([])

    def test_validate_messages_none(self, mesh):
        """Test validation rejects None messages."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            mesh._validate_messages(None)

    def test_validate_messages_valid(self, mesh):
        """Test validation accepts valid messages."""
        messages = [{"role": "user", "content": "Hello"}]
        mesh._validate_messages(messages)  # Should not raise

    def test_extract_prompt_and_context(self, mesh):
        """Test prompt and context extraction."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello AI"},
        ]

        prompt, context_hash = mesh._extract_prompt_and_context(messages)

        assert prompt == "Hello AI"
        assert isinstance(context_hash, str)
        assert len(context_hash) == 64  # SHA256 hex digest

    def test_extract_prompt_empty_messages(self, mesh):
        """Test extraction with empty messages."""
        prompt, context_hash = mesh._extract_prompt_and_context([])

        assert prompt == ""
        assert isinstance(context_hash, str)

    def test_assemble_response_content(self, mesh):
        """Test response content assembly."""
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": " world"}}]},
            {"choices": [{"delta": {"content": "!"}}]},
        ]

        content = mesh._assemble_response_content(chunks)

        assert content == "Hello world!"

    def test_assemble_response_content_empty(self, mesh):
        """Test assembly with empty chunks."""
        content = mesh._assemble_response_content([])
        assert content == ""

    def test_assemble_response_content_missing_fields(self, mesh):
        """Test assembly with missing fields."""
        chunks = [
            {"choices": [{}]},
            {"choices": [{"delta": {}}]},
        ]

        content = mesh._assemble_response_content(chunks)
        assert content == ""

    @pytest.mark.asyncio
    async def test_try_recall_from_cache_miss(self, mesh):
        """Test cache miss returns None."""
        with patch("app.core.ai_gateway.get_cognitive_engine") as mock_engine:
            mock_engine.return_value.recall.return_value = None

            result = mesh._try_recall_from_cache("test prompt", "hash123")

            assert result is None

    def test_try_recall_from_cache_hit(self, mesh):
        """Test cache hit returns cached data."""
        cached_data = [{"chunk": 1}, {"chunk": 2}]

        with patch("app.core.ai_gateway.get_cognitive_engine") as mock_engine:
            mock_engine.return_value.recall.return_value = cached_data

            result = mesh._try_recall_from_cache("test prompt", "hash123")

            assert result == cached_data

    def test_record_success_metrics(self, mesh):
        """Test success metrics recording."""
        node = MagicMock()
        node.model_id = "test-model"
        mesh.omni_router = MagicMock()

        with patch("app.core.ai_gateway._performance_optimizer") as mock_optimizer:
            mesh._record_success_metrics(
                node=node,
                prompt="test",
                duration_ms=100.0,
                full_content="response content",
                quality_score=0.9,
            )

            assert mesh.omni_router.record_outcome.called
            assert mock_optimizer.record_request.called

    def test_record_empty_response(self, mesh):
        """Test empty response recording."""
        node = MagicMock()
        node.model_id = "test-model"
        errors = []
        mesh.omni_router = MagicMock()

        with patch("app.core.ai_gateway._performance_optimizer") as mock_optimizer:
            mesh._record_empty_response(
                node=node,
                prompt="test",
                duration_ms=100.0,
                errors=errors,
            )

            assert len(errors) == 1
            assert "Empty response" in errors[0]
            assert mesh.omni_router.record_outcome.called
            assert mock_optimizer.record_request.called

    def test_handle_rate_limit_error(self, mesh):
        """Test rate limit error handling."""
        node = MagicMock()
        node.model_id = "test-model"
        errors = []

        mesh._handle_rate_limit_error(node, "test prompt", errors)

        assert len(errors) == 1
        assert "Rate Limited" in errors[0]
        node.circuit_breaker.record_saturation.assert_called_once()

    def test_handle_connection_error_no_yield(self, mesh):
        """Test connection error handling without prior yield."""
        from app.core.ai_gateway import AIConnectionError

        node = MagicMock()
        node.model_id = "test-model"
        error = AIConnectionError("Connection failed")
        errors = []

        with patch("app.core.ai_gateway._performance_optimizer"):
            mesh._handle_connection_error(node, "test", error, False, errors)

        assert len(errors) == 1
        assert "Connection error" in errors[0]
        node.circuit_breaker.record_failure.assert_called_once()

    def test_handle_connection_error_with_yield(self, mesh):
        """Test connection error handling after yield raises."""
        from app.core.ai_gateway import AIConnectionError

        node = MagicMock()
        node.model_id = "test-model"
        error = AIConnectionError("Connection failed")
        errors = []

        with patch("app.core.ai_gateway._performance_optimizer"):
            with pytest.raises(AIConnectionError):
                mesh._handle_connection_error(node, "test", error, True, errors)

    def test_handle_unexpected_error_no_yield(self, mesh):
        """Test unexpected error handling without prior yield."""
        node = MagicMock()
        node.model_id = "test-model"
        error = Exception("Unexpected error")
        errors = []

        mesh._handle_unexpected_error(node, "test", error, False, errors)

        assert len(errors) == 1
        assert "Exception" in errors[0]
        node.circuit_breaker.record_failure.assert_called_once()

    def test_handle_unexpected_error_with_yield(self, mesh):
        """Test unexpected error handling after yield raises."""
        node = MagicMock()
        node.model_id = "test-model"
        error = Exception("Unexpected error")
        errors = []

        with pytest.raises(Exception, match="Unexpected error"):
            mesh._handle_unexpected_error(node, "test", error, True, errors)


class TestComplexityReduction:
    """Verify complexity reduction goals."""

    def test_extracted_methods_exist(self):
        """Verify all extracted methods exist."""
        mesh = NeuralRoutingMesh(api_key="test_api_key")

        # Validation
        assert hasattr(mesh, "_validate_messages")

        # Cache operations
        assert hasattr(mesh, "_extract_prompt_and_context")
        assert hasattr(mesh, "_try_recall_from_cache")

        # Response processing
        assert hasattr(mesh, "_assemble_response_content")
        assert hasattr(mesh, "_process_node_response")

        # Metrics recording
        assert hasattr(mesh, "_record_success_metrics")
        assert hasattr(mesh, "_record_empty_response")

        # Error handling
        assert hasattr(mesh, "_handle_rate_limit_error")
        assert hasattr(mesh, "_handle_connection_error")
        assert hasattr(mesh, "_handle_unexpected_error")

    def test_methods_are_small(self):
        """Verify extracted methods are small (SRP)."""
        import inspect

        mesh = NeuralRoutingMesh(api_key="test_api_key")

        small_methods = [
            "_validate_messages",
            "_extract_prompt_and_context",
            "_assemble_response_content",
            "_record_success_metrics",
            "_record_empty_response",
            "_handle_rate_limit_error",
        ]

        for method_name in small_methods:
            method = getattr(mesh, method_name)
            source = inspect.getsource(method)
            lines = [
                line
                for line in source.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

            # Small methods should be < 30 lines (including docstrings)
            assert len(lines) < 30, f"{method_name} has {len(lines)} lines"
