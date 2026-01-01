"""
Common Imports & Type Hints.

This module acts as a facade for common external dependencies to ensure consistency
and reduce boilerplate. It strictly forbids internal application imports to prevent
circular dependencies.

Allowed:
- Python Standard Library (typing, os, sys, etc.)
- 3rd Party Libraries (FastAPI, SQLAlchemy, Pydantic)

Forbidden:
- app.* (Internal modules)
"""
# ruff: noqa: F401

import logging
import os
import sys
import time
import traceback
from collections import defaultdict
from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Final,
    Generic,
    Literal,
    NoReturn,
    Protocol,
    TypeVar,
    cast,
)
from uuid import UUID, uuid4

# 3rd Party Imports (Guarded)
try:
    from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session, relationship
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
    from fastapi.responses import JSONResponse, StreamingResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError, validator
    from pydantic_settings import BaseSettings
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

# ==============================================================================
# Feature Flags
# ==============================================================================
class FeatureFlags:
    """Runtime availability flags."""
    HAS_SQLALCHEMY = HAS_SQLALCHEMY
    HAS_FASTAPI = HAS_FASTAPI
    HAS_PYDANTIC = HAS_PYDANTIC
