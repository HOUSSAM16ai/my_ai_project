# app/core/common_imports.py
"""
SUPERHUMAN IMPORT MANAGEMENT SYSTEM
====================================
نظام خارق لإدارة الواردات وتقليل التكرار الكارثي

This module centralizes common imports to eliminate import duplication across the project.
Import from here instead of repeating imports in every file.
"""

# ==================== STANDARD LIBRARY ====================
import logging
import os
import sys
import time
import traceback
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast
from typing import TYPE_CHECKING

# ==================== THIRD-PARTY CORE ====================
try:
    from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
    from sqlalchemy.orm import Session, relationship
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.responses import JSONResponse, StreamingResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from pydantic import BaseModel, Field, validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

# ==================== PROJECT CORE ====================
# These imports are safe and commonly used across the project

def safe_import_models():
    """Safely import models with fallback."""
    try:
        from app import models
        return models
    except ImportError:
        return None

def safe_import_db():
    """Safely import database with fallback."""
    try:
        from app.core.database import SessionLocal, engine
        return SessionLocal, engine
    except ImportError:
        return None, None

def safe_import_ai_client():
    """Safely import AI client with fallback."""
    try:
        from app.core.ai_gateway import get_ai_client
        return get_ai_client
    except ImportError:
        return None


# ==================== COMMON UTILITIES ====================

class ImportHelper:
    """Helper class for conditional imports."""
    
    _cache = {}
    
    @classmethod
    def get_module(cls, module_name: str, fallback=None):
        """
        Get module with caching and fallback.
        
        Args:
            module_name: Full module path (e.g., 'app.services.agent_tools')
            fallback: Value to return if import fails
            
        Returns:
            Imported module or fallback value
        """
        if module_name in cls._cache:
            return cls._cache[module_name]
        
        try:
            parts = module_name.split('.')
            module = __import__(module_name)
            for part in parts[1:]:
                module = getattr(module, part)
            cls._cache[module_name] = module
            return module
        except (ImportError, AttributeError):
            cls._cache[module_name] = fallback
            return fallback
    
    @classmethod
    def has_module(cls, module_name: str) -> bool:
        """Check if module is available."""
        return cls.get_module(module_name) is not None


# ==================== FEATURE FLAGS ====================

class FeatureFlags:
    """Central feature flags based on available imports."""
    
    HAS_SQLALCHEMY = HAS_SQLALCHEMY
    HAS_FASTAPI = HAS_FASTAPI
    HAS_PYDANTIC = HAS_PYDANTIC
    
    @classmethod
    def check_feature(cls, feature_name: str) -> bool:
        """Check if feature is available."""
        return getattr(cls, f"HAS_{feature_name.upper()}", False)


# ==================== EXPORTS ====================

__all__ = [
    # Standard library
    'logging',
    'os',
    'sys',
    'time',
    'traceback',
    'defaultdict',
    'Callable',
    'asdict',
    'dataclass',
    'field',
    'datetime',
    'Path',
    'Any',
    'Protocol',
    'TypeVar',
    'cast',
    'TYPE_CHECKING',
    
    # Safe importers
    'safe_import_models',
    'safe_import_db',
    'safe_import_ai_client',
    
    # Utilities
    'ImportHelper',
    'FeatureFlags',
    
    # Conditional imports (if available)
    'HAS_SQLALCHEMY',
    'HAS_FASTAPI',
    'HAS_PYDANTIC',
]

# Add conditional exports
if HAS_SQLALCHEMY:
    __all__.extend([
        'Column', 'Integer', 'String', 'Text', 'DateTime', 
        'Boolean', 'ForeignKey', 'Session', 'relationship'
    ])

if HAS_FASTAPI:
    __all__.extend([
        'FastAPI', 'HTTPException', 'Depends', 'status',
        'JSONResponse', 'StreamingResponse'
    ])

if HAS_PYDANTIC:
    __all__.extend(['BaseModel', 'Field', 'validator'])
