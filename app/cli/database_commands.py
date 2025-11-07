# app/cli/database_commands.py
# ======================================================================================
# ==                 DATABASE MANAGEMENT CLI COMMANDS (v2.0) 🚀                      ==
# ======================================================================================
# PRIME DIRECTIVE:
#   أوامر CLI خارقة لإدارة قاعدة البيانات - Superior database management commands
#
#   Commands:
#   - flask database health: Check database health
#   - flask database stats: Show database statistics
#   - flask database optimize: Optimize database
#   - flask database backup: Create database backup
#   - flask database schema <table>: Show table schema
#
#   Note: Flask-Migrate commands (migrate, upgrade, etc.) are available under:
#   - flask db migrate
#   - flask db upgrade
#   - flask db downgrade
#   etc.

import json
import os
from datetime import UTC, datetime

import click
from flask import Blueprint
from flask.cli import with_appcontext

from app.services import database_service

database_cli = Blueprint("database_cli", __name__, cli_group="database")


@database_cli.cli.command("health")
@with_appcontext
def check_health():
    """🏥 فحص صحة قاعدة البيانات - Check database health"""
    click.echo("🔍 Checking database health...")
    click.echo("=" * 60)

    try:
        health = database_service.get_database_health()

        # Display status
        status_icon = (
            "✅"
            if health["status"] == "healthy"
            else "⚠️"
            if health["status"] == "degraded"
            else "❌"
        )
        click.echo(f"\n{status_icon} Status: {health['status'].upper()}")
        click.echo(f"📅 Timestamp: {health['timestamp']}")

        # Display checks
        if health.get("checks"):
            click.echo("\n🔧 Health Checks:")
            for check_name, check_data in health["checks"].items():
                check_icon = "✅" if check_data.get("status") == "ok" else "❌"
                click.echo(f"  {check_icon} {check_name}: {check_data.get('status', 'unknown')}")
                for key, value in check_data.items():
                    if key != "status":
                        click.echo(f"      {key}: {value}")

        # Display metrics
        if health.get("metrics"):
            click.echo("\n📊 Metrics:")
            for metric_name, metric_value in health["metrics"].items():
                if isinstance(metric_value, dict):
                    click.echo(f"  📈 {metric_name}:")
                    for k, v in metric_value.items():
                        click.echo(f"      {k}: {v}")
                else:
                    click.echo(f"  📈 {metric_name}: {metric_value}")

        # Display warnings
        if health.get("warnings"):
            click.echo(f"\n⚠️  Warnings ({len(health['warnings'])}):")
            for warning in health["warnings"]:
                click.echo(f"  - {warning}")

        # Display errors
        if health.get("errors"):
            click.echo(f"\n❌ Errors ({len(health['errors'])}):")
            for error in health["errors"]:
                click.echo(f"  - {error}")

        click.echo("\n" + "=" * 60)
        click.echo(
            "✅ Health check complete!" if health["status"] == "healthy" else "⚠️ Issues detected!"
        )

    except Exception as e:
        click.echo(f"❌ Health check failed: {str(e)}", err=True)
        raise click.Abort()


@database_cli.cli.command("stats")
@with_appcontext
def show_stats():
    """📊 إحصائيات قاعدة البيانات - Show database statistics"""
    click.echo("📊 Database Statistics")
    click.echo("=" * 60)

    try:
        stats = database_service.get_database_stats()

        click.echo(f"\n📈 Total Records: {stats['total_records']:,}")
        click.echo(f"\n📁 Tables ({len(stats['tables'])}):")
        click.echo("-" * 60)

        # Sort by count
        sorted_tables = sorted(stats["tables"], key=lambda x: x.get("count", 0), reverse=True)

        for table in sorted_tables:
            if "error" in table:
                click.echo(f"  ⚠️  {table['name']:<30} ERROR: {table['error']}")
            else:
                count = table["count"]
                bar_length = min(int(count / 10), 30) if count > 0 else 0
                bar = "█" * bar_length
                click.echo(f"  📁 {table['name']:<30} {count:>8,} {bar}")

        click.echo("\n" + "=" * 60)

    except Exception as e:
        click.echo(f"❌ Stats failed: {str(e)}", err=True)
        raise click.Abort()


@database_cli.cli.command("optimize")
@with_appcontext
def optimize():
    """⚡ تحسين قاعدة البيانات - Optimize database"""
    click.echo("⚡ Optimizing database...")
    click.echo("=" * 60)

    if not click.confirm("⚠️  This will run ANALYZE and clear caches. Continue?"):
        click.echo("❌ Optimization cancelled")
        return

    try:
        result = database_service.optimize_database()

        click.echo(f"\n📊 Status: {result['status']}")

        if result.get("operations"):
            click.echo(f"\n✅ Operations completed ({len(result['operations'])}):")
            for op in result["operations"]:
                click.echo(f"  ✓ {op}")

        if result.get("errors"):
            click.echo(f"\n❌ Errors ({len(result['errors'])}):")
            for error in result["errors"]:
                click.echo(f"  ✗ {error}")

        click.echo("\n" + "=" * 60)
        click.echo(
            "✅ Optimization complete!"
            if result["status"] == "success"
            else "⚠️ Optimization had issues"
        )

    except Exception as e:
        click.echo(f"❌ Optimization failed: {str(e)}", err=True)
        raise click.Abort()


@database_cli.cli.command("schema")
@click.argument("table_name")
@with_appcontext
def show_schema(table_name):
    """📋 عرض مخطط الجدول - Show table schema

    Args:
        table_name: Name of the table to inspect
    """
    click.echo(f"📋 Schema for table: {table_name}")
    click.echo("=" * 80)

    try:
        schema = database_service.get_table_schema(table_name)

        if schema.get("status") == "error":
            click.echo(f"❌ Error: {schema.get('message')}", err=True)
            raise click.Abort()

        # Table info
        click.echo(f"\n📁 Table: {schema['table']}")
        click.echo(f"🔧 Model: {schema['model']}")

        if schema.get("metadata"):
            meta = schema["metadata"]
            click.echo(f"{meta.get('icon', '📁')} {meta.get('description', 'No description')}")
            click.echo(f"📂 Category: {meta.get('category', 'Unknown')}")

        # Columns
        if schema.get("columns"):
            click.echo(f"\n📊 Columns ({len(schema['columns'])}):")
            click.echo("-" * 80)
            click.echo(f"{'Name':<25} {'Type':<20} {'Nullable':<10} {'Key':<10}")
            click.echo("-" * 80)

            for col in schema["columns"]:
                name = col["name"]
                col_type = col["type"][:18]
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                key = "PK" if col["primary_key"] else ("UQ" if col["unique"] else "")
                click.echo(f"{name:<25} {col_type:<20} {nullable:<10} {key:<10}")

        # Indexes
        if schema.get("indexes"):
            click.echo(f"\n🔍 Indexes ({len(schema['indexes'])}):")
            click.echo("-" * 80)
            for idx in schema["indexes"]:
                unique = "UNIQUE" if idx.get("unique") else ""
                cols = ", ".join(idx["columns"])
                click.echo(f"  📌 {idx['name']:<40} ({cols}) {unique}")

        # Foreign Keys
        if schema.get("foreign_keys"):
            click.echo(f"\n🔗 Foreign Keys ({len(schema['foreign_keys'])}):")
            click.echo("-" * 80)
            for fk in schema["foreign_keys"]:
                cols = ", ".join(fk["columns"])
                ref_cols = ", ".join(fk["referred_columns"])
                click.echo(f"  🔗 {cols} → {fk['referred_table']}.{ref_cols}")

        click.echo("\n" + "=" * 80)

    except Exception as e:
        click.echo(f"❌ Schema inspection failed: {str(e)}", err=True)
        raise click.Abort()


@database_cli.cli.command("tables")
@with_appcontext
def list_tables():
    """📁 قائمة بجميع الجداول - List all tables"""
    click.echo("📁 Database Tables")
    click.echo("=" * 80)

    try:
        tables = database_service.get_all_tables()

        # Group by category
        categories = {}
        for table in tables:
            cat = table.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(table)

        # Display by category
        for category in sorted(categories.keys()):
            click.echo(f"\n📂 {category}")
            click.echo("-" * 80)

            for table in categories[category]:
                icon = table.get("icon", "📁")
                name = table["name"]
                count = table.get("count", 0)
                recent = table.get("recent_24h", 0)
                cols = table.get("column_count", 0)
                desc = table.get("description", "No description")[:40]

                click.echo(
                    f"  {icon} {name:<25} {count:>8,} records  {recent:>5} new  {cols:>3} cols  {desc}"
                )

        total_records = sum(t.get("count", 0) for t in tables)
        click.echo("\n" + "=" * 80)
        click.echo(f"📊 Total: {len(tables)} tables, {total_records:,} records")

    except Exception as e:
        click.echo(f"❌ Failed to list tables: {str(e)}", err=True)
        raise click.Abort()


@database_cli.cli.command("backup")
@click.option("--output", "-o", default="backup", help="Output directory for backup")
@with_appcontext
def backup(output):
    """💾 نسخ احتياطي لقاعدة البيانات - Backup database"""
    click.echo("💾 Creating database backup...")
    click.echo("=" * 60)

    try:
        # Create output directory
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(output, f"db_backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        tables = database_service.get_all_tables()
        total_records = 0

        for table in tables:
            table_name = table["name"]
            click.echo(f"📦 Backing up {table_name}...")

            result = database_service.export_table_data(table_name)

            if result.get("status") == "success":
                output_file = os.path.join(backup_dir, f"{table_name}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result["data"], f, indent=2, ensure_ascii=False)

                count = len(result["data"])
                total_records += count
                click.echo(f"  ✅ {count:,} records → {output_file}")
            else:
                click.echo(f"  ❌ Failed: {result.get('message')}", err=True)

        # Create metadata file
        metadata = {
            "timestamp": timestamp,
            "total_tables": len(tables),
            "total_records": total_records,
            "tables": [t["name"] for t in tables],
        }

        metadata_file = os.path.join(backup_dir, "backup_metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        click.echo("\n" + "=" * 60)
        click.echo("✅ Backup complete!")
        click.echo(f"📂 Location: {backup_dir}")
        click.echo(f"📊 {len(tables)} tables, {total_records:,} records")

    except Exception as e:
        click.echo(f"❌ Backup failed: {str(e)}", err=True)
        raise click.Abort()
