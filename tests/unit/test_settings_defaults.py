from app.core.settings.base import AppSettings


def test_default_user_service_url_codespaces() -> None:
    assert AppSettings._default_user_service_url(is_codespaces=True) == "http://localhost:8003"


def test_default_user_service_url_non_codespaces() -> None:
    assert AppSettings._default_user_service_url(is_codespaces=False) == "http://user-service:8003"
