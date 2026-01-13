"""
أدوات التحقق من مُعرّفات SQL ومكونات الاستعلام الآمنة.

تضمن هذه الوحدة أن أسماء الجداول والأعمدة وأنواع الأعمدة
تخضع للتحقق قبل استخدامها في الاستعلامات النصية.
"""

from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_COLUMN_TYPE_PATTERN = re.compile(r"^[A-Za-z0-9_\\s(),]+$")
_FORBIDDEN_TYPE_TOKENS = {"DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE"}


def validate_identifier(identifier: str) -> str:
    """
    التحقق من صلاحية اسم جدول/عمود SQL.

    Raises:
        ValueError: إذا كان المُعرّف غير صالح.
    """
    if not _IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError("اسم الجدول أو العمود غير صالح.")
    return identifier


def quote_identifier(identifier: str) -> str:
    """
    يعيد المُعرّف بصيغة آمنة قابلة للاستخدام في SQL النصي.
    """
    safe = validate_identifier(identifier)
    return f'"{safe}"'


def validate_column_type(column_type: str) -> str:
    """
    التحقق من صيغة نوع العمود لمنع حقن SQL.

    Raises:
        ValueError: إذا كان نوع العمود يحتوي على رموز غير مسموحة.
    """
    if not _COLUMN_TYPE_PATTERN.fullmatch(column_type):
        raise ValueError("صيغة نوع العمود غير صالحة.")
    tokens = {token.upper() for token in column_type.replace(",", " ").split()}
    if tokens.intersection(_FORBIDDEN_TYPE_TOKENS):
        raise ValueError("نوع العمود يحتوي على عبارات محظورة.")
    return column_type


async def ensure_table_exists(session: AsyncSession, table_name: str) -> None:
    """
    يتأكد من وجود الجدول في قاعدة البيانات الحالية.
    """
    validate_identifier(table_name)
    query = text(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = :table_name
        """
    )
    result = await session.execute(query, {"table_name": table_name})
    if result.scalar() is None:
        raise ValueError("الجدول المطلوب غير موجود.")


async def ensure_columns_exist(
    session: AsyncSession,
    table_name: str,
    columns: set[str],
) -> None:
    """
    يتأكد من وجود الأعمدة المطلوبة في جدول محدد.
    """
    if not columns:
        return
    await ensure_table_exists(session, table_name)
    for column in columns:
        validate_identifier(column)
    query = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
        """
    )
    result = await session.execute(query, {"table_name": table_name})
    available = {row[0] for row in result.all()}
    missing = columns - available
    if missing:
        raise ValueError(f"الأعمدة التالية غير موجودة: {sorted(missing)}")
