"""
Compatibility layer for Flask-like globals in a FastAPI/Starlette environment.
This module provides thread-local (context-local) proxies for request, g, and current_user.
"""

import contextvars
from typing import Any, Optional, Callable
from fastapi.responses import JSONResponse
from fastapi import Request

# Context variables to hold the state
_request_ctx_var: contextvars.ContextVar[Optional[Request]] = contextvars.ContextVar(
    "request", default=None
)
_g_ctx_var: contextvars.ContextVar[Optional[dict]] = contextvars.ContextVar("g", default=None)
_user_ctx_var: contextvars.ContextVar[Any] = contextvars.ContextVar("user", default=None)


class LocalProxy:
    """
    A simple implementation of a local proxy to avoid depending on werkzeug.
    """

    def __init__(self, local: Callable[[], Any]):
        object.__setattr__(self, "_local", local)

    def _get_current_object(self):
        return self._local()

    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)

    def __setattr__(self, name, value):
        setattr(self._get_current_object(), name, value)

    def __delattr__(self, name):
        delattr(self._get_current_object(), name)

    def __repr__(self):
        try:
            obj = self._get_current_object()
        except RuntimeError:
            return "<LocalProxy unbound>"
        return repr(obj)

    def __bool__(self):
        try:
            return bool(self._get_current_object())
        except RuntimeError:
            return False

    def __eq__(self, other):
        try:
            return self._get_current_object() == other
        except RuntimeError:
            return False

    def __ne__(self, other):
        try:
            return self._get_current_object() != other
        except RuntimeError:
            return True


def _get_request():
    req = _request_ctx_var.get()
    if req is None:
        raise RuntimeError("Working outside of request context")
    return req


def _get_g():
    g_val = _g_ctx_var.get()
    if g_val is None:
        raise RuntimeError("Working outside of application context")
    return g_val


def _get_current_user():
    return _user_ctx_var.get()


# Proxies
request = LocalProxy(_get_request)
current_user = LocalProxy(_get_current_user)


class G:
    """Simulate Flask's g object"""

    def __getattr__(self, name):
        g_dict = _get_g()
        if name not in g_dict:
            raise AttributeError(f"'_AppCtxGlobals' object has no attribute '{name}'")
        return g_dict[name]

    def __setattr__(self, name, value):
        g_dict = _get_g()
        g_dict[name] = value

    def get(self, name, default=None):
        return _get_g().get(name, default)


g = G()


class AnonymousUser:
    @property
    def is_authenticated(self):
        return False

    @property
    def id(self):
        return None

    def __str__(self):
        return "AnonymousUser"


def jsonify(*args, **kwargs):
    """
    Simulate Flask's jsonify.
    """
    if args and kwargs:
        raise TypeError("jsonify() behavior undefined when passed both args and kwargs")
    elif len(args) == 1:  # single argument
        data = args[0]
    else:
        data = args or kwargs

    return JSONResponse(content=data)


# Context managers for setting the context (to be used in middleware)
class RequestContext:
    def __init__(self, req: Request):
        self.request = req
        self.token = None
        self.g_token = None

    def __enter__(self):
        self.token = _request_ctx_var.set(self.request)
        self.g_token = _g_ctx_var.set({})
        return self.request

    def __exit__(self, exc_type, exc_value, traceback):
        if self.token:
            _request_ctx_var.reset(self.token)
        if self.g_token:
            _g_ctx_var.reset(self.g_token)


class UserContext:
    def __init__(self, user: Any):
        self.user = user
        self.token = None

    def __enter__(self):
        self.token = _user_ctx_var.set(self.user)
        return self.user

    def __exit__(self, exc_type, exc_value, traceback):
        if self.token:
            _user_ctx_var.reset(self.token)
