import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.getcwd())

from app.core.settings.base import BaseServiceSettings
from microservices.user_service.settings import UserServiceSettings


def test_settings():
    print("Testing BaseServiceSettings defaults...")
    base = BaseServiceSettings(SERVICE_NAME="test", DATABASE_URL="sqlite:///test.db")
    assert base.ENVIRONMENT == "development"
    assert base.DATABASE_URL == "sqlite+aiosqlite:///test.db"
    print("BaseServiceSettings OK.")

    print("Testing UserServiceSettings defaults...")
    user_settings = UserServiceSettings()
    assert user_settings.SERVICE_NAME == "user-service"
    assert "user_service.db" in user_settings.DATABASE_URL
    print("UserServiceSettings OK.")

    print("Testing Env Overrides...")
    os.environ["USER_LOG_LEVEL"] = "DEBUG"
    os.environ["USER_DATABASE_URL"] = "sqlite:///env.db"

    # Re-instantiate to pick up env vars
    # Note: pydantic-settings reads env vars at instantiation
    user_settings_env = UserServiceSettings()
    assert user_settings_env.LOG_LEVEL == "DEBUG"
    assert user_settings_env.DATABASE_URL == "sqlite+aiosqlite:///env.db"
    print("Env Overrides OK.")


if __name__ == "__main__":
    try:
        test_settings()
        print("\n✅ All Settings Tests Passed (Standalone)")
    except Exception as e:
        print(f"\n❌ Settings Tests Failed: {e}")
        sys.exit(1)
