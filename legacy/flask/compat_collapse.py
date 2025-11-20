# app/core/kernel_v2/compat_collapse.py
"""
The Compatibility Collapse Layer for Reality Kernel v2.
"""
import json
import uuid
from unittest.mock import MagicMock


class _MockUser:
    """A mock user object."""
    def __init__(self):
        self.id = uuid.uuid4()
        self.is_authenticated = True # Mimic flask_login behavior

class _CompatG:
    """Mimics `flask.g`."""
    def __init__(self, kernel):
        self._kernel = kernel

    def __getattr__(self, name):
        return self._kernel.state.get(name)

    def __setattr__(self, name, value):
        if name == "_kernel":
            super().__setattr__(name, value)
        else:
            self._kernel.state.set(name, value)

class _CompatCurrentApp:
    """Mimics `flask.current_app`."""
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def config(self):
        return self._kernel.config

    @property
    def logger(self):
        return self._kernel.logger

# --- New Mock Objects for Request and Jsonify ---

class _CompatRequest(MagicMock):
    """
    A MagicMock that can stand in for the Flask request object.
    It can be configured in tests to provide headers, args, etc.
    """
    pass

def _compat_jsonify(*args, **kwargs):
    """
    A mock jsonify that returns a dictionary, similar to how FastAPI handles it.
    A real implementation would return a Response object.
    """
    if args and kwargs:
        raise TypeError("jsonify() took either args or kwargs, not both")
    if len(args) == 1:
        return json.dumps(args[0])
    return json.dumps(kwargs)


# These will be initialized by the MetaKernel
g = None
current_app = None
current_user = _MockUser()
request = _CompatRequest()
jsonify = _compat_jsonify

def initialize_compat_layer(kernel):
    """Initializes the compatibility layer with the kernel instance."""
    global g, current_app
    g = _CompatG(kernel)
    current_app = _CompatCurrentApp(kernel)
