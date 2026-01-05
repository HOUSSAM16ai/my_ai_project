from __future__ import annotations

import pytest

from app.core.error_messages import build_bilingual_error_message


def test_timeout_message_includes_details() -> None:
    message = build_bilingual_error_message("Timeout reached", prompt_length=1234, max_tokens=2048)

    assert "⏱️" in message
    assert "Technical Details" in message
    assert "1,234" in message
    assert "2,048" in message


def test_server_error_mode_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_ULTIMATE_COMPLEXITY_MODE", "1")
    message = build_bilingual_error_message("server_error", prompt_length=10, max_tokens=20)
    assert "ULTIMATE MODE نشط" in message

    monkeypatch.delenv("LLM_ULTIMATE_COMPLEXITY_MODE", raising=False)
    monkeypatch.setenv("LLM_EXTREME_COMPLEXITY_MODE", "1")
    message = build_bilingual_error_message("SERVER 500", prompt_length=10, max_tokens=20)
    assert "EXTREME MODE نشط" in message

    monkeypatch.delenv("LLM_EXTREME_COMPLEXITY_MODE", raising=False)
    message = build_bilingual_error_message("SERVER", prompt_length=10, max_tokens=20)
    assert "MODE نشط" not in message


def test_specific_routes_precede_generic() -> None:
    no_response = build_bilingual_error_message("no_response", prompt_length=1, max_tokens=1)
    assert "لم يتم استلام رد" in no_response

    rate_limited = build_bilingual_error_message("Rate limit exceeded", prompt_length=1, max_tokens=1)
    assert "حد الطلبات" in rate_limited

    generic = build_bilingual_error_message("unexpected", prompt_length=1, max_tokens=1)
    assert "⚠️" in generic

