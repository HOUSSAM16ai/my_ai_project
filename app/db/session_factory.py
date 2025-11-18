# WARNING: This file is a migration helper — do not assume models are fully portable yet.
# It provides an independent, configurable SQLAlchemy session factory for use in
# new FastAPI/ASGI components and refactored services, avoiding direct dependency
# on the Flask application context (current_app).

import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

# --- Default Configuration ---

# Safe default pool configuration for production environments.
# - pool_pre_ping: Checks connection validity before use, preventing errors from stale connections.
# - pool_size: The number of connections to keep open in the pool.
# - max_overflow: The number of connections that can be opened beyond pool_size.
DEFAULT_POOL_CONFIG: dict[str, Any] = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True,
}

# --- Global Session Factory ---

# This global variable will hold the session factory (sessionmaker instance).
# It's initialized on the first call to `create_session` or `get_session_generator`.
SessionLocal: sessionmaker[Session] | None = None


def make_engine(
    database_url: str | None = None, **overrides: Any
) -> Engine:
    """
    Creates and returns a SQLAlchemy Engine instance.

    This function is the core of the session factory. It robustly aconfigures the engine,
    sourcing the DATABASE_URL from environment variables and allowing for runtime overrides.

    Args:
        database_url: The database connection string. If not provided, it will be
                      fetched from the `DATABASE_URL` environment variable.
        **overrides: A dictionary of additional keyword arguments to pass directly to
                     `sqlalchemy.create_engine`, overriding defaults.

    Returns:
        A configured SQLAlchemy Engine instance.

    Raises:
        ValueError: If `DATABASE_URL` is not set and not provided as an argument,
                    or if the URL is malformed.
    """
    db_url = database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "DATABASE_URL is not set in environment variables and was not provided. "
            "Please set it to a valid SQLAlchemy connection string."
        )

    try:
        # Validate the URL structure before creating the engine.
        make_url(db_url)
    except Exception as e:
        raise ValueError(f"Invalid DATABASE_URL: {db_url}") from e

    # Prepare engine configuration.
    # Connection pooling is not supported by SQLite's default in-memory mode,
    # so we only add pooling options for other database drivers.
    engine_options: dict[str, Any] = {"future": True}
    if not db_url.startswith("sqlite"):
        engine_options.update(DEFAULT_POOL_CONFIG)

    # Allow echoing SQL statements for debugging, controlled by an env var.
    db_echo = str(os.environ.get("DB_ECHO", "false")).lower() in ("true", "1", "t")
    engine_options["echo"] = db_echo

    # Apply any runtime overrides.
    engine_options.update(overrides)

    return create_engine(db_url, **engine_options)


def _initialize_session_factory(engine: Engine | None = None) -> None:
    """
    Initializes the global SessionLocal factory if it hasn't been already.

    This is an internal function designed to be called by the public-facing
    session-creating functions.

    Args:
        engine: An optional Engine instance. If not provided, a new one will be created
                using `make_engine()`.
    """
    global SessionLocal
    if SessionLocal is None:
        engine_instance = engine or make_engine()
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine_instance
        )


def create_session(engine: Engine | None = None) -> Session:
    """
    Creates and returns a new, standalone SQLAlchemy Session.

    This is a simple convenience function for use in scripts, CLI commands, or any
    context where a single, non-managed session is needed.

    Args:
        engine: An optional, pre-configured Engine. If not provided, the global
                factory will be initialized with a default engine.

    Returns:
        A new SQLAlchemy Session instance.
    """
    _initialize_session_factory(engine)
    if not SessionLocal:
        # This should not happen if _initialize_session_factory works correctly.
        raise RuntimeError("Session factory could not be initialized.")
    return SessionLocal()


def get_session_generator(
    engine: Engine | None = None,
) -> Generator[Session, None, None]:
    """
    Yields a SQLAlchemy Session, suitable for dependency injection frameworks like FastAPI.

    This generator function is designed to be used with `fastapi.Depends`. It ensures
    that a database session is created for each request and properly closed afterward,

    even if errors occur.

    Args:
        engine: An optional, pre-configured Engine. If not provided, the global
                factory will be initialized with a default engine.

    Yields:
        A SQLAlchemy Session instance.
    """
    _initialize_session_factory(engine)
    if not SessionLocal:
        raise RuntimeError("Session factory could not be initialized.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Example of local verification and smoke test.
    # To run:
    # 1. Make sure `DATABASE_URL` is set in your environment (e.g., `export DATABASE_URL=sqlite:///:memory:`)
    # 2. Run `python app/db/session_factory.py`

    print("Running smoke test for session factory...")
    try:
        if not os.environ.get("DATABASE_URL"):
            print("DATABASE_URL not set. Using in-memory SQLite for smoke test.")
            os.environ["DATABASE_URL"] = "sqlite:///:memory:"

        session = create_session()
        result = session.execute(text("SELECT 1")).scalar_one()
        session.close()

        if result == 1:
            print("✅ Smoke test passed: Successfully connected to the database and executed a query.")
        else:
            print(f"❌ Smoke test failed: Expected result 1, but got {result}.")

    except Exception as e:
        print(f"❌ Smoke test failed with an error: {e}")
