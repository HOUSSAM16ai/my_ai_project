"""أوامر ترحيل قاعدة البيانات باستخدام Alembic وفق نهج وظيفي مبسط."""

from __future__ import annotations

import click
from alembic import command
from alembic.config import Config

from app.cli_handlers.context import CLIContext, get_cli_context


def register_migrate_commands(root: click.Group) -> None:
    """يسجل أوامر الترحيل ضمن واجهة CLI الموحدة."""

    @root.command("db-migrate")
    @click.option("--rev", default="head", help="النسخة المستهدفة للترقية")
    @click.pass_context
    def db_migrate(ctx: click.Context, rev: str) -> None:
        """يشغّل ترقية Alembic حتى النسخة المحددة."""

        context = get_cli_context(ctx)
        cfg = _build_config(context, rev)
        context.logger.info("alembic upgrade %s", rev)
        command.upgrade(cfg, rev)
        context.logger.info("انتهى تنفيذ ترقية Alembic.")


def _build_config(context: CLIContext, rev: str) -> Config:
    """يبني ضبط Alembic بناءً على الإعدادات الحالية."""

    cfg = Config()
    cfg.set_main_option("sqlalchemy.url", context.settings.DATABASE_URL)
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("target_metadata", "app.core.db_schema:SQLModel.metadata")
    cfg.set_main_option("revision_environment", "True")
    cfg.set_main_option("x_rev", rev)
    return cfg
