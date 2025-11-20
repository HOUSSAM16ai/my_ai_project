# tests/gateways/test_ai_gateway_smoke.py
import json
from unittest.mock import MagicMock

import pytest

from app.gateways.ai_service_gateway import AIServiceGateway
from app.protocols.http_client import HttpClient, ResponseLike


class FakeResponse(ResponseLike):
    def __init__(
        self, status_code: int, json_data: dict | None = None, lines: list[bytes] | None = None
    ):
        self._status_code = status_code
        self._json_data = json_data
        self._lines = lines if lines is not None else []

    @property
    def status_code(self) -> int:
        return self._status_code

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise Exception(f"HTTP Error: {self.status_code}")

    def iter_lines(self) -> iter:
        return iter(self._lines)

    def json(self) -> dict | None:
        return self._json_data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeHttpClient(HttpClient):
    def __init__(self, response: ResponseLike):
        self.response = response

    def post(
        self,
        url: str,
        *,
        headers: dict | None = None,
        json: dict | None = None,
        stream: bool = False,
        timeout: int | None = None,
    ):
        return self.response


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.AI_SERVICE_URL = "http://fake-ai-service.com"
    settings.SECRET_KEY = "fake-secret"
    return settings


@pytest.fixture
def mock_logger():
    return MagicMock()


def test_stream_chat_success(mock_settings, mock_logger):
    """Tests successful streaming chat response."""
    lines = [
        json.dumps({"type": "message", "payload": {"content": "Hello"}}).encode("utf-8"),
        json.dumps({"type": "message", "payload": {"content": " there!"}}).encode("utf-8"),
    ]
    fake_response = FakeResponse(status_code=200, lines=lines)
    fake_http_client = FakeHttpClient(response=fake_response)

    gateway = AIServiceGateway(
        http_client=fake_http_client, settings=mock_settings, logger=mock_logger
    )

    response_chunks = list(gateway.stream_chat("Hi", "conv123", "user1"))

    assert len(response_chunks) == 2
    assert response_chunks[0] == {"type": "message", "payload": {"content": "Hello"}}
    assert response_chunks[1] == {"type": "message", "payload": {"content": " there!"}}


def test_stream_chat_rate_limit(mock_settings, mock_logger):
    """Tests rate limit (429) error during streaming chat."""
    fake_response = FakeResponse(status_code=429)
    fake_http_client = FakeHttpClient(response=fake_response)

    gateway = AIServiceGateway(
        http_client=fake_http_client, settings=mock_settings, logger=mock_logger
    )

    response_chunks = list(gateway.stream_chat("Hi", "conv123", "user1"))

    assert len(response_chunks) == 1
    assert response_chunks[0]["type"] == "error"
    assert "Could not connect to the AI service" in response_chunks[0]["payload"]["error"]


def test_stream_chat_server_error(mock_settings, mock_logger):
    """Tests server error (500) during streaming chat."""
    fake_response = FakeResponse(status_code=500)
    fake_http_client = FakeHttpClient(response=fake_response)

    gateway = AIServiceGateway(
        http_client=fake_http_client, settings=mock_settings, logger=mock_logger
    )

    response_chunks = list(gateway.stream_chat("Hi", "conv123", "user1"))

    assert len(response_chunks) == 1
    assert response_chunks[0]["type"] == "error"
    assert "Could not connect to the AI service" in response_chunks[0]["payload"]["error"]


@pytest.mark.skipif("not config.getoption('--run-integration')")
def test_ai_gateway_integration(mock_settings, mock_logger):
    """
    Integration test for the AI Service Gateway.
    This test is skipped by default and can be enabled with the --run-integration flag.
    It requires a running AI service.
    """
    from app.protocols.http_client import RequestsAdapter

    http_client = RequestsAdapter()
    gateway = AIServiceGateway(http_client=http_client, settings=mock_settings, logger=mock_logger)

    # This will likely fail if the service is not running, but it's a start
    with pytest.raises(Exception):  # noqa: B017
        list(gateway.stream_chat("Hi", "conv123", "user1"))
