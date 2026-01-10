# app/middleware/core/hooks.py
# ======================================================================================
# ==                    LIFECYCLE HOOKS (v∞)                                        ==
# ======================================================================================
"""
خطافات دورة الحياة - Lifecycle Hooks

Extensible hook system for middleware lifecycle events.
Enables plugins and observers to react to middleware execution.

Design Pattern: Observer Pattern + Event System
"""

from collections import defaultdict
from collections.abc import Callable


class LifecycleHooks:
    """
    Lifecycle hook manager for middleware events

    Allows external components to register callbacks that
    are invoked at specific points in the middleware lifecycle.

    Supported Events:
    - before_execution: Before middleware runs
    - after_success: After successful execution
    - after_failure: After failed execution
    - after_execution: After execution (always)
    """

    def __init__(self):
        """Initialize empty hook registry"""
        self._hooks: dict[str, list[Callable]] = defaultdict(list)

    def register(self, event: str, callback: Callable) -> None:
        """
        Register a callback for an event

        Args:
            event: Event name
            callback: Function to call when event occurs
        """
        self._hooks[event].append(callback)

    def unregister(self, event: str, callback: Callable) -> bool:
        """
        Unregister a callback

        Args:
            event: Event name
            callback: Callback to remove

        Returns:
            True if removed, False if not found
        """
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            return True
        return False

    def trigger(self, event: str, *args, **kwargs) -> None:
        """
        Trigger all callbacks for an event

        Args:
            event: Event name
            *args: Positional arguments for callbacks
            **kwargs: Keyword arguments for callbacks
        """
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # Hooks should not break the pipeline
                # Log error but continue
                print(f"Hook error in event '{event}': {e}")

    def clear(self, event: str | None = None) -> None:
        """
        Clear hooks

        Args:
            event: Specific event to clear, or None to clear all
        """
        if event:
            self._hooks[event].clear()
        else:
            self._hooks.clear()

    def get_hook_count(self, event: str) -> int:
        """Get number of registered hooks for an event"""
        return len(self._hooks.get(event, []))

# Global hooks instance
_global_hooks = LifecycleHooks()

def get_global_hooks() -> LifecycleHooks:
    """Get the global lifecycle hooks manager"""
    return _global_hooks

def on_before_execution(callback: Callable) -> None:
    """
    Decorator to register a before_execution hook

    Usage:
        @on_before_execution
        def my_hook(ctx: RequestContext) -> None:
            print(f"Processing {ctx.path}")
    """
    _global_hooks.register("before_execution", callback)
    return callback

def on_after_success(callback: Callable) -> None:
    """
    Decorator to register an after_success hook

    Usage:
        @on_after_success
        def my_hook(ctx: RequestContext, result: MiddlewareResult) -> None:
            print("Success!")
    """
    _global_hooks.register("after_success", callback)
    return callback

def on_after_failure(callback: Callable) -> None:
    """
    Decorator to register an after_failure hook

    Usage:
        @on_after_failure
        def my_hook(ctx: RequestContext, result: MiddlewareResult) -> None:
            print("Failed!")
    """
    _global_hooks.register("after_failure", callback)
    return callback

def on_after_execution(callback: Callable) -> None:
    """
    Decorator to register an after_execution hook

    Usage:
        @on_after_execution
        def my_hook(ctx: RequestContext, result: MiddlewareResult) -> None:
            print("Completed!")
    """
    _global_hooks.register("after_execution", callback)
    return callback
