"""
Enterprise-Grade Flexible Enum Type System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Handles case-insensitive enum mapping with:
- Automatic normalization (read/write)
- Comprehensive logging
- Performance metrics
- Graceful error handling
- Type safety
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from functools import lru_cache
from typing import Any, Generic, TypeVar

from sqlalchemy import String, TypeDecorator
from sqlalchemy.engine import Dialect

# Type variable for generic enum support
E = TypeVar("E", bound=Enum)

logger = logging.getLogger(__name__)


class FlexibleEnum(TypeDecorator, Generic[E]):
    """
    SQLAlchemy TypeDecorator for case-insensitive Enum handling.

    Features:
    ─────────
    ✓ Normalizes values to lowercase on write
    ✓ Handles uppercase legacy data on read
    ✓ Provides detailed logging for debugging
    ✓ Includes performance metrics
    ✓ Graceful fallback with clear error messages

    Usage:
    ──────
    class MyModel(Base):
        status: MyEnum = Column(FlexibleEnum(MyEnum))

    Example:
    ────────
    >>> FlexibleEnum(MessageRole). process_result_value("USER", dialect)
    MessageRole.USER

    >>> FlexibleEnum(MessageRole). process_bind_param(MessageRole.USER, dialect)
    "user"
    """

    impl = String(50)
    cache_ok = True  # Enable query caching for performance

    def __init__(self, enum_class: type[E], *args: Any, **kwargs: Any) -> None:
        """
        Initialize FlexibleEnum with target enum class.

        Args:
            enum_class: The Enum class to use for conversion
        """
        self.enum_class = enum_class
        self._build_lookup_cache()
        super().__init__(*args, **kwargs)

    def _build_lookup_cache(self) -> None:
        """Pre-build lookup dictionaries for O(1) conversion."""
        # Map: lowercase_value -> enum_member
        self._value_map: dict[str, E] = {
            member.value.lower(): member
            for member in self.enum_class
        }
        # Map: uppercase_name -> enum_member
        self._name_map: dict[str, E] = {
            member.name.upper(): member
            for member in self.enum_class
        }
        # Valid values for error messages
        self._valid_values = list(self._value_map.keys())

    @lru_cache(maxsize=128)
    def _resolve_enum(self, value: str) -> E | None:
        """
        Resolve string value to enum member with caching.

        Resolution order:
        1. Exact value match (lowercase)
        2.  Name match (uppercase)
        3. None (not found)
        """
        normalized = value.strip().lower()

        # Try value match first (most common)
        if normalized in self._value_map:
            return self._value_map[normalized]

        # Try name match (legacy uppercase like 'USER')
        upper_value = value.strip().upper()
        if upper_value in self._name_map:
            return self._name_map[upper_value]

        return None

    def process_bind_param(
        self,
        value: E | str | None,
        dialect: Dialect
    ) -> str | None:
        """
        Process value before writing to database.

        Ensures all values are stored in lowercase format
        for consistency and future compatibility.

        Args:
            value: Enum member or string to store
            dialect: Database dialect

        Returns:
            Lowercase string value or None
        """
        if value is None:
            return None

        start_time = time.perf_counter()

        try:
            if isinstance(value, self.enum_class):
                result = value.value  # Already lowercase by convention
            elif isinstance(value, str):
                # Normalize any string input
                resolved = self._resolve_enum(value)
                if resolved:
                    result = resolved.value
                else:
                    # Log warning but allow storage for flexibility
                    logger.warning(
                        f"Unknown {self.enum_class.__name__} value '{value}', "
                        f"storing as lowercase.  Valid values: {self._valid_values}"
                    )
                    result = value.lower()
            else:
                result = str(value).lower()

            # Performance logging (debug level)
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 1.0:  # Log if > 1ms
                logger.debug(
                    f"FlexibleEnum.process_bind_param took {elapsed:.2f}ms"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error in process_bind_param for {self.enum_class.__name__}: "
                f"value={value!r}, error={e}"
            )
            raise

    def process_result_value(
        self,
        value: str | None,
        dialect: Dialect
    ) -> E | None:
        """
        Process value after reading from database.

        Handles legacy uppercase values (e.g., 'USER' -> MessageRole.USER)
        while supporting standard lowercase values.

        Args:
            value: String value from database
            dialect: Database dialect

        Returns:
            Enum member or None

        Raises:
            ValueError: If value cannot be resolved to enum member
        """
        if value is None:
            return None

        start_time = time.perf_counter()

        try:
            resolved = self._resolve_enum(value)

            if resolved is None:
                error_msg = (
                    f"Cannot convert '{value}' to {self.enum_class.__name__}. "
                    f"Valid values: {self._valid_values}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Log legacy format detection (for monitoring migration progress)
            if value.isupper() and value != resolved.value:
                logger.info(
                    f"Legacy uppercase enum detected: '{value}' -> {resolved}. "
                    f"Consider running data migration."
                )

            # Performance logging
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 1.0:
                logger.debug(
                    f"FlexibleEnum.process_result_value took {elapsed:.2f}ms"
                )

            return resolved

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in process_result_value for "
                f"{self.enum_class.__name__}: value={value!r}, error={e}"
            )
            raise


# =============================================================================
# CONVENIENCE FACTORY FUNCTIONS
# =============================================================================

def flexible_enum_column(enum_class: type[E]) -> FlexibleEnum[E]:
    """
    Factory function for creating FlexibleEnum columns.

    Usage:
        role = Column(flexible_enum_column(MessageRole))
    """
    return FlexibleEnum(enum_class)


# =============================================================================
# DATA MIGRATION UTILITIES
# =============================================================================

class EnumMigrationHelper:
    """
    Helper class for migrating legacy enum values in database.

    Usage:
        helper = EnumMigrationHelper(session)
        await helper.migrate_table_enum(
            table="admin_messages",
            column="role",
            enum_class=MessageRole
        )
    """

    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.migration")

    async def migrate_table_enum(
        self,
        table: str,
        column: str,
        enum_class: type[Enum],
        dry_run: bool = True
    ) -> dict[str, int]:
        """
        Migrate uppercase enum values to lowercase.

        Args:
            table: Table name
            column: Column name
            enum_class: Enum class for validation
            dry_run: If True, only report changes without applying

        Returns:
            Dict with migration statistics
        """
        from sqlalchemy import text

        stats = {"total": 0, "migrated": 0, "errors": 0}

        # Get all distinct values
        query = text(f"SELECT DISTINCT {column} FROM {table}")
        result = await self.session.execute(query)
        values = [row[0] for row in result.fetchall()]

        for value in values:
            if value is None:
                continue

            stats["total"] += 1

            # Check if needs migration (is uppercase)
            if value.isupper():
                new_value = value.lower()

                # Validate new value is valid enum
                valid_values = [m.value for m in enum_class]
                if new_value not in valid_values:
                    self.logger.error(
                        f"Cannot migrate '{value}': '{new_value}' not in {valid_values}"
                    )
                    stats["errors"] += 1
                    continue

                if dry_run:
                    self.logger.info(
                        f"[DRY RUN] Would migrate: {value} -> {new_value}"
                    )
                else:
                    update_query = text(
                        f"UPDATE {table} SET {column} = :new WHERE {column} = :old"
                    )
                    await self.session.execute(
                        update_query,
                        {"new": new_value, "old": value}
                    )
                    self.logger.info(f"Migrated: {value} -> {new_value}")

                stats["migrated"] += 1

        if not dry_run:
            await self.session.commit()

        return stats


# =============================================================================
# HEALTH CHECK & MONITORING
# =============================================================================

class EnumHealthChecker:
    """Monitor enum consistency across the database."""

    def __init__(self, session):
        self.session = session

    async def check_enum_health(
        self,
        table: str,
        column: str,
        enum_class: type[Enum]
    ) -> dict[str, Any]:
        """
        Check enum column health and return statistics.

        Returns:
            {
                "healthy": bool,
                "total_rows": int,
                "uppercase_count": int,
                "lowercase_count": int,
                "invalid_count": int,
                "invalid_values": list
            }
        """
        from sqlalchemy import text

        query = text(f"""
            SELECT {column}, COUNT(*) as cnt
            FROM {table}
            WHERE {column} IS NOT NULL
            GROUP BY {column}
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        valid_values = {m.value for m in enum_class}
        valid_names = {m.name for m in enum_class}

        stats = {
            "healthy": True,
            "total_rows": 0,
            "uppercase_count": 0,
            "lowercase_count": 0,
            "invalid_count": 0,
            "invalid_values": []
        }

        for value, count in rows:
            stats["total_rows"] += count

            if value.lower() in valid_values:
                if value.isupper():
                    stats["uppercase_count"] += count
                    stats["healthy"] = False  # Has legacy data
                else:
                    stats["lowercase_count"] += count
            elif value.upper() in valid_names:
                stats["uppercase_count"] += count
                stats["healthy"] = False
            else:
                stats["invalid_count"] += count
                stats["invalid_values"].append(value)
                stats["healthy"] = False

        return stats
