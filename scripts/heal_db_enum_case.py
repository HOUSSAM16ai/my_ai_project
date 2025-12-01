#!/usr/bin/env python3
"""
Fix script for Supabase ENUM casing issues.
Converts UPPERCASE enum values in the database to lowercase,
resolving LookupError issues with Python Enums.
"""

import argparse
import asyncio
import logging

from sqlalchemy import text

from app.core.database import async_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENUM_FIXES = [
    {
        "table": "admin_messages",
        "column": "role",
        "values": ["user", "assistant", "tool", "system"],
    },
    {
        "table": "missions",
        "column": "status",
        "values": [
            "pending",
            "planning",
            "planned",
            "running",
            "adapting",
            "success",
            "failed",
            "canceled",
        ],
    },
    {
        "table": "tasks",
        "column": "status",
        "values": ["pending", "running", "success", "failed", "retry", "skipped"],
    },
    {
        "table": "mission_plans",
        "column": "status",
        "values": ["draft", "valid", "invalid", "selected", "abandoned"],
    },
]


async def analyze_enum_issues(dry_run: bool = True):
    """Analyze and fix ENUM casing issues."""

    async with async_session_factory() as session:
        total_fixed = 0

        for fix in ENUM_FIXES:
            table = fix["table"]
            column = fix["column"]

            logger.info(f"\n📊 Analyzing table: {table}.{column}")

            for value in fix["values"]:
                upper_value = value.upper()

                # Check for records with UPPERCASE value
                # Using text() for raw SQL to bypass ORM enum mapping which might fail
                count_query = text(
                    f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE {column} = :upper_val
                """
                )
                try:
                    result = await session.execute(count_query, {"upper_val": upper_value})
                    count = result.scalar()
                except Exception as e:
                    logger.warning(f"  ❌ Could not check {table}.{column}: {e}")
                    continue

                if count and count > 0:
                    logger.warning(f"  ⚠️ Found {count} record(s) with value '{upper_value}'")

                    if not dry_run:
                        update_query = text(
                            f"""
                            UPDATE {table}
                            SET {column} = :lower_val
                            WHERE {column} = :upper_val
                        """
                        )
                        await session.execute(
                            update_query, {"lower_val": value, "upper_val": upper_value}
                        )
                        logger.info(f"  ✅ Fixed {count} record(s) -> '{value}'")
                        total_fixed += count
                    else:
                        logger.info(f"  ➡️ [DRY-RUN] Would fix {count} record(s) -> '{value}'")
                        total_fixed += count

        if not dry_run:
            if total_fixed > 0:
                await session.commit()
                logger.info(f"\n🎉 Successfully fixed {total_fixed} records total.")
            else:
                logger.info("\n✨ No issues found to fix.")
        else:
            logger.info(f"\n📋 [DRY-RUN] Total records to be fixed: {total_fixed}")


def main():
    parser = argparse.ArgumentParser(description="Fix Supabase ENUM casing issues")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")
    parser.add_argument("--fix", action="store_true", help="Apply fixes to the database")
    args = parser.parse_args()

    # Default to dry-run if neither is specified, or if dry-run is specified
    is_dry_run = True
    if args.fix:
        is_dry_run = False

    # If both, dry-run wins (safety)
    if args.dry_run:
        is_dry_run = True

    if not args.fix and not args.dry_run:
        print("Usage: python scripts/heal_db_enum_case.py [--dry-run | --fix]")
        print("Defaulting to --dry-run")

    asyncio.run(analyze_enum_issues(dry_run=is_dry_run))


if __name__ == "__main__":
    main()
