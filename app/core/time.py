"""
The TIME-ENGINE.

This engine enforces the Law of Temporal Coherence, eliminating context
errors and async/sync paradoxes. It provides a bridge for legacy code
that expects a Flask-like application context.
"""
from contextlib import contextmanager
from app.core.database import AsyncSessionLocal
