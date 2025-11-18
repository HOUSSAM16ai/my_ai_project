import asyncio
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Generator, Callable
from app.core.config import get_settings
from app.core.logger import get_logger

class AppContext:
    """
    A minimal application context shim.
    """

    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger("compat")

@contextmanager
def with_app_context() -> Generator[AppContext, None, None]:
    """
    Provides a minimal Flask-like application context.
    """
    yield AppContext()

@asynccontextmanager
async def with_app_context_async() -> AsyncGenerator[AppContext, None]:
    """
    Provides a minimal Flask-like application context for async functions.
    """
    yield AppContext()

class CurrentApp:
    """
    A shim for the `current_app` proxy.
    """

    @property
    def config(self) -> Any:
        return get_settings()

    @property
    def logger(self) -> Any:
        return get_logger("compat")

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(get_settings(), key, default)

current_app = CurrentApp()
