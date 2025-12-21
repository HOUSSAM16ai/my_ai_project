# app/services/async_tool_bridge.py
"""
ASYNC TOOL BRIDGE
=================
Provides async wrappers for synchronous agent_tools and master_agent_service.
Uses run_in_executor to prevent event loop blocking.

This is the CRITICAL layer that bridges:
- Sync agent_tools (read_file, write_file, etc.)
- Sync OvermindService (start_new_mission, etc.)
- Async FastAPI endpoints

DESIGN PRINCIPLES:
1. Never call sync I/O directly in async context
2. Use ThreadPoolExecutor for CPU-bound + I/O-bound sync code
3. Pass primitive types (int, str) across thread boundaries, NOT ORM objects
4. Implement timeouts for all blocking operations
"""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import functools
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)

# Thread pool for sync operations
# Size = 4 to limit concurrent blocking operations
_TOOL_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tool_bridge_")


def _shutdown_executor():
    """Cleanup executor on application shutdown."""
    with contextlib.suppress(Exception):
        _TOOL_EXECUTOR.shutdown(wait=False)


# Register cleanup on application exit
atexit.register(_shutdown_executor)


async def run_sync_tool[T](
    func: Callable[..., T],
    *args,
    timeout: float = 30.0,
    **kwargs,
) -> T:
    """
    Execute a synchronous function in a thread pool without blocking the event loop.

    Args:
        func: Synchronous function to execute
        *args: Positional arguments for func
        timeout: Maximum execution time in seconds
        **kwargs: Keyword arguments for func

    Returns:
        Result of func(*args, **kwargs)

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout
        Exception: Any exception raised by func
    """
    loop = asyncio.get_running_loop()

    # Wrap function with args/kwargs
    partial_func = functools.partial(func, *args, **kwargs)

    try:
        # Run in executor with timeout
        result = await asyncio.wait_for(
            loop.run_in_executor(_TOOL_EXECUTOR, partial_func), timeout=timeout
        )
        return result
    except TimeoutError:
        logger.error(f"Tool execution timeout: {func.__name__} (>{timeout}s)")
        raise
    except Exception as e:
        logger.error(f"Tool execution error: {func.__name__} - {e}")
        raise


class AsyncAgentTools:
    """
    Async wrapper for app.services.agent_tools.
    All methods use run_in_executor internally.
    """

    def __init__(self):
        self._tools = None
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy load agent_tools to prevent circular imports."""
        if self._loaded:
            return
        try:
            from app.services import agent_tools

            self._tools = agent_tools
        except ImportError as e:
            logger.warning(f"agent_tools not available: {e}")
            self._tools = None
        self._loaded = True

    @property
    def available(self) -> bool:
        self._ensure_loaded()
        return self._tools is not None

    async def read_file(
        self,
        path: str,
        max_bytes: int = 50000,
        ignore_missing: bool = True,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Async wrapper for read_file tool."""
        self._ensure_loaded()
        if not self._tools:
            return {"ok": False, "error": "agent_tools not available"}

        try:
            result = await run_sync_tool(
                self._tools.read_file,
                path=path,
                max_bytes=max_bytes,
                ignore_missing=ignore_missing,
                timeout=timeout,
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"ok": True, "data": result}
        except TimeoutError:
            return {"ok": False, "error": f"Timeout reading file: {path}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def write_file(
        self,
        path: str,
        content: str,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Async wrapper for write_file tool."""
        self._ensure_loaded()
        if not self._tools:
            return {"ok": False, "error": "agent_tools not available"}

        try:
            result = await run_sync_tool(
                self._tools.write_file,
                path=path,
                content=content,
                timeout=timeout,
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"ok": True, "data": result}
        except TimeoutError:
            return {"ok": False, "error": f"Timeout writing file: {path}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def code_search_lexical(
        self,
        query: str,
        root: str = ".",
        limit: int = 10,
        context_radius: int = 3,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        """Async wrapper for code_search_lexical tool."""
        self._ensure_loaded()
        if not self._tools:
            return {"ok": False, "error": "agent_tools not available"}

        try:
            result = await run_sync_tool(
                self._tools.code_search_lexical,
                query=query,
                root=root,
                limit=limit,
                context_radius=context_radius,
                timeout=timeout,
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"ok": True, "data": result}
        except TimeoutError:
            return {"ok": False, "error": f"Timeout searching for: {query}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def code_index_project(
        self,
        root: str = ".",
        max_files: int = 500,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Async wrapper for code_index_project tool."""
        self._ensure_loaded()
        if not self._tools:
            return {"ok": False, "error": "agent_tools not available"}

        try:
            result = await run_sync_tool(
                self._tools.code_index_project,
                root=root,
                max_files=max_files,
                timeout=timeout,
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"ok": True, "data": result}
        except TimeoutError:
            return {"ok": False, "error": "Timeout indexing project"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def generic_think(
        self,
        prompt: str,
        mode: str = "analysis",
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Async wrapper for generic_think tool."""
        self._ensure_loaded()
        if not self._tools:
            return {"ok": False, "error": "agent_tools not available"}

        try:
            result = await run_sync_tool(
                self._tools.generic_think,
                prompt=prompt,
                mode=mode,
                timeout=timeout,
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"ok": True, "data": result}
        except TimeoutError:
            return {"ok": False, "error": "Timeout during analysis"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


class AsyncOvermindBridge:
    """
    Async bridge for master_agent_service.OvermindService.
    Handles sync-to-async conversion for mission operations.

    CRITICAL: Pass user_id (int), NOT User object across thread boundary!
    """

    def __init__(self):
        self._service = None
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy load OvermindService to prevent circular imports."""
        if self._loaded:
            return
        try:
            from app.services.master_agent_service import _overmind_service_singleton

            self._service = _overmind_service_singleton
        except ImportError as e:
            logger.warning(f"OvermindService not available: {e}")
            self._service = None
        self._loaded = True

    @property
    def available(self) -> bool:
        self._ensure_loaded()
        return self._service is not None

    async def start_mission(
        self,
        objective: str,
        user_id: int,  # CRITICAL: Pass ID, not User object!
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """
        Start a new mission asynchronously.

        Args:
            objective: Mission objective text
            user_id: ID of the initiating user (NOT User object!)
            timeout: Timeout for mission creation (not execution)

        Returns:
            Dict with mission_id and status, or error
        """
        self._ensure_loaded()
        if not self._service:
            return {"ok": False, "error": "OvermindService not available"}

        def _create_mission():
            """Sync function to run in executor."""
            from app.core.database import SessionLocal
            from app.models import User

            session = SessionLocal()
            try:
                user = session.get(User, user_id)
                if not user:
                    return {"ok": False, "error": f"User {user_id} not found"}

                mission = self._service.start_new_mission(objective=objective, initiator=user)

                # Return primitive types only!
                return {
                    "ok": True,
                    "mission_id": mission.id,
                    "status": mission.status.value,
                    "objective": mission.objective[:100],
                }
            finally:
                session.close()

        try:
            result = await run_sync_tool(_create_mission, timeout=timeout)
            return result
        except TimeoutError:
            return {"ok": False, "error": "Timeout starting mission"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_mission_status(
        self,
        mission_id: int,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Get current mission status."""
        self._ensure_loaded()

        def _get_status():
            from app.core.database import SessionLocal
            from app.models import Mission, Task, TaskStatus

            session = SessionLocal()
            try:
                mission = session.get(Mission, mission_id)
                if not mission:
                    return {"ok": False, "error": "Mission not found"}

                # Count task statuses
                tasks = session.query(Task).filter_by(mission_id=mission_id).all()
                task_summary = {
                    "total": len(tasks),
                    "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
                    "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
                    "success": sum(1 for t in tasks if t.status == TaskStatus.SUCCESS),
                    "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
                }

                return {
                    "ok": True,
                    "mission_id": mission.id,
                    "status": mission.status.value,
                    "tasks": task_summary,
                    "is_terminal": mission.status.value in ("success", "failed", "canceled"),
                }
            finally:
                session.close()

        try:
            return await run_sync_tool(_get_status, timeout=timeout)
        except Exception as e:
            return {"ok": False, "error": str(e)}


# Singleton instances
_async_tools = AsyncAgentTools()
_async_overmind = AsyncOvermindBridge()


def get_async_tools() -> AsyncAgentTools:
    return _async_tools


def get_async_overmind() -> AsyncOvermindBridge:
    return _async_overmind
