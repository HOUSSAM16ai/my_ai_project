import json
import os
from unittest import mock

import pytest

from app.services.llm_client_service import (
    _BREAKER_STATE,
    _LLMTOTAL,
    _POST_HOOKS,
    _PRE_HOOKS,
    MockLLMClient,
    _HttpFallbackClient,
    get_llm_client,
    invoke_chat,
    invoke_chat_stream,
    is_mock_client,
    llm_health,
    register_llm_post_hook,
    register_llm_pre_hook,
    reset_llm_client,
)


@pytest.fixture(autouse=True)
def reset_llm_service_state():
    """Reset the global state of the LLM service before each test."""
    reset_llm_client()
    _BREAKER_STATE["errors"] = []
    _BREAKER_STATE["open_until"] = 0.0
    _BREAKER_STATE["open_events"] = 0

    _LLMTOTAL["prompt_tokens"] = 0
    _LLMTOTAL["completion_tokens"] = 0
    _LLMTOTAL["total_tokens"] = 0
    _LLMTOTAL["calls"] = 0
    _LLMTOTAL["errors"] = 0
    _LLMTOTAL["cost_usd"] = 0.0
    _LLMTOTAL["latencies_ms"] = []
    _LLMTOTAL["last_error_kind"] = None

    _PRE_HOOKS.clear()
    _POST_HOOKS.clear()

    # Also clear env vars that might affect the tests
    with mock.patch.dict(os.environ, {}, clear=True):
        yield


class TestLLMInitialization:
    def test_get_llm_client_defaults_to_mock(self):
        """Test that without API keys, it defaults to a mock client."""
        client = get_llm_client()
        assert is_mock_client(client)
        assert isinstance(client, MockLLMClient)
        assert client.meta()["reason"] == "no-api-key"

    def test_force_mock_mode(self):
        """Test LLM_FORCE_MOCK environment variable."""
        with mock.patch.dict(os.environ, {"LLM_FORCE_MOCK": "1", "OPENAI_API_KEY": "sk-fake"}):
            reset_llm_client()
            client = get_llm_client()
            assert is_mock_client(client)
            # The client stores the reason passed to constructor
            assert client.meta()["reason"] == "forced-mock-flag"
            # The global meta stores the reason "forced"
            assert llm_health()["meta"]["reason"] == "forced"

    def test_openai_client_initialization(self):
        """Test initialization with OpenAI API key."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            with mock.patch("app.services.llm_client_service.openai") as mock_openai:
                # Setup mock for modern OpenAI client
                mock_openai.OpenAI.return_value = mock.Mock()

                reset_llm_client()
                client = get_llm_client()

                assert not is_mock_client(client)
                assert not isinstance(client, MockLLMClient)
                mock_openai.OpenAI.assert_called_once()
                call_kwargs = mock_openai.OpenAI.call_args[1]
                assert call_kwargs["api_key"] == "sk-test-key"

    def test_openrouter_http_fallback(self):
        """Test OpenRouter with HTTP fallback enabled."""
        env_vars = {"OPENROUTER_API_KEY": "sk-or-test", "LLM_HTTP_FALLBACK": "1"}
        with mock.patch.dict(os.environ, env_vars):
            with mock.patch("app.services.llm_client_service.requests"):
                # Mock openai to be None so it skips to fallback check or fails
                with mock.patch("app.services.llm_client_service.openai", None):
                    reset_llm_client()
                    client = get_llm_client()

                    assert isinstance(client, _HttpFallbackClient)
                    meta = client.meta()
                    assert meta["http_fallback"] is True
                    assert meta["base_url"] == "https://openrouter.ai/api/v1"

    def test_real_client_init_failure_falls_back_to_mock(self):
        """Test that if real client fails to init, we get a mock client."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with mock.patch("app.services.llm_client_service.openai") as mock_openai:
                # Make modern client init fail
                mock_openai.OpenAI.side_effect = Exception("Boom")

                # Make legacy client wrapper init fail by ensuring it returns None
                # The code checks `if not hasattr(openai, "ChatCompletion"): return None`
                del mock_openai.ChatCompletion

                reset_llm_client()
                client = get_llm_client()

                assert is_mock_client(client)
                assert client.meta()["reason"] == "real-client-init-failure"


class TestMockClient:
    def test_mock_client_chat_completion(self):
        client = MockLLMClient("test")
        messages = [{"role": "user", "content": "Hello world"}]

        response = client.chat.completions.create(model="gpt-4", messages=messages)

        assert hasattr(response, "choices")
        assert len(response.choices) > 0
        content = response.choices[0].message.content
        assert "[MOCK:test]" in content
        assert "User: Hello world" in content
        assert hasattr(response, "usage")


class TestHttpFallbackClient:
    def test_http_fallback_chat_completion_success(self):
        client = _HttpFallbackClient("key", "http://base.url", 10.0)

        with mock.patch("app.services.llm_client_service.requests") as mock_requests:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}],
                "usage": {"total_tokens": 10},
            }
            mock_requests.post.return_value = mock_response

            response = client.chat.completions.create(
                model="test-model", messages=[{"role": "user", "content": "Hi"}]
            )

            assert response.choices[0].message.content == "Response"
            mock_requests.post.assert_called_once()
            _args, kwargs = mock_requests.post.call_args
            assert kwargs["headers"]["Authorization"] == "Bearer key"
            assert kwargs["json"]["model"] == "test-model"

    def test_http_fallback_errors(self):
        client = _HttpFallbackClient("key", "http://base.url", 10.0)

        scenarios = [
            (500, "server_error_500"),
            (401, "authentication_error"),
            (429, "rate_limit_error"),
            (418, "HTTP fallback bad status"),
        ]

        with mock.patch("app.services.llm_client_service.requests") as mock_requests:
            for status, error_substr in scenarios:
                mock_response = mock.Mock()
                mock_response.status_code = status
                mock_response.text = "Error detail"
                mock_requests.post.return_value = mock_response

                with pytest.raises(RuntimeError, match=error_substr):
                    client.chat.completions.create(model="m", messages=[])


class TestInvocationLogic:
    def test_invoke_chat_success_mock(self):
        """Test simple successful invocation with mock."""
        result = invoke_chat("gpt-4", [{"role": "user", "content": "test"}])

        assert "content" in result
        assert "[MOCK:no-api-key]" in result["content"]
        assert result["meta"]["attempts"] == 1
        assert _LLMTOTAL["calls"] == 1

    def test_invoke_chat_hooks(self):
        """Test pre and post hooks."""
        pre_called = False
        post_called = False

        def pre_hook(payload):
            nonlocal pre_called
            pre_called = True
            assert payload["model"] == "gpt-4"

        def post_hook(payload, envelope):
            nonlocal post_called
            post_called = True
            assert "content" in envelope

        register_llm_pre_hook(pre_hook)
        register_llm_post_hook(post_hook)

        invoke_chat("gpt-4", [{"role": "user", "content": "test"}])

        assert pre_called
        assert post_called

    def test_invoke_chat_retry_logic(self):
        """Test that retries happen on failure."""
        with mock.patch.dict(os.environ, {"LLM_MAX_RETRIES": "3", "LLM_RETRY_BACKOFF_BASE": "1.0"}):
            client = get_llm_client()  # Mock client

            # Since client.chat returns new wrapper each time, we patch the class method
            # MockLLMClient._ChatWrapper._CompletionsWrapper.create

            original_create = MockLLMClient._ChatWrapper._CompletionsWrapper.create

            mock_create = mock.Mock()
            # Fail twice with a retriable error (e.g., timeout), then succeed
            # Note: create takes (self, model, messages, ...) so we should mock return value

            # Create a success response object
            success_resp = original_create(client.chat.completions, model="m", messages=[])

            mock_create.side_effect = [
                RuntimeError("timeout error"),
                RuntimeError("timeout error"),
                success_resp,
            ]

            with mock.patch.object(
                MockLLMClient._ChatWrapper._CompletionsWrapper,
                "create",
                side_effect=mock_create.side_effect,
            ):
                with mock.patch("time.sleep"):
                    result = invoke_chat("m", [{"role": "user", "content": "test"}])

                assert result["meta"]["attempts"] == 3
                assert _LLMTOTAL["errors"] == 2

    def test_circuit_breaker(self):
        """Test that circuit breaker opens after threshold errors."""
        env = {
            "LLM_BREAKER_ERROR_THRESHOLD": "2",
            "LLM_BREAKER_WINDOW": "60",
            "LLM_MAX_RETRIES": "0",  # Don't retry, just fail fast
        }
        with mock.patch.dict(os.environ, env):
            get_llm_client()

            with mock.patch.object(
                MockLLMClient._ChatWrapper._CompletionsWrapper,
                "create",
                side_effect=RuntimeError("server_error_500"),
            ):
                with mock.patch("time.sleep"):
                    # Call 1 -> Fail
                    with pytest.raises(RuntimeError):
                        invoke_chat("m", [])

                    # Call 2 -> Fail -> Open Breaker
                    with pytest.raises(RuntimeError):
                        invoke_chat("m", [])

                    # Call 3 -> Rejected by Breaker
                    with pytest.raises(RuntimeError, match="circuit breaker OPEN"):
                        invoke_chat("m", [])

    def test_invoke_chat_stream(self):
        """Test streaming invocation."""
        chunks = list(invoke_chat_stream("m", [{"role": "user", "content": "test"}]))
        assert len(chunks) > 0
        # Last chunk should be the full envelope
        assert "meta" in chunks[-1]
        assert chunks[-1]["meta"]["stream"] is True

    def test_cost_estimation(self):
        """Test cost calculation."""
        cost_table = {"gpt-4": {"prompt": 0.03, "completion": 0.06}}
        env = {"MODEL_COST_TABLE_JSON": json.dumps(cost_table)}
        with mock.patch.dict(os.environ, env):
            result = invoke_chat("gpt-4", [{"role": "user", "content": "test"}])
            assert result["cost"] is not None
            assert result["cost"] > 0

    def test_sanitization(self):
        """Test output sanitization."""
        env = {"LLM_SANITIZE_OUTPUT": "1", "OPENAI_API_KEY": "sk-secret"}
        with mock.patch.dict(os.environ, env):
            get_llm_client()

            mock_resp = mock.Mock()
            mock_choice = mock.Mock()
            mock_choice.message.content = "Here is my key: sk-secret"
            mock_choice.message.tool_calls = None
            mock_resp.choices = [mock_choice]
            mock_resp.usage = {}

            with mock.patch.object(
                MockLLMClient._ChatWrapper._CompletionsWrapper, "create", return_value=mock_resp
            ):
                result = invoke_chat("m", [])
                assert "[REDACTED:sk-]" in result["content"]

    def test_llm_health(self):
        """Test health check output."""
        get_llm_client()  # Ensure initialized
        health = llm_health()
        assert health["initialized"] is True
        assert health["client_kind"] == "mock"
        assert "cumulative" in health
        assert "circuit_breaker" in health
