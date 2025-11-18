# app/cli_handlers/migrate_cli.py
import click
from alembic import command
from alembic.config import Config


def register_migrate_commands(root):
    @root.command("db-migrate")
    @click.option("--rev", default="head")
    @click.pass_context
    def db_migrate(ctx, rev):
        settings = ctx.obj["settings"]
        logger = ctx.obj["logger"]
        cfg = Config()
        cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        cfg.set_main_option("script_location", "migrations")
        logger.info("alembic upgrade %s", rev)
        command.upgrade(cfg, rev)
        logger.info("alembic done")
