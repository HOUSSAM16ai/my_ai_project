"""
مصنع عميل OpenAI والبنية التحتية.
OpenAI Client Factory and Infrastructure.
"""

from typing import Any, Protocol
import threading
from app.config.settings import get_settings
from app.core.logging import get_logger

_LOG = get_logger(__name__)


class LLMClientProtocol(Protocol):
    """
    بروتوكول يحدد واجهة العميل (للتوافق مع Mock و Real).
    Protocol defining the client interface.
    """
    chat: Any  # Should be narrower, but OpenAI client structure is complex


class MockClient:
    """
    عميل وهمي للاختبار.
    Mock client for testing.
    """
    def __init__(self, flag: str = "") -> None:
        self._flag = flag
        self._is_mock_client = True
        self.chat = self

    @property
    def completions(self) -> "MockClient":
        return self

    def create(self, *args: Any, **kwargs: Any) -> Any:
        # Return a structure resembling OpenAI response
        # This is minimal; usually mocks are more sophisticated or use unittest.mock
        from types import SimpleNamespace
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        role="assistant",
                        content=f"Mock Response [{self._flag}]",
                        tool_calls=None
                    ),
                    finish_reason="stop"
                )
            ],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            model="mock-model-v1"
        )


_CLIENT_SINGLETON: Any | None = None
_CLIENT_LOCK = threading.Lock()
_CLIENT_META: dict[str, Any] = {}


def get_llm_client() -> Any:
    """
    الحصول على مثيل عميل LLM (نمط Singleton).
    Get LLM client instance (Singleton pattern).
    """
    global _CLIENT_SINGLETON

    # We can check settings here
    settings = get_settings()

    # Simple check for testing env var if needed, but prefer settings
    # For now, we rely on standard OpenAI client creation

    if _CLIENT_SINGLETON:
        return _CLIENT_SINGLETON

    with _CLIENT_LOCK:
        if _CLIENT_SINGLETON is None:
            # Import here to avoid early dependency check issues
            from openai import OpenAI

            api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else "dummy"

            _CLIENT_SINGLETON = OpenAI(
                api_key=api_key,
                # base_url could be added here if needed
            )
            _LOG.info("LLM Client initialized.")

        return _CLIENT_SINGLETON


def reset_llm_client() -> None:
    """
    إعادة تعيين العميل (للاختبارات).
    Reset the client (for tests).
    """
    global _CLIENT_SINGLETON
    with _CLIENT_LOCK:
        _CLIENT_SINGLETON = None


def is_mock_client(client: Any) -> bool:
    return hasattr(client, "_is_mock_client")
