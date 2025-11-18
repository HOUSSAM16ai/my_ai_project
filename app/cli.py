# app/cli.py
import click

from app.cli_handlers.db_cli import register_db_commands
from app.cli_handlers.maintenance_cli import register_maintenance_commands
from app.cli_handlers.migrate_cli import register_migrate_commands
from app.core.di import get_logger, get_session, get_settings


@click.group()
@click.option("--env", default=None, help="Optional env file or label")
@click.pass_context
def cli(ctx, env):
    """A CLI tool for CogniForge."""
    settings = get_settings(env)
    logger = get_logger(settings)
    ctx.obj = {
        "settings": settings,
        "logger": logger,
        "get_session": get_session,
    }


register_db_commands(cli)
register_migrate_commands(cli)
register_maintenance_commands(cli)

if __name__ == "__main__":
    cli()
