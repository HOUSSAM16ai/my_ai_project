"""
Enterprise Enum Migration & Health System
══════════════════════════════════════════
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class MigrationStats:
    """Migration statistics"""
    table: str
    column: str
    total_rows: int = 0
    migrated: int = 0
    already_correct: int = 0
    errors: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 100.0
        return (self.migrated + self.already_correct) / self.total_rows * 100


@dataclass
class HealthReport:
    """Enum column health report"""
    table: str
    column: str
    healthy: bool
    total_rows: int
    lowercase_count: int
    uppercase_count: int
    invalid_count: int
    invalid_values: list[str]

    def __str__(self) -> str:
        status = "✅ Healthy" if self.healthy else "⚠️ Needs Repair"
        return f"""
╔══════════════════════════════════════════════════════════╗
║ Enum Health Report: {self.table}.{self.column}
╠══════════════════════════════════════════════════════════╣
║ Status: {status}
║ Total Rows: {self.total_rows}
║ ├── lowercase (Correct): {self.lowercase_count}
║ ├── UPPERCASE (Legacy): {self.uppercase_count}
║ └── Invalid: {self.invalid_count}
╚══════════════════════════════════════════════════════════╝
"""


class EnumMigrationService:
    """
    Comprehensive Enum Migration and Health Check Service.

    Usage:
    ──────────
    service = EnumMigrationService(session)

    # Health Check
    report = await service.health_check("admin_messages", "role", MessageRole)

    # Migrate
    stats = await service.migrate("admin_messages", "role", MessageRole)
    """

    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.migration")

    async def health_check(
        self,
        table: str,
        column: str,
        enum_class: type[Enum]
    ) -> HealthReport:
        """
        Check health of an Enum column.

        Returns:
            HealthReport with full details
        """
        query = text(f"""
            SELECT {column}, COUNT(*) as cnt
            FROM {table}
            WHERE {column} IS NOT NULL
            GROUP BY {column}
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        valid_values = {m.value.lower() for m in enum_class}
        valid_names = {m.name.upper() for m in enum_class}

        report = HealthReport(
            table=table,
            column=column,
            healthy=True,
            total_rows=0,
            lowercase_count=0,
            uppercase_count=0,
            invalid_count=0,
            invalid_values=[]
        )

        for value, count in rows:
            report.total_rows += count

            if value.lower() in valid_values:
                if value.islower():
                    report.lowercase_count += count
                else:
                    report.uppercase_count += count
                    report.healthy = False
            elif value.upper() in valid_names:
                report.uppercase_count += count
                report.healthy = False
            else:
                report.invalid_count += count
                report.invalid_values.append(value)
                report.healthy = False

        return report

    async def migrate(
        self,
        table: str,
        column: str,
        enum_class: type[Enum],
        dry_run: bool = True,
        batch_size: int = 1000
    ) -> MigrationStats:
        """
        Migrate Enum values from uppercase to lowercase.

        Args:
            table: Table name
            column: Column name
            enum_class: Enum type
            dry_run: True = Simulation only
            batch_size: Batch size

        Returns:
            MigrationStats with statistics
        """
        stats = MigrationStats(table=table, column=column)

        # Get distinct values
        query = text(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL")
        result = await self.session.execute(query)
        values = [row[0] for row in result.fetchall()]

        valid_values = {m.value.lower() for m in enum_class}

        for value in values:
            if value is None:
                continue

            stats.total_rows += 1
            lower_value = value.lower()

            # Validate value
            if lower_value not in valid_values:
                self.logger.error(f"Invalid value: '{value}'")
                stats.errors += 1
                continue

            # Needs migration?
            if value == lower_value:
                stats.already_correct += 1
                continue

            # Execute migration
            if dry_run:
                self.logger.info(f"[DRY RUN] {value} → {lower_value}")
            else:
                update_query = text(f"""
                    UPDATE {table}
                    SET {column} = :new_value
                    WHERE {column} = :old_value
                """)
                await self.session.execute(
                    update_query,
                    {"new_value": lower_value, "old_value": value}
                )
                self.logger.info(f"✅ Migrated: {value} → {lower_value}")

            stats.migrated += 1

        if not dry_run:
            await self.session.commit()

        return stats

    async def migrate_all_enums(
        self,
        dry_run: bool = True
    ) -> dict[str, MigrationStats]:
        """Migrate all Enum columns in the project"""
        from app.models import (
            MessageRole, MissionStatus, PlanStatus,
            TaskStatus, MissionEventType
        )

        targets = [
            ("admin_messages", "role", MessageRole),
            ("missions", "status", MissionStatus),
            ("mission_plans", "status", PlanStatus),
            ("tasks", "status", TaskStatus),
            ("mission_events", "event_type", MissionEventType),
        ]

        results = {}
        for table, column, enum_class in targets:
            self.logger.info(f"═══ Migrating {table}.{column} ═══")
            stats = await self.migrate(table, column, enum_class, dry_run)
            results[f"{table}.{column}"] = stats
            print(f"  → {stats.migrated} migrated, {stats.already_correct} correct")

        return results


# ══════════════════════════════════════════════════════════════
# CLI Interface
# ══════════════════════════════════════════════════════════════

async def main():
    """CLI entry point"""
    from app.core.database import async_session_factory
    from app.models import MessageRole
    from dotenv import load_dotenv

    load_dotenv()

    if len(sys.argv) < 2:
        print("""
Usage:
  python scripts/heal_db_enum_case.py health    # Health Check
  python scripts/heal_db_enum_case.py migrate   # Migrate (dry-run)
  python scripts/heal_db_enum_case.py migrate --execute  # Execute Migration
        """)
        return

    command = sys.argv[1]

    async with async_session_factory() as session:
        service = EnumMigrationService(session)

        if command == "health":
            report = await service.health_check(
                "admin_messages", "role", MessageRole
            )
            print(report)

        elif command == "migrate":
            dry_run = "--execute" not in sys.argv
            if dry_run:
                print("🔍 Simulation Mode (dry-run)...")
            else:
                print("⚡ Executing Actual Migration...")

            results = await service.migrate_all_enums(dry_run=dry_run)

            print("\n📊 Summary:")
            for key, stats in results.items():
                print(f"  {key}: {stats.success_rate:.1f}% Success")


if __name__ == "__main__":
    asyncio.run(main())
