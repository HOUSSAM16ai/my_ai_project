from app.core import error_messages


def test_error_context_normalizes_error() -> None:
    context = error_messages.ErrorContext(prompt_length=1, max_tokens=2, error="TIMEOUT")
    assert context.normalized_error == "timeout"


def test_build_bilingual_error_message_timeout() -> None:
    message = error_messages.build_bilingual_error_message("request timed out", 10, 20)
    assert "Timeout" in message
    assert "Max tokens" in message


def test_build_bilingual_error_message_rate_limit() -> None:
    message = error_messages.build_bilingual_error_message("Rate limit exceeded", 5, 10)
    assert "Rate Limit" in message
    assert "Error:" in message


def test_build_bilingual_error_message_context_length() -> None:
    message = error_messages.build_bilingual_error_message("context length token", 500, 1000)
    assert "Context Length" in message
    assert "Prompt length" in message


def test_build_bilingual_error_message_auth() -> None:
    message = error_messages.build_bilingual_error_message("Invalid API key", 1, 2)
    assert "Authentication Error" in message
    assert "API key" in message


def test_build_bilingual_error_message_server_error_with_mode(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ULTIMATE_COMPLEXITY_MODE", "1")
    monkeypatch.setenv("LLM_EXTREME_COMPLEXITY_MODE", "1")
    message = error_messages.build_bilingual_error_message("500 server error", 5, 10)
    assert "ULTIMATE MODE" in message
    assert "Server Error 500" in message


def test_build_bilingual_error_message_no_response() -> None:
    message = error_messages.build_bilingual_error_message("no_response", 7, 11)
    assert "No Response" in message
    assert "Prompt length" in message


def test_build_bilingual_error_message_generic() -> None:
    message = error_messages.build_bilingual_error_message("something else", 3, 4)
    assert "Error Occurred" in message
    assert "Prompt length" in message


def test_server_mode_status_prefers_ultimate(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ULTIMATE_COMPLEXITY_MODE", "1")
    monkeypatch.setenv("LLM_EXTREME_COMPLEXITY_MODE", "1")
    assert error_messages._server_mode_status().startswith("🚀 ULTIMATE MODE")


def test_server_mode_status_extreme(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0")
    monkeypatch.setenv("LLM_EXTREME_COMPLEXITY_MODE", "1")
    assert error_messages._server_mode_status().startswith("💪 EXTREME MODE")


def test_server_mode_status_empty(monkeypatch) -> None:
    monkeypatch.delenv("LLM_ULTIMATE_COMPLEXITY_MODE", raising=False)
    monkeypatch.delenv("LLM_EXTREME_COMPLEXITY_MODE", raising=False)
    assert error_messages._server_mode_status() == ""
