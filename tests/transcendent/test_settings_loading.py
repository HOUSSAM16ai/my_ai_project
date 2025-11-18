from app.core.config import get_settings

def test_settings_loading():
    """
    Tests that Pydantic settings are loaded from the environment.
    """
    settings = get_settings()
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///./test.db"
    assert settings.API_KEY == "test_api_key"
