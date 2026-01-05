"""
نظام الأنواع المركزي (Central Type System).
========================================

This module provides centralized type definitions following CS 252r principles:
- Type safety and correctness
- Reusable type aliases
- Clear semantic types
- Documentation for complex types

المعايير (Standards):
- Harvard CS 252r: Type Systems & Program Verification
- PEP 484: Type Hints
- PEP 604: Allow writing union types as X | Y
- PEP 695: Type Parameter Syntax

استخدام (Usage):
    from app.core.types import JSON, JSONDict, JSONList, Metadata
"""

from __future__ import annotations

from typing import TypeAlias, TypeVar

# ============================================================================
# Basic Type Aliases
# ============================================================================

JSONPrimitive: TypeAlias = str | int | float | bool | None
"""القيمة البدائية المسموح بها ضمن JSON."""

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | JSONPrimitive
"""نوع يدعم جميع قيم JSON بشكل متداخل دون استخدام Any."""

JSONDict: TypeAlias = dict[str, JSON]
"""تمثيل كائن JSON مع قيم متماسكة النوع."""

JSONList: TypeAlias = list[JSON]
"""تمثيل مصفوفة JSON بقيم متداخلة محكمة."""

JSONValue: TypeAlias = JSONPrimitive
"""نوع القيم البدائية لـ JSON لإبقاء التوثيق موحدًا."""

# ============================================================================
# Common Data Structure Types
# ============================================================================

Metadata: TypeAlias = dict[str, str | int | float | bool]
"""قاموس بيانات وصفية بقيم بدائية فقط لتفادي الأنواع الحرة."""

Headers: TypeAlias = dict[str, str]
"""HTTP headers type"""

QueryParams: TypeAlias = dict[str, str | int | bool]
"""نوع معاملات الاستعلام بقيم محددة ودون Any."""

Config: TypeAlias = dict[str, JSON]
"""تهيئة منسجمة تعتمد على قيم JSON الصارمة."""

# ============================================================================
# Function and Callback Types
# ============================================================================

from collections.abc import Awaitable, Callable

AsyncCallable: TypeAlias = Callable[..., Awaitable[object]]
"""تابع غير متزامن يعيد أي كائن مضبوط النوع دون اللجوء إلى Any."""

ErrorHandler: TypeAlias = Callable[[Exception], object]
"""معالج أخطاء يعيد قيمة مضبوطة لتوثيق السلوك بوضوح."""

Validator: TypeAlias = Callable[[object], bool]
"""دالة تحقق لمدخلات موثقة بدلاً من الأنواع العامة."""

# ============================================================================
# Domain-Specific Types
# ============================================================================

# User and Authentication
UserId: TypeAlias = int
"""User identifier type"""

Email: TypeAlias = str
"""Email address type (semantic)"""

Token: TypeAlias = str
"""Authentication token type"""

# Mission and Task
MissionId: TypeAlias = int
"""Mission identifier type"""

TaskId: TypeAlias = int
"""Task identifier type"""

# Timestamps
Timestamp: TypeAlias = float
"""Unix timestamp (seconds since epoch)"""

# ============================================================================
# Type Variables for Generics
# ============================================================================

T = TypeVar('T')
"""Generic type variable"""

T_co = TypeVar('T_co', covariant=True)
"""Covariant type variable"""

T_contra = TypeVar('T_contra', contravariant=True)
"""Contravariant type variable"""

# Bounded type variables
EntityT = TypeVar('EntityT', bound='BaseEntity')
"""Type variable bounded to BaseEntity"""

ModelT = TypeVar('ModelT')
"""Type variable for model types"""

# ============================================================================
# Result Types (for error handling)
# ============================================================================

from typing import Generic

class Result(Generic[T]):
    """
    نوع نتيجة موثق لإرجاع نجاح أو خطأ مع واجهة عربية واضحة.

    Result type for operations that can succeed or fail.

    Following functional programming principles for error handling.

    Example:
        def divide(a: int, b: int) -> Result[float]:
            if b == 0:
                return Result.error("Division by zero")
            return Result.ok(a / b)
    """
    
    def __init__(self, value: T | None = None, error: str | None = None):
        self._value = value
        self._error = error
    
    @property
    def is_ok(self) -> bool:
        """Check if result is successful"""
        return self._error is None
    
    @property
    def is_error(self) -> bool:
        """Check if result is an error"""
        return self._error is not None
    
    @property
    def value(self) -> T:
        """Get the value (raises if error)"""
        if self._error:
            raise ValueError(f"Cannot get value from error result: {self._error}")
        return self._value  # type: ignore
    
    @property
    def error(self) -> str:
        """Get the error message (raises if ok)"""
        if self._error is None:
            raise ValueError("Cannot get error from ok result")
        return self._error
    
    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Create a successful result"""
        return cls(value=value)
    
    @classmethod
    def error(cls, error: str) -> Result[T]:
        """Create an error result"""
        return cls(error=error)

# ============================================================================
# Export All Types
# ============================================================================

__all__ = [
    # Basic types
    'JSONPrimitive',
    'JSON',
    'JSONDict',
    'JSONList',
    'JSONValue',
    # Common structures
    'Metadata',
    'Headers',
    'QueryParams',
    'Config',
    # Functions
    'AsyncCallable',
    'ErrorHandler',
    'Validator',
    # Domain types
    'UserId',
    'Email',
    'Token',
    'MissionId',
    'TaskId',
    'Timestamp',
    # Type variables
    'T',
    'T_co',
    'T_contra',
    'EntityT',
    'ModelT',
    # Result type
    'Result',
]
